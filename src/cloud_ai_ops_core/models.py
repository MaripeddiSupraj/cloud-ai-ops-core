from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExtractedAsset:
    url: str
    final_url: str
    domain: str
    title: str
    description: str
    excerpt: str
    content_type_hint: str
    image_urls: list[str] = field(default_factory=list)
    image_paths: list[str] = field(default_factory=list)
    official_source_urls: list[str] = field(default_factory=list)


@dataclass
class ClassifiedPost:
    title: str
    content_type: str
    category: str
    subcategory: str
    tools: list[str]
    confidence: str
    rationale: str
    verification_points: list[str]


@dataclass
class EnhancedPost:
    title: str
    category: str
    subcategory: str
    content_type: str
    tools: list[str]
    source_url: str
    summary: str
    why_it_matters: str
    key_takeaways: list[str]
    verification_notes: list[str]
    official_sources: list[str]


@dataclass
class PublishedEntry:
    entry_path: str
    category: str
    subcategory: str
    content_type: str
    tools: list[str]
