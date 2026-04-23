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
