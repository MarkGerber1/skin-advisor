import os
import yaml
from functools import lru_cache
from pydantic import BaseModel


class BotSettings(BaseModel):
    bot_token: str
    admin_ids: list[int]


class WebhookSettings(BaseModel):
    host: str
    port: int


class RunSettings(BaseModel):
    mode: str
    webhook_url: str | None = None


class AppConfig(BaseModel):
    bot_name: str
    locale_default: str
    currency: str
    price_tiers: dict[str, str]
    marketplaces: list[str]
    brands_whitelist: list[str]
    disclaimer: str
    admin_usernames: list[str]
    privacy_policy_url: str
    data_retention_days: int


class Settings(BaseModel):
    bot: BotSettings
    webhook: WebhookSettings
    run: RunSettings
    app: AppConfig


def load_yaml_config(path: str = "config/app.yaml") -> dict:
    """Загружает конфигурацию из YAML файла."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_admin_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


@lru_cache
def get_settings() -> Settings:
    """Комбинирует YAML и переменные окружения из .env (BOT_TOKEN, ADMIN_IDS, RUN_MODE, WEBHOOK_*)."""
    yaml_config_data = load_yaml_config()
    run_settings = RunSettings(**yaml_config_data.get("run", {}))
    app_settings = AppConfig(**yaml_config_data.get("app", {}))

    # Читаем .env/.envvars через стандартный os.environ (предполагается, что .env загружен ранее менеджером процессов или Docker Compose)
    bot_token = os.getenv("BOT_TOKEN", "")
    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS"))

    webhook_host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    webhook_port_str = os.getenv("WEBHOOK_PORT", "8080")
    try:
        webhook_port = int(webhook_port_str)
    except ValueError:
        webhook_port = 8080

    run_mode = os.getenv("RUN_MODE", run_settings.mode or "polling")
    webhook_url = os.getenv("WEBHOOK_URL", run_settings.webhook_url or None)

    settings = Settings(
        bot=BotSettings(bot_token=bot_token, admin_ids=admin_ids),
        webhook=WebhookSettings(host=webhook_host, port=webhook_port),
        run=RunSettings(mode=run_mode, webhook_url=webhook_url),
        app=app_settings,
    )

    return settings
