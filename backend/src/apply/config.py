from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so config works regardless of CWD
# (backend/ vs repo-root). config.py lives at backend/src/apply/config.py,
# so the repo root is four parents up.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_CANDIDATES = (_REPO_ROOT / ".env", Path(".env"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(str(p) for p in _ENV_CANDIDATES),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = Field(alias="DATABASE_URL")

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    firecrawl_api_key: str = Field(default="", alias="FIRECRAWL_API_KEY")

    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="http://localhost:3001", alias="LANGFUSE_HOST")

    apply_env: str = Field(default="dev", alias="APPLY_ENV")
    apply_port: int = Field(default=8000, alias="APPLY_PORT")
    apply_cost_cap_usd: float = Field(default=0.50, alias="APPLY_COST_CAP_USD")
    apply_daily_cap_usd: float = Field(default=5.00, alias="APPLY_DAILY_CAP_USD")

    apply_use_real_agents: bool = Field(default=False, alias="APPLY_USE_REAL_AGENTS")

    # OpenRouter routing for Claude (OpenAI-compatible API)
    apply_openrouter_api_key: str = Field(default="", alias="APPLY_OPENROUTER_API_KEY")
    apply_http_referer: str = Field(
        default="https://github.com/apply-agent/apply", alias="APPLY_HTTP_REFERER"
    )
    apply_x_title: str = Field(default="Apply", alias="APPLY_X_TITLE")


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
