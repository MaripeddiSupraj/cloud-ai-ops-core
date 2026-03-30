from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


class OllamaConfig:
    def __init__(self, classifier_model: str, verifier_model: str, vision_model: str) -> None:
        self.classifier_model = classifier_model
        self.verifier_model = verifier_model
        self.vision_model = vision_model


def _chat(payload: dict) -> dict:
    request = Request(
        OLLAMA_CHAT_URL,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
    return json.loads(body)


def chat_json(model: str, prompt: str) -> dict:
    response = _chat(
        {
            "model": model,
            "stream": False,
            "format": "json",
            "messages": [{"role": "user", "content": prompt}],
        }
    )
    return json.loads(response["message"]["content"])


def describe_images(model: str, prompt: str, image_paths: list[str]) -> str:
    if not image_paths:
        return ""
    response = _chat(
        {
            "model": model,
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [str(Path(path).expanduser().resolve()) for path in image_paths[:3]],
                }
            ],
        }
    )
    return response["message"]["content"].strip()
