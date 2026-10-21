"""
Crawler module — scans sources, builds token graph, emits candidates.
Uses safe terminology only (no "kill" language).
"""

import asyncio
from datetime import datetime
from typing import Callable, Optional
from uuid import uuid4

from app.core.logging import get_logger
from app.data_providers.base import BaseDataProvider
from app.engines.analysis import AnalysisEngine
from app.models.schemas import MarketData, TokenNode, TokenStatus

logger = get_logger("crawler")


class Crawler:
    def __init__(
        self,
        provider: BaseDataProvider,
        analysis: AnalysisEngine,
        on_event: Optional[Callable] = None,
    ):
        self.provider = provider
        self.analysis = analysis
        self.on_event = on_event or (lambda *a, **k: None)
        self.graph: dict[str, TokenNode] = {}
        self._running = False
        self._scans = 0
        self._candidates: list[dict] = []

    @property
    def scans_count(self) -> int:
        return self._scans

    def get_graph_snapshot(self) -> list[TokenNode]:
        return list(self.graph.values())

    async def scan_once(self) -> list[TokenNode]:
        """Single scan cycle: discover, analyse, classify."""
        self._scans += 1
        await self._emit("CRAWLER_SCAN_STARTED", f"Scan #{self._scans} démarré")

        symbols = await self.provider.list_symbols()
        discovered: list[TokenNode] = []

        for symbol in symbols:
            data = await self.provider.get_market_data(symbol)
            if not data:
                continue

            analysis = self.analysis.analyze(data)
            status, explanation = self._classify(data, analysis)

            node = TokenNode(
                id=str(uuid4()),
                symbol=symbol,
                price=data.price,
                change_24h=data.change_24h,
                liquidity_usd=data.liquidity_usd,
                volume_24h=data.volume_24h,
                risk_score=analysis["risk_score"],
                status=status,
                last_update=datetime.utcnow(),
                explanation=explanation,
            )

            if symbol in self.graph:
                node.x = self.graph[symbol].x
                node.y = self.graph[symbol].y
                node.id = self.graph[symbol].id
            else:
                import math, random
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(120, 380)
                node.x = 400 + radius * math.cos(angle)
                node.y = 300 + radius * math.sin(angle)

            self.graph[symbol] = node
            discovered.append(node)

            await self._emit(
                "TOKEN_DISCOVERED" if status == TokenStatus.DISCOVERED else "TOKEN_FILTERED",
                f"{symbol}: {explanation}",
                symbol=symbol,
                data={"status": status.value, "risk_score": analysis["risk_score"]},
            )

        await self._emit(
            "CRAWLER_SCAN_COMPLETED",
            f"Scan #{self._scans} terminé — {len(discovered)} tokens",
            data={"count": len(discovered)},
        )
        return discovered

    def _classify(self, data: MarketData, analysis: dict) -> tuple[TokenStatus, str]:
        if analysis.get("suspicious_contract"):
            return TokenStatus.HIGH_RISK, "Contrat suspect / trop récent — high risk"
        if analysis.get("low_liquidity"):
            return TokenStatus.FILTERED, "Liquidité trop faible — filtered"
        if analysis["risk_score"] >= 0.8:
            return TokenStatus.HIGH_RISK, f"Score de risque élevé ({analysis['risk_score']:.2f})"
        if analysis["risk_score"] >= 0.6:
            return TokenStatus.DISCOVERED, "Risque modéré — candidat à surveillance"
        return TokenStatus.DISCOVERED, "Candidat intéressant — passed to analysis"

    async def _emit(self, event_type: str, message: str, symbol: str | None = None, data: dict | None = None):
        logger.info(event_type.lower(), message=message, symbol=symbol)
        if self.on_event:
            await self.on_event(event_type, message, symbol, data or {})

    def clear_graph(self) -> None:
        self.graph.clear()
        logger.info("graph_cleared")
