"""Claude model factories routed through OpenRouter.

We use OpenRouter's OpenAI-compatible API rather than calling Anthropic
directly. This lets us swap model providers later without code changes
and takes advantage of OpenRouter's unified billing and fallback pool.

Custom headers `HTTP-Referer` and `X-Title` are OpenRouter's attribution
mechanism — they identify our app for rate limits and leaderboards.
"""
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from apply.config import get_settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# OpenRouter model IDs — see https://openrouter.ai/models for the catalog.
# Keep in one place so upgrading is a single edit.
HAIKU_MODEL_ID = "anthropic/claude-haiku-4.5"
SONNET_MODEL_ID = "anthropic/claude-sonnet-4.5"


def _build_openrouter_client() -> AsyncOpenAI:
    settings = get_settings()
    api_key = settings.apply_openrouter_api_key
    return AsyncOpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            # OpenAI SDK sometimes drops Authorization on non-OpenAI hosts; set explicit
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": settings.apply_http_referer,
            "X-Title": settings.apply_x_title,
        },
    )


def _build_model(model_id: str) -> OpenAIModel:
    provider = OpenAIProvider(openai_client=_build_openrouter_client())
    return OpenAIModel(model_id, provider=provider)


def haiku() -> OpenAIModel:
    """Cheap, fast model for structured parsing + classification."""
    return _build_model(HAIKU_MODEL_ID)


def sonnet() -> OpenAIModel:
    """Reasoning model for research + fit analysis."""
    return _build_model(SONNET_MODEL_ID)
