"""Abstract data provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from app.models.schemas import MarketData


class BaseDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        ...

    @abstractmethod
    async def list_symbols(self) -> list[str]:
        ...

    @abstractmethod
    async def stream(self) -> AsyncIterator[MarketData]:
        ...

    async def health_check(self) -> bool:
        return True
