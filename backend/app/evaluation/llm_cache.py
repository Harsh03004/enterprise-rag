"""Local cache of LLM drafts for evaluation runs.

Generation is the only step of an evaluation that costs API quota; retrieval,
reranking and grounding run locally. Caching each draft by the exact request
means a rerun only sends prompts that actually changed (for example after a
retrieval change), and costs nothing after grounding or scoring changes.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from app.services.llm import generate_response

# Bump when request behaviour changes in a way the key cannot see
# (e.g. provider-specific options in app.services.llm).
CACHE_VERSION = 2


class LlmCache:
    def __init__(self, path: Path | None):
        self.path = path
        self.entries: dict[str, str] = {}
        self.hits = 0
        self.misses = 0
        if path is not None and path.is_file():
            self.entries = json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def key(prompt: str, system_prompt: str | None, config: dict) -> str:
        provider = str(config.get("provider", "")).lower()
        payload = {
            "version": CACHE_VERSION,
            "provider": provider,
            "model": config.get(f"{provider}_model"),
            "temperature": config.get("temperature"),
            "max_output_tokens": config.get("max_output_tokens"),
            "system_prompt": system_prompt,
            "prompt": prompt,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def generate(self, prompt: str, config: dict | None = None, system_prompt: str | None = None) -> str:
        config = config or {}
        cache_key = self.key(prompt, system_prompt, config)
        if cache_key in self.entries:
            self.hits += 1
            return self.entries[cache_key]
        answer = generate_response(prompt, config=config, system_prompt=system_prompt)
        self.misses += 1
        # Only successful, non-empty drafts are stored; failures are retried next run.
        if answer and answer.strip():
            self.entries[cache_key] = answer
            self._save()
        return answer

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=self.path.parent, delete=False, suffix=".tmp"
        ) as file:
            json.dump(self.entries, file)
            temporary = Path(file.name)
        os.chmod(temporary, 0o644)
        os.replace(temporary, self.path)
