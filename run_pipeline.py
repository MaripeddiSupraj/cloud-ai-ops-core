#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from src.cloud_ai_ops_core.ollama_client import OllamaConfig
from src.cloud_ai_ops_core.pipeline import process_url


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Cloud AI Ops knowledge pipeline for a URL.")
    parser.add_argument("--url", required=True, help="Source URL, such as a LinkedIn post, blog, docs page, or repo.")
    parser.add_argument(
        "--public-repo",
        default=str((Path(__file__).resolve().parent.parent / "cloud-ai-ops-knowledge").resolve()),
        help="Path to the public reading repo.",
    )
    parser.add_argument("--classifier-model", default="llama3:latest")
    parser.add_argument("--verifier-model", default="deepseek-r1:latest")
    parser.add_argument("--vision-model", default="")
    parser.add_argument("--push-public", action="store_true", help="Commit and push the public repo after publishing.")
    args = parser.parse_args()

    result = process_url(
        url=args.url,
        public_repo=Path(args.public_repo).expanduser().resolve(),
        push_public=args.push_public,
        ollama=OllamaConfig(
            classifier_model=args.classifier_model,
            verifier_model=args.verifier_model,
            vision_model=args.vision_model,
        ),
    )
    print(f"Published: {result.entry_path}")
    print(f"Content type: {result.content_type}")
    print(f"Category: {result.category}")
    print(f"Subcategory: {result.subcategory}")
    print(f"Tools: {', '.join(result.tools) if result.tools else 'unclassified'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
