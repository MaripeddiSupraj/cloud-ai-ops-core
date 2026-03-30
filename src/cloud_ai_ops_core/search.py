from __future__ import annotations

import html
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def search_web(query: str, limit: int = 5) -> list[str]:
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 CloudAIOpsCore"})
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError):
        return []
    matches = re.findall(r'<a[^>]+class="result__a"[^>]+href="(.*?)"', body, flags=re.IGNORECASE)
    urls = []
    seen = set()
    for raw in matches:
        candidate = html.unescape(raw)
        if candidate.startswith("http") and candidate not in seen:
            seen.add(candidate)
            urls.append(candidate)
        if len(urls) >= limit:
            break
    return urls
