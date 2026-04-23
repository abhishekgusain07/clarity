from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from apply.agents.voice_similarity import (
    compute_voice_similarity,
    embed_text,
)


@pytest.mark.asyncio
async def test_embed_text_uses_openai_small_model():
    fake_embedding = [0.1, 0.2, 0.3]

    mock_client = AsyncMock()
    mock_client.embeddings.create.return_value.data = [type("O", (), {"embedding": fake_embedding})()]

    with patch("apply.agents.voice_similarity._get_openai_client", return_value=mock_client):
        vec = await embed_text("hello world")

    assert vec == pytest.approx(fake_embedding)
    mock_client.embeddings.create.assert_awaited_once()
    _, kwargs = mock_client.embeddings.create.await_args
    assert kwargs["model"] == "text-embedding-3-small"
    assert kwargs["input"] == "hello world"


@pytest.mark.asyncio
async def test_compute_voice_similarity_returns_max_cosine():
    # Craft vectors where we know the cosine answer
    draft_vec = np.array([1.0, 0.0, 0.0])
    sample_vecs = [
        np.array([0.9, 0.1, 0.0]),  # close to draft: cosine ~ 0.994
        np.array([0.0, 1.0, 0.0]),  # orthogonal: cosine 0
    ]

    async def fake_embed(text: str) -> list[float]:
        mapping = {
            "draft": draft_vec.tolist(),
            "close": sample_vecs[0].tolist(),
            "far": sample_vecs[1].tolist(),
        }
        return mapping[text]

    with patch("apply.agents.voice_similarity.embed_text", side_effect=fake_embed):
        score = await compute_voice_similarity(draft="draft", samples=["close", "far"])

    assert 0.99 <= score <= 1.0


@pytest.mark.asyncio
async def test_compute_voice_similarity_empty_samples_returns_neutral():
    score = await compute_voice_similarity(draft="anything", samples=[])
    assert score == 0.5  # neutral when no corpus to compare against
