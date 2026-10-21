"""
Configuration centralisée du Spider Jarvis Trading Agent.
Toutes les valeurs sensibles viennent des variables d'environnement.
"""

from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "Spider Jarvis Trading Agent"
    app_version: str = "0.1.0"

    trading_mode: Literal["paper", "live"] = "paper"
    live_trading_confirmation: str = ""

    database_url: str = "sqlite:///./spider_jarvis.db"

    data_provider: Literal["mock", "historical", "websocket", "binance"] = "mock"
    exchange_name: str = "none"
    exchange_api_key: str = ""
    exchange_api_secret: str = ""

    max_trade_amount: float = 25.0
    max_daily_loss: float = 50.0
    max_open_positions: int = 3
    max_daily_trades: int = 10
    default_stop_loss_percent: float = 2.0
    default_take_profit_percent: float = 4.0
    max_position_size_percent: float = 10.0
    cooldown_after_losses_seconds: int = 300
    max_data_age_seconds: int = 60

    jev_provider: str = "local"
    jev_model: str = "rule_based"

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    log_level: str = "INFO"
    log_file: str = "logs/spider_jarvis.log"

    rate_limit_per_minute: int = 60
    enable_auth: bool = False
    secret_key: str = "change-me-in-production"

    scan_interval_seconds: int = 30
    enable_scheduler: bool = True

    @field_validator("trading_mode")
    @classmethod
    def validate_trading_mode(cls, v: str) -> str:
        if v not in ("paper", "live"):
            return "paper"
        return v

    @property
    def is_live_trading_allowed(self) -> bool:
        return (
            self.trading_mode == "live"
            and self.live_trading_confirmation == "I_UNDERSTAND_THE_RISK"
        )

    @property
    def effective_trading_mode(self) -> str:
        if self.is_live_trading_allowed:
            return "live"
        return "paper"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
