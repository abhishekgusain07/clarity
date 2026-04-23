from typing import Any

from apply.config import get_settings


class _NoopClient:
    """Drop-in no-op when Langfuse keys are not configured."""

    def trace(self, *args: Any, **kwargs: Any) -> Any:
        return _NoopSpan()

    def span(self, *args: Any, **kwargs: Any) -> Any:
        return _NoopSpan()

    def flush(self) -> None:
        pass


class _NoopSpan:
    def __enter__(self) -> "_NoopSpan":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def span(self, *args: Any, **kwargs: Any) -> "_NoopSpan":
        return _NoopSpan()

    def update(self, *args: Any, **kwargs: Any) -> None:
        pass

    def end(self) -> None:
        pass


_client: Any | None = None


def get_langfuse() -> Any:
    """Return a Langfuse client or a no-op if not configured."""
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        _client = _NoopClient()
        return _client

    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except ImportError:
        _client = _NoopClient()

    return _client
