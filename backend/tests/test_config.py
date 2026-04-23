from apply.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("APPLY_ENV", "test")
    monkeypatch.setenv("APPLY_COST_CAP_USD", "0.75")

    settings = Settings()

    assert settings.database_url == "postgresql+asyncpg://u:p@h/db"
    assert settings.apply_env == "test"
    assert settings.apply_cost_cap_usd == 0.75


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")

    settings = Settings()

    assert settings.apply_env == "dev"
    assert settings.apply_port == 8000
    assert settings.apply_cost_cap_usd == 0.50
    assert settings.apply_daily_cap_usd == 5.00


def test_settings_use_real_agents_default_false(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.delenv("APPLY_USE_REAL_AGENTS", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.apply_use_real_agents is False


def test_settings_use_real_agents_true(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "true")

    settings = Settings()

    assert settings.apply_use_real_agents is True


def test_settings_openrouter_fields(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("APPLY_OPENROUTER_API_KEY", "sk-or-v1-test")
    monkeypatch.setenv("APPLY_HTTP_REFERER", "https://example.com/app")
    monkeypatch.setenv("APPLY_X_TITLE", "Example App")

    settings = Settings()

    assert settings.apply_openrouter_api_key == "sk-or-v1-test"
    assert settings.apply_http_referer == "https://example.com/app"
    assert settings.apply_x_title == "Example App"


def test_settings_openrouter_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.delenv("APPLY_OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("APPLY_HTTP_REFERER", raising=False)
    monkeypatch.delenv("APPLY_X_TITLE", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.apply_openrouter_api_key == ""
    assert settings.apply_http_referer == "https://github.com/apply-agent/apply"
    assert settings.apply_x_title == "Apply"
