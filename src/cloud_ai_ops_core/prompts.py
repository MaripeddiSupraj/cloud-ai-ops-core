from __future__ import annotations


CLASSIFICATION_PROMPT = """You are a strict classification agent for a technical knowledge repository.

Choose exactly one category and one subcategory.

Allowed categories and subcategories:
- ai: llm, agents, mlops, prompts, tools, general
- cloud: aws, azure, gcp, architecture, general
- devops: cicd, kubernetes, terraform, observability, platform, general
- security: iam, devsecops, compliance, general
- engineering: backend, frontend, architecture, api, general
- career: growth, interview, leadership, general
- productivity: workflow, automation, learning, general
- general: general

Allowed content types:
- post
- article
- document
- repo
- video
- link

Return only JSON:
{{
  "title": "clean title",
  "content_type": "post",
  "category": "ai",
  "subcategory": "agents",
  "tools": ["openai", "github"],
  "confidence": "high",
  "rationale": "short reason",
  "verification_points": ["point 1", "point 2"]
}}

Source URL: {url}
Detected title: {title}
Domain: {domain}
Detected content type hint: {content_type_hint}
Description: {description}
Excerpt: {excerpt}
Image summary: {image_summary}
Official source candidates: {official_sources}
"""


ENHANCEMENT_PROMPT = """You are a verification and enhancement agent for a public technical knowledge repository.

Rules:
- preserve the original idea
- improve clarity and usefulness
- if something is uncertain, say so in verification notes
- use official-source excerpts when available

Return only JSON:
{{
  "title": "clean title",
  "summary": "2-3 sentence summary",
  "why_it_matters": "short practical value",
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
  "verification_notes": ["note 1", "note 2"],
  "official_sources": ["https://..."]
}}

Source URL: {url}
Title: {title}
Content type: {content_type}
Category: {category}
Subcategory: {subcategory}
Tools: {tools}
Classification rationale: {rationale}
Verification points: {verification_points}
Description: {description}
Excerpt: {excerpt}
Image summary: {image_summary}
Official source excerpts: {official_excerpts}
"""


VERIFICATION_PROMPT = """You are a web verification agent.

Goal:
- inspect the source post summary
- inspect search-result excerpts
- decide whether the post appears accurate, partially accurate, unverifiable, outdated, or hype-heavy
- prefer official and primary sources

Return only JSON:
{{
  "verification_notes": ["note 1", "note 2", "note 3"],
  "supporting_sources": ["https://...", "https://..."],
  "official_sources": ["https://..."]
}}

Source URL: {url}
Title: {title}
Content type: {content_type}
Category: {category}
Subcategory: {subcategory}
Tools: {tools}
Post excerpt: {excerpt}
Image summary: {image_summary}
Official source excerpts: {official_excerpts}
Search-result excerpts: {search_excerpts}
"""
