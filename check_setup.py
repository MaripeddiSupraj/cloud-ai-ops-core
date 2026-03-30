#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    ok = True

    linkedin_cookie = os.getenv("LINKEDIN_COOKIE", "").strip()
    print(f"LINKEDIN_COOKIE: {'set' if linkedin_cookie else 'missing'}")
    if not linkedin_cookie:
        ok = False

    try:
        result = subprocess.run(
            ["ollama", "list"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"Ollama: unavailable ({exc})")
        return 1

    print("Installed Ollama models:")
    print(result.stdout.strip() or "(none)")

    text = result.stdout.lower()
    if "llama3:latest" not in text:
        print("Missing recommended classifier model: llama3:latest")
        ok = False
    if "deepseek-r1:latest" not in text:
        print("Missing recommended verifier model: deepseek-r1:latest")
        ok = False
    if "llava" not in text and "vision" not in text:
        print("No vision model detected. Image reading will stay disabled.")

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
