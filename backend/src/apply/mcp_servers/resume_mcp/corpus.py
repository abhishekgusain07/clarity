"""In-process loader for the user's resume + profile + voice corpus.

The resume-mcp server wraps this in MCP tools, but it's also directly
importable for tests and for agents that want to bypass the MCP layer.
The seed files live at the repo's `backend/seed/` directory by default;
tests pass an override via `seed_dir=tmp_path`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


_DEFAULT_SEED_DIR = Path(__file__).resolve().parents[4] / "seed"


@dataclass(frozen=True)
class VoiceSample:
    id: str
    kind: str
    text: str


class ResumeCorpus:
    def __init__(self, seed_dir: Path | None = None) -> None:
        self.seed_dir = seed_dir or _DEFAULT_SEED_DIR
        self._profile_cache: dict | None = None
        self._resume_cache: str | None = None
        self._samples_cache: list[VoiceSample] | None = None

    def _profile(self) -> dict:
        if self._profile_cache is None:
            self._profile_cache = json.loads((self.seed_dir / "profile.json").read_text())
        return self._profile_cache

    def resume_markdown(self) -> str:
        if self._resume_cache is None:
            self._resume_cache = (self.seed_dir / "resume.md").read_text()
        return self._resume_cache

    def profile_field(self, key: str) -> str | None:
        value = self._profile().get(key)
        if value is None or value == "":
            return None
        return value if isinstance(value, str) else str(value)

    def list_voice_samples(self) -> list[VoiceSample]:
        if self._samples_cache is None:
            data = json.loads((self.seed_dir / "voice_samples.json").read_text())
            self._samples_cache = [
                VoiceSample(id=s["id"], kind=s["kind"], text=s["text"])
                for s in data["samples"]
            ]
        return list(self._samples_cache)

    def find_voice_samples(
        self,
        query: str | None,
        kind: str | None,
        top_k: int,
    ) -> list[VoiceSample]:
        """Phase 3a: ignores `query` (no embedding similarity here — that's
        the voice_similarity module). Returns samples filtered by `kind`,
        capped at `top_k`. Phase 3b can add semantic retrieval."""
        samples = self.list_voice_samples()
        if kind:
            samples = [s for s in samples if s.kind == kind]
        return samples[:top_k]
