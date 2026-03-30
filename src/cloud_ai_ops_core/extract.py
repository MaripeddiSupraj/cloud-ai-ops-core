from __future__ import annotations

import html
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


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


def fetch_url_context(url: str) -> dict:
    parsed = urlparse(url)
    metadata = {
        "url": url,
        "final_url": url,
        "domain": parsed.netloc,
        "title": derive_title_from_url(url),
        "description": "",
        "excerpt": "",
        "fetch_status": "unfetched",
    }
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 CloudAIOpsCore"})
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read(250000).decode("utf-8", errors="ignore")
            final_url = response.geturl()
    except (HTTPError, URLError, TimeoutError) as exc:
        metadata["fetch_status"] = f"error: {exc}"
        return metadata

    title = extract_title_from_html(body)
    description = extract_meta_description(body)
    excerpt = clean_text(body)[:1400]

    metadata.update(
        {
            "final_url": final_url,
            "domain": urlparse(final_url).netloc,
            "title": title or metadata["title"],
            "description": description,
            "excerpt": description or excerpt,
            "fetch_status": "ok",
        }
    )
    return metadata

