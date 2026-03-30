from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClassifiedPost:
    url: str
    title: str
    source_name: str
    source_domain: str
    content_type: str
    categories: list[str]
    tools: list[str]
    summary_seed: str
    official_sources: list[str]
    fetched_excerpt: str


@dataclass
class PublishedEntry:
    entry_path: str
    content_type: str
    primary_category: str
    tools: list[str]

