from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .extract import fetch_url_context
from .models import ClassifiedPost, PublishedEntry
from .taxonomy import CATEGORY_KEYWORDS, OFFICIAL_SOURCES, TOOL_KEYWORDS


def contains_keyword(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower())
    if re.fullmatch(r"[a-z0-9]+", keyword.lower()):
        pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return keyword.lower() in text


def infer_labels(text: str, mapping: dict[str, list[str]]) -> list[str]:
    haystack = text.lower()
    return sorted(label for label, words in mapping.items() if any(contains_keyword(haystack, word) for word in words))


def classify_content_type(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "linkedin.com" in host:
        return "post"
    if "youtube.com" in host or "youtu.be" in host or "vimeo.com" in host:
        return "video"
    if "github.com" in host:
        if re.fullmatch(r"/[^/]+/[^/]+/?", path):
            return "repo"
        return "document"
    if "/blog/" in path or "/article/" in path:
        return "article"
    if "/docs/" in path or host.startswith("docs."):
        return "document"
    return "link"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "item"


def classify_agent(url: str) -> ClassifiedPost:
    context = fetch_url_context(url)
    text = " ".join(
        [
            url,
            context["title"],
            context["description"],
            context["excerpt"],
            context["domain"],
        ]
    )
    categories = infer_labels(text, CATEGORY_KEYWORDS) or ["general"]
    tools = infer_labels(text, TOOL_KEYWORDS)
    official_sources = []
    for item in categories + tools:
        official_sources.extend(OFFICIAL_SOURCES.get(item, []))
    official_sources = sorted(dict.fromkeys(official_sources))
    summary_seed = context["description"] or context["excerpt"][:220] or f"{classify_content_type(context['final_url']).capitalize()} entry."
    return ClassifiedPost(
        url=url,
        title=context["title"],
        source_name=context["domain"],
        source_domain=context["domain"],
        content_type=classify_content_type(context["final_url"]),
        categories=categories,
        tools=tools,
        summary_seed=summary_seed,
        official_sources=official_sources,
        fetched_excerpt=context["excerpt"],
    )


def enhance_agent(item: ClassifiedPost) -> dict:
    primary_category = item.categories[0] if item.categories else "general"
    tools_text = ", ".join(item.tools) if item.tools else "unclassified"
    official_lines = item.official_sources or ["No official source mapped yet."]
    summary = (
        f"{item.content_type.capitalize()} focused on {', '.join(item.categories[:3])}, "
        f"with likely relevance to {tools_text}. Seed: {item.summary_seed[:220].strip()}"
    )
    return {
        "title": item.title,
        "primary_category": primary_category,
        "summary": summary,
        "official_sources": official_lines,
        "classification": {
            "content_type": item.content_type,
            "categories": item.categories,
            "tools": item.tools,
            "source_name": item.source_name,
            "source_url": item.url,
        },
    }


def ensure_public_repo_layout(public_repo: Path) -> None:
    for path in (public_repo / "content", public_repo / "indexes"):
        path.mkdir(parents=True, exist_ok=True)


def load_registry(public_repo: Path) -> list[dict]:
    registry = public_repo / "registry.json"
    if not registry.exists():
        return []
    rows = json.loads(registry.read_text(encoding="utf-8"))
    normalized = []
    for row in rows:
        if "categories" not in row:
            row["categories"] = row.get("topics", ["general"])
        row.setdefault("tools", [])
        normalized.append(row)
    return normalized


def save_registry(public_repo: Path, rows: list[dict]) -> None:
    (public_repo / "registry.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


def build_markdown(enhanced: dict, created_at: str, slug: str, entry_path: Path) -> str:
    classification = enhanced["classification"]
    categories = ", ".join(classification["categories"]) if classification["categories"] else "general"
    tools = ", ".join(classification["tools"]) if classification["tools"] else "unclassified"
    official_sources = "\n".join(f"- {url}" for url in enhanced["official_sources"])
    return f"""---
title: "{enhanced['title']}"
slug: "{slug}"
created_at: "{created_at}"
content_type: "{classification['content_type']}"
categories: [{", ".join(f'"{item}"' for item in classification["categories"])}]
tools: [{", ".join(f'"{item}"' for item in classification["tools"])}]
source_name: "{classification['source_name']}"
source_url: "{classification['source_url']}"
---

# {enhanced['title']}

## Snapshot

{enhanced['summary']}

## Classification

- Content type: `{classification['content_type']}`
- Categories: `{categories}`
- Tools: `{tools}`

## Cross-check With Official Sources

{official_sources}

## Why it matters

Add the core insight from the original post here.

## Key takeaways

- Add takeaway 1
- Add takeaway 2
- Add takeaway 3

## Source

- Original link: `{classification['source_url']}`
- Stored path: `{entry_path}`
"""


def rebuild_indexes(public_repo: Path, registry_rows: list[dict]) -> None:
    entries = sorted(registry_rows, key=lambda row: row["created_at"], reverse=True)
    by_type: dict[str, list[dict]] = defaultdict(list)
    by_category: dict[str, list[dict]] = defaultdict(list)
    by_tool: dict[str, list[dict]] = defaultdict(list)

    for row in entries:
        by_type[row["content_type"]].append(row)
        for category in row["categories"] or ["general"]:
            by_category[category].append(row)
        for tool in row["tools"] or ["unclassified"]:
            by_tool[tool].append(row)

    write_index(public_repo / "indexes" / "all.md", "# All Entries", entries)
    write_group_index(public_repo / "indexes" / "by-content-type.md", "# Browse By Content Type", by_type)
    write_group_index(public_repo / "indexes" / "by-category.md", "# Browse By Category", by_category)
    write_group_index(public_repo / "indexes" / "by-tool.md", "# Browse By Tool", by_tool)


def render_entry_line(public_repo: Path, row: dict) -> str:
    rel = Path(row["entry_path"]).relative_to(public_repo)
    return f"- [{row['title']}](../{rel.as_posix()}) | `{row['content_type']}` | {row['created_at'][:10]}"


def write_index(path: Path, title: str, entries: list[dict]) -> None:
    lines = [title, ""]
    lines.extend(render_entry_line(path.parents[1], row) for row in entries)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_group_index(path: Path, title: str, groups: dict[str, list[dict]]) -> None:
    public_repo = path.parents[1]
    lines = [title, ""]
    for group in sorted(groups):
        lines.append(f"## {group}")
        lines.append("")
        lines.extend(render_entry_line(public_repo, row) for row in groups[group])
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def publish_agent(enhanced: dict, public_repo: Path, push_public: bool) -> PublishedEntry:
    ensure_public_repo_layout(public_repo)
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    slug = f"{datetime.now().strftime('%Y%m%d')}-{slugify(enhanced['title'])}"
    primary_category = enhanced["primary_category"]
    category_dir = public_repo / "content" / primary_category
    category_dir.mkdir(parents=True, exist_ok=True)
    entry_path = category_dir / f"{slug}.md"
    entry_path.write_text(build_markdown(enhanced, created_at, slug, entry_path), encoding="utf-8")

    registry_rows = load_registry(public_repo)
    registry_rows.append(
        {
            "title": enhanced["title"],
            "slug": slug,
            "created_at": created_at,
            "content_type": enhanced["classification"]["content_type"],
            "categories": enhanced["classification"]["categories"],
            "tools": enhanced["classification"]["tools"],
            "source_url": enhanced["classification"]["source_url"],
            "entry_path": str(entry_path),
        }
    )
    save_registry(public_repo, registry_rows)
    rebuild_indexes(public_repo, registry_rows)

    if push_public:
        subprocess.run(["git", "add", "."], cwd=public_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Add entry: {enhanced['title'][:60]}"],
            cwd=public_repo,
            check=True,
        )
        subprocess.run(["git", "push"], cwd=public_repo, check=True)

    return PublishedEntry(
        entry_path=str(entry_path),
        content_type=enhanced["classification"]["content_type"],
        primary_category=primary_category,
        tools=enhanced["classification"]["tools"],
    )


def process_url(url: str, public_repo: Path, push_public: bool) -> PublishedEntry:
    classified = classify_agent(url)
    enhanced = enhance_agent(classified)
    return publish_agent(enhanced, public_repo=public_repo, push_public=push_public)
