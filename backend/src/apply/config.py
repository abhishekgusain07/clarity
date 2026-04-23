from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
