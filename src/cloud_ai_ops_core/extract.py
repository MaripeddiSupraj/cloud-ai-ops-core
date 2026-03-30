from __future__ import annotations

import html
import mimetypes
import os
import re
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .models import ExtractedAsset
from .taxonomy import OFFICIAL_SOURCES, TOOL_KEYWORDS


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_title_from_html(payload: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", payload, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return clean_text(match.group(1))


def extract_meta_description(payload: str) -> str:
    patterns = [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, payload, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return clean_text(match.group(1))
    return ""


def derive_title_from_url(url: str) -> str:
    parsed = urlparse(url)
    leaf = parsed.path.strip("/").split("/")[-1] or parsed.netloc
    title = leaf.replace("-", " ").replace("_", " ").strip()
    title = re.sub(r"\s+", " ", title)
    return title.title() or parsed.netloc


def detect_content_type(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "linkedin.com" in host:
        return "post"
    if "youtube.com" in host or "youtu.be" in host or "vimeo.com" in host:
        return "video"
    if "github.com" in host and re.fullmatch(r"/[^/]+/[^/]+/?", path):
        return "repo"
    if "/docs/" in path or host.startswith("docs."):
        return "document"
    if "/blog/" in path or "/article/" in path:
        return "article"
    return "link"


def extract_image_urls(base_url: str, payload: str) -> list[str]:
    candidates = []
    candidates.extend(
        re.findall(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']',
            payload,
            flags=re.IGNORECASE,
        )
    )
    candidates.extend(re.findall(r'<img[^>]+src=["\'](.*?)["\']', payload, flags=re.IGNORECASE)[:5])
    seen = set()
    urls = []
    for item in candidates:
        absolute = urljoin(base_url, html.unescape(item))
        if absolute.startswith("http") and absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)
    return urls[:3]


def download_images(image_urls: list[str]) -> list[str]:
    saved = []
    scratch = Path(tempfile.gettempdir()) / "cloud-ai-ops-core-images"
    scratch.mkdir(parents=True, exist_ok=True)
    for index, image_url in enumerate(image_urls[:3], start=1):
        request = Request(image_url, headers={"User-Agent": "Mozilla/5.0 CloudAIOpsCore"})
        try:
            with urlopen(request, timeout=20) as response:
                data = response.read()
                content_type = response.headers.get_content_type()
        except (HTTPError, URLError, TimeoutError):
            continue
        suffix = mimetypes.guess_extension(content_type or "") or Path(urlparse(image_url).path).suffix or ".jpg"
        suffix = suffix.lstrip(".")
        destination = scratch / f"asset-{index}.{suffix}"
        destination.write_bytes(data)
        saved.append(str(destination))
    return saved


def infer_official_sources(text: str) -> list[str]:
    haystack = text.lower()
    urls = []
    for tool, words in TOOL_KEYWORDS.items():
        if any(word.lower() in haystack for word in words):
            official = OFFICIAL_SOURCES.get(tool)
            if official and official not in urls:
                urls.append(official)
    return urls


def fetch_url_context(url: str) -> ExtractedAsset:
    parsed = urlparse(url)
    title = derive_title_from_url(url)
    headers = {"User-Agent": "Mozilla/5.0 CloudAIOpsCore"}
    if "linkedin.com" in parsed.netloc.lower():
        linkedin_cookie = os.getenv("LINKEDIN_COOKIE", "").strip()
        if linkedin_cookie:
            headers["Cookie"] = linkedin_cookie
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read(250000).decode("utf-8", errors="ignore")
            final_url = response.geturl()
    except (HTTPError, URLError, TimeoutError):
        return ExtractedAsset(
            url=url,
            final_url=url,
            domain=parsed.netloc,
            title=title,
            description="",
            excerpt="",
            content_type_hint=detect_content_type(url),
        )

    final_title = extract_title_from_html(body) or title
    description = extract_meta_description(body)
    excerpt = clean_text(body)[:1400]
    image_urls = extract_image_urls(final_url, body)
    image_paths = download_images(image_urls)
    official_source_urls = infer_official_sources(" ".join([final_url, final_title, description, excerpt]))
    return ExtractedAsset(
        url=url,
        final_url=final_url,
        domain=urlparse(final_url).netloc,
        title=final_title,
        description=description,
        excerpt=description or excerpt,
        content_type_hint=detect_content_type(final_url),
        image_urls=image_urls,
        image_paths=image_paths,
        official_source_urls=official_source_urls,
        search_query=" ".join(part for part in [final_title, description[:120], parsed.netloc] if part).strip(),
    )
