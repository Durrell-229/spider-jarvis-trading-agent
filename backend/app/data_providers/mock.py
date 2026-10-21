"""
Mock data provider — fully offline, no API keys required.
Generates realistic synthetic crypto market data for paper trading & demos.
"""

import asyncio
import math
import random
from datetime import datetime
from typing import AsyncIterator, Optional
from uuid import uuid4

from app.data_providers.base import BaseDataProvider
from app.models.schemas import MarketData


MOCK_TOKENS = [
    "BTC", "ETH", "SOL", "AVAX", "LINK", "DOT", "ATOM", "NEAR",
    "ARB", "OP", "MATIC", "UNI", "AAVE", "CRV", "MKR", "SNX",
    "PEPE", "DOGE", "SHIB", "WIF", "BONK", "JUP", "PYTH", "TIA",
]


class MockDataProvider(BaseDataProvider):
    name = "mock"

    def __init__(self):
        self._prices: dict[str, float] = {
            "BTC": 67500.0,
            "ETH": 3450.0,
            "SOL": 178.0,
            "AVAX": 38.5,
            "LINK": 14.2,
            "DOT": 7.1,
            "ATOM": 9.8,
            "NEAR": 5.4,
            "ARB": 0.85,
            "OP": 1.95,
            "MATIC": 0.42,
            "UNI": 9.5,
            "AAVE": 185.0,
            "CRV": 0.55,
            "MKR": 1850.0,
            "SNX": 2.1,
            "PEPE": 0.000012,
            "DOGE": 0.15,
            "SHIB": 0.000018,
            "WIF": 2.35,
            "BONK": 0.000025,
            "JUP": 0.95,
            "PYTH": 0.38,
            "TIA": 5.8,
        }
        self._base_vol: dict[str, float] = {s: random.uniform(1e6, 5e8) for s in MOCK_TOKENS}
        self._liq: dict[str, float] = {s: random.uniform(5e4, 2e7) for s in MOCK_TOKENS}
        self._tick = 0

    def _evolve(self, symbol: str) -> float:
        price = self._prices[symbol]
        noise = random.gauss(0, 0.004)
        jump = 0.0
        if random.random() < 0.02:
            jump = random.choice([-1, 1]) * random.uniform(0.02, 0.08)
        new_price = price * (1 + noise + jump)
        new_price = max(new_price, price * 0.5)
        self._prices[symbol] = new_price
        return new_price

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        if symbol not in self._prices:
            return None
        price = self._evolve(symbol)
        change = random.uniform(-12, 18)
        vol = self._base_vol[symbol] * random.uniform(0.7, 1.4)
        liq = self._liq[symbol] * random.uniform(0.85, 1.15)
        spread = random.uniform(0.05, 1.8)
        volatility = abs(change) * random.uniform(0.3, 0.9) + random.uniform(0.5, 4)

        contract_age = random.uniform(10, 5000)
        top_holder = random.uniform(5, 55)
        if symbol in ("PEPE", "WIF", "BONK") and random.random() < 0.3:
            contract_age = random.uniform(1, 20)
            top_holder = random.uniform(35, 65)
            liq = random.uniform(2000, 15000)

        return MarketData(
            symbol=symbol,
            price=round(price, 8 if price < 1 else 4),
            change_24h=round(change, 2),
            volume_24h=round(vol, 2),
            liquidity_usd=round(liq, 2),
            market_cap=round(liq * random.uniform(5, 30), 2),
            holders_count=random.randint(500, 150000),
            top_holder_pct=round(top_holder, 1),
            contract_age_hours=round(contract_age, 1),
            spread_pct=round(spread, 3),
            volatility_1h=round(volatility, 2),
            timestamp=datetime.utcnow(),
            source="mock",
        )

    async def list_symbols(self) -> list[str]:
        return list(MOCK_TOKENS)

    async def stream(self) -> AsyncIterator[MarketData]:
        while True:
            self._tick += 1
            sample = random.sample(MOCK_TOKENS, k=min(4, len(MOCK_TOKENS)))
            for sym in sample:
                data = await self.get_market_data(sym)
                if data:
                    yield data
            await asyncio.sleep(2.0)

    async def health_check(self) -> bool:
        return True
