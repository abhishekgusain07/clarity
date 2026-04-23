"""Voice-similarity scoring via OpenAI embeddings.

Uses `text-embedding-3-small` (cheap: $0.02/1M tokens, 1536 dims). Computes
the MAX cosine similarity between the draft and each sample in the corpus.
Max (not mean) because a cover letter that sounds like ANY of the user's
past writings is in-voice; an average gets diluted by stylistic diversity
across kinds (essay vs email vs cover letter).
"""
from __future__ import annotations

import numpy as np
from openai import AsyncOpenAI

from apply.config import get_settings

_EMBED_MODEL = "text-embedding-3-small"
_NEUTRAL_SCORE = 0.5  # returned when there's no corpus to compare against


_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    """Plain OpenAI client (not routed through OpenRouter — embeddings are
    cheap and direct-OpenAI is the canonical endpoint for these models)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed_text(text: str) -> list[float]:
    client = _get_openai_client()
    resp = await client.embeddings.create(model=_EMBED_MODEL, input=text)
    return list(resp.data[0].embedding)


def _cosine(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    av = np.asarray(a, dtype=np.float64)
    bv = np.asarray(b, dtype=np.float64)
    na = float(np.linalg.norm(av))
    nb = float(np.linalg.norm(bv))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(av, bv) / (na * nb))


async def compute_voice_similarity(draft: str, samples: list[str]) -> float:
    """Max cosine similarity between `draft` and `samples`. Returns 0.5 if no samples."""
    if not samples:
        return _NEUTRAL_SCORE
    draft_vec = await embed_text(draft)
    best = 0.0
    for sample in samples:
        sample_vec = await embed_text(sample)
        sim = _cosine(draft_vec, sample_vec)
        if sim > best:
            best = sim
    # Clamp to [0, 1] because cosine can dip negative but voice-similarity shouldn't
    return max(0.0, min(1.0, best))
