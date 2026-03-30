#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from src.cloud_ai_ops_core.ollama_client import OllamaConfig
from src.cloud_ai_ops_core.pipeline import process_url


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    load_env_file(repo_root / ".env")

    parser = argparse.ArgumentParser(description="Run the Cloud AI Ops knowledge pipeline for a URL.")
    parser.add_argument("url_arg", nargs="?", help="Source URL, such as a LinkedIn post, blog, docs page, or repo.")
    parser.add_argument("--url", "-u", help="Source URL, such as a LinkedIn post, blog, docs page, or repo.")
    parser.add_argument(
        "--public-repo",
        "-p",
        default=str((repo_root.parent / "cloud-ai-ops-knowledge").resolve()),
        help="Path to the public reading repo.",
    )
    parser.add_argument("--classifier-model", default="llama3:latest")
    parser.add_argument("--verifier-model", default="deepseek-r1:latest")
    parser.add_argument("--vision-model", default="")
    parser.add_argument("--push-public", action="store_true", help="Commit and push the public repo after publishing.")
    args = parser.parse_args()

    url = args.url or args.url_arg
    if not url:
        parser.error("Provide a URL either as the first argument or with --url.")

    if "linkedin.com" in url and not os.getenv("LINKEDIN_COOKIE", "").strip():
        print("LinkedIn URL detected but LINKEDIN_COOKIE is not set.", file=sys.stderr)
        print("Set it first, for example:", file=sys.stderr)
        print("  export LINKEDIN_COOKIE='li_at=your_real_cookie_here'", file=sys.stderr)
        return 2

    try:
        result = process_url(
            url=url,
            public_repo=Path(args.public_repo).expanduser().resolve(),
            push_public=args.push_public,
            ollama=OllamaConfig(
                classifier_model=args.classifier_model,
                verifier_model=args.verifier_model,
                vision_model=args.vision_model,
            ),
        )
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        print("Tip: run `python3 check_setup.py` first and confirm Ollama models/cookie setup.", file=sys.stderr)
        return 1

    print(f"Published: {result.entry_path}")
    print(f"Content type: {result.content_type}")
    print(f"Category: {result.category}")
    print(f"Subcategory: {result.subcategory}")
    print(f"Tools: {', '.join(result.tools) if result.tools else 'unclassified'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
