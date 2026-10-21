"""Data provider factory."""

from app.core.config import get_settings
from app.data_providers.base import BaseDataProvider
from app.data_providers.mock import MockDataProvider


def create_data_provider() -> BaseDataProvider:
    settings = get_settings()
    provider = settings.data_provider.lower()

    if provider == "mock":
        return MockDataProvider()
    # Future: historical, websocket, binance adapters
    # Always fall back to mock for safety / offline mode
    return MockDataProvider()
