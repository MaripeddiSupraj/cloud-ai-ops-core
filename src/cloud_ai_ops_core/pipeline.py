from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from .extract import fetch_url_context
from .models import ClassifiedPost, EnhancedPost, PublishedEntry
from .ollama_client import OllamaConfig, chat_json, describe_images
from .prompts import CLASSIFICATION_PROMPT, ENHANCEMENT_PROMPT, VERIFICATION_PROMPT
from .search import search_web


CONTENT_TYPE_TO_SUBDIR = {
    "post": "posts",
    "article": "articles",
    "document": "docs",
    "repo": "repos",
    "video": "videos",
    "link": "links",
}


def slugify(value: str) -> str:
    import re

    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "item"


def fetch_official_context(urls: list[str]) -> str:
    excerpts = []
    for url in urls[:3]:
        asset = fetch_url_context(url)
        if asset.excerpt:
            excerpts.append(f"{url}: {asset.excerpt[:500]}")
    return "\n".join(excerpts)


def fetch_search_context(urls: list[str]) -> str:
    excerpts = []
    for url in urls[:5]:
        asset = fetch_url_context(url)
        text = asset.excerpt[:400] if asset.excerpt else ""
        if text:
            excerpts.append(f"{url}: {text}")
    return "\n".join(excerpts)


def classify_agent(url: str, ollama: OllamaConfig, context_text: str = "") -> tuple[ClassifiedPost, str]:
    asset = fetch_url_context(url)
    if context_text:
        asset.provided_context = context_text
        asset.excerpt = "\n".join(part for part in [context_text, asset.excerpt] if part).strip()
    image_summary = ""
    if asset.image_paths and ollama.vision_model:
        image_summary = describe_images(
            ollama.vision_model,
            "Describe the technical or informational meaning of these images from the source.",
            asset.image_paths,
        )
    prompt = CLASSIFICATION_PROMPT.format(
        url=asset.url,
        title=asset.title,
        domain=asset.domain,
        content_type_hint=asset.content_type_hint,
        description=asset.description or "n/a",
        excerpt=asset.excerpt or "n/a",
        image_summary=image_summary or "n/a",
        official_sources=", ".join(asset.official_source_urls) or "n/a",
    )
    response = chat_json(ollama.classifier_model, prompt)
    return (
        ClassifiedPost(
            title=response["title"],
            content_type=response["content_type"],
            category=response["category"],
            subcategory=response["subcategory"],
            tools=response.get("tools", []),
            confidence=response.get("confidence", "medium"),
            rationale=response.get("rationale", ""),
            verification_points=response.get("verification_points", []),
        ),
        image_summary,
    )


def enhance_agent(url: str, classified: ClassifiedPost, image_summary: str, ollama: OllamaConfig, context_text: str = "") -> EnhancedPost:
    asset = fetch_url_context(url)
    if context_text:
        asset.provided_context = context_text
        asset.excerpt = "\n".join(part for part in [context_text, asset.excerpt] if part).strip()
    official_context = fetch_official_context(asset.official_source_urls)
    search_urls = search_web(asset.search_query or classified.title, limit=5)
    search_context = fetch_search_context(search_urls)
    verification_response = chat_json(
        ollama.verifier_model,
        VERIFICATION_PROMPT.format(
            url=asset.url,
            title=classified.title,
            content_type=classified.content_type,
            category=classified.category,
            subcategory=classified.subcategory,
            tools=", ".join(classified.tools) or "unclassified",
            excerpt=asset.excerpt or "n/a",
            image_summary=image_summary or "n/a",
            official_excerpts=official_context or "n/a",
            search_excerpts=search_context or "n/a",
        ),
    )
    prompt = ENHANCEMENT_PROMPT.format(
        url=asset.url,
        title=classified.title,
        content_type=classified.content_type,
        category=classified.category,
        subcategory=classified.subcategory,
        tools=", ".join(classified.tools) or "unclassified",
        rationale=classified.rationale or "n/a",
        verification_points="; ".join(classified.verification_points) or "n/a",
        description=asset.description or "n/a",
        excerpt=asset.excerpt or "n/a",
        image_summary=image_summary or "n/a",
        official_excerpts="\n".join(
            part for part in [official_context, search_context, "\n".join(verification_response.get("verification_notes", []))]
        )
        or "n/a",
        provided_context=asset.provided_context or "n/a",
    )
    response = chat_json(ollama.verifier_model, prompt)
    return EnhancedPost(
        title=response["title"],
        category=classified.category,
        subcategory=classified.subcategory,
        content_type=classified.content_type,
        tools=classified.tools,
        source_url=asset.url,
        summary=response["summary"],
        core_points=response.get("core_points", []),
        why_it_matters=response["why_it_matters"],
        key_takeaways=response["key_takeaways"],
        verification_notes=response["verification_notes"] + verification_response.get("verification_notes", []),
        official_sources=response["official_sources"] or verification_response.get("official_sources", []) or asset.official_source_urls,
        supporting_sources=verification_response.get("supporting_sources", search_urls),
    )


def build_markdown(item: EnhancedPost) -> str:
    core_points = "\n".join(f"- {point}" for point in item.core_points) if item.core_points else "- Main source points were not extracted cleanly."
    takeaways = "\n".join(f"- {point}" for point in item.key_takeaways)
    verification = "\n".join(f"- {point}" for point in item.verification_notes)
    official = "\n".join(f"- {url}" for url in item.official_sources)
    supporting = "\n".join(f"- {url}" for url in item.supporting_sources)
    tools = "\n".join(f"- {tool}" for tool in item.tools) if item.tools else "- unclassified"
    return f"""# {item.title}

## Summary

{item.summary}

## Why It Matters

{item.why_it_matters}

## Core Points

{core_points}

## Key Takeaways

{takeaways}

## Verification Notes

{verification}

## Tools

{tools}

## Official Sources

{official}

## Supporting Sources

{supporting}

## Original Source

- {item.source_url}
"""


def publish_agent(item: EnhancedPost, public_repo: Path, push_public: bool) -> PublishedEntry:
    subdir = CONTENT_TYPE_TO_SUBDIR.get(item.content_type, "links")
    target_dir = public_repo / item.category / item.subcategory / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    slug = f"{datetime.now().strftime('%Y%m%d')}-{slugify(item.title)}"
    entry_path = target_dir / f"{slug}.md"
    entry_path.write_text(build_markdown(item), encoding="utf-8")

    if push_public:
        subprocess.run(["git", "add", "."], cwd=public_repo, check=True)
        subprocess.run(["git", "commit", "-m", f"Add entry: {item.title[:60]}"], cwd=public_repo, check=True)
        subprocess.run(["git", "push"], cwd=public_repo, check=True)

    return PublishedEntry(
        entry_path=str(entry_path),
        category=item.category,
        subcategory=item.subcategory,
        content_type=item.content_type,
        tools=item.tools,
    )


def process_url(url: str, public_repo: Path, push_public: bool, ollama: OllamaConfig, context_text: str = "") -> PublishedEntry:
    classified, image_summary = classify_agent(url, ollama, context_text=context_text)
    enhanced = enhance_agent(url, classified, image_summary, ollama, context_text=context_text)
    return publish_agent(enhanced, public_repo=public_repo, push_public=push_public)
