"""
Central orchestrator: ties Crawler -> Analysis -> JEV -> Risk Engine -> Paper Trading.
Drives spider state machine and broadcasts events via WebSocket.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Optional
from uuid import uuid4

from app.core.config import get_settings
from app.core.logging import get_logger
from app.crawler.crawler import Crawler
from app.data_providers.factory import create_data_provider
from app.engines.analysis import AnalysisEngine
from app.jev.engine import JEVEngine
from app.models.schemas import (
    DecisionType,
    EventLog,
    SpiderState,
    SystemStatus,
    TokenStatus,
)
from app.risk.engine import RiskEngine
from app.services.paper_trading import PaperTradingEngine

logger = get_logger("orchestrator")


class Orchestrator:
    def __init__(self):
        self.settings = get_settings()
        self.provider = create_data_provider()
        self.analysis = AnalysisEngine()
        self.jev = JEVEngine()
        self.risk = RiskEngine()
        self.paper = PaperTradingEngine(initial_balance=10_000.0)
        self.crawler = Crawler(self.provider, self.analysis, on_event=self._on_crawler_event)

        self.spider_state = SpiderState.IDLE
        self.emergency_stop = False
        self.paused = False
        self.running = False
        self.last_action = "Systeme initialise"
        self.last_data_update: Optional[datetime] = None
        self.event_log: list[EventLog] = []
        self.latest_jev: Optional[dict] = None
        self._broadcast: Optional[Callable] = None
        self._task: Optional[asyncio.Task] = None
        self._scan_task: Optional[asyncio.Task] = None

    def set_broadcast(self, fn: Callable) -> None:
        self._broadcast = fn

    async def _emit(self, event_type: str, message: str, symbol: str | None = None, data: dict | None = None, level: str = "INFO"):
        entry = EventLog(
            id=str(uuid4()),
            event_type=event_type,
            message=message,
            symbol=symbol,
            data=data or {},
            timestamp=datetime.utcnow(),
            level=level,
        )
        self.event_log.append(entry)
        if len(self.event_log) > 500:
            self.event_log = self.event_log[-400:]
        self.last_action = message
        logger.info(event_type.lower(), message=message, symbol=symbol)
        if self._broadcast:
            await self._broadcast({
                "type": "event",
                "payload": entry.model_dump(mode="json"),
            })

    async def _on_crawler_event(self, event_type: str, message: str, symbol: str | None, data: dict):
        await self._emit(event_type, message, symbol, data)

    async def _set_state(self, state: SpiderState, message: str = ""):
        self.spider_state = state
        if self._broadcast:
            await self._broadcast({
                "type": "spider_state",
                "payload": {
                    "state": state.value,
                    "message": message or state.value,
                    "color": self._state_color(state),
                },
            })
        await self._emit("SPIDER_STATE", f"Araignee -> {state.value}: {message}", data={"state": state.value})

    def _state_color(self, state: SpiderState) -> str:
        mapping = {
            SpiderState.IDLE: "blue",
            SpiderState.SCANNING: "cyan",
            SpiderState.TARGET_SELECTED: "cyan",
            SpiderState.TRAVELLING: "cyan",
            SpiderState.ANALYSING: "yellow",
            SpiderState.WAITING_FOR_JEV: "violet",
            SpiderState.RISK_CHECK: "yellow",
            SpiderState.PAPER_ORDER: "green",
            SpiderState.POSITION_OPEN: "green",
            SpiderState.POSITION_CLOSED: "green",
            SpiderState.REJECTED: "red",
            SpiderState.ERROR: "red",
            SpiderState.EMERGENCY_STOP: "red",
        }
        return mapping.get(state, "blue")

    def get_status(self) -> SystemStatus:
        stats = self.paper.stats()
        return SystemStatus(
            trading_mode=self.settings.effective_trading_mode,
            live_trading_enabled=self.settings.is_live_trading_allowed,
            spider_state=self.spider_state,
            emergency_stop=self.emergency_stop,
            data_connection="connected" if self.last_data_update else "idle",
            last_data_update=self.last_data_update,
            risk_engine_status="STOPPED" if self.emergency_stop else "ACTIVE",
            paper_balance=stats["paper_balance"],
            open_positions=stats["open_positions"],
            daily_trades=stats["daily_trades"],
            daily_pnl=stats["daily_pnl"],
            scans_count=self.crawler.scans_count,
            last_action=self.last_action,
        )

    async def start(self) -> None:
        if self.running:
            return
        if self.emergency_stop:
            await self._emit("ERROR", "Impossible de demarrer: emergency stop actif.", level="ERROR")
            return
        self.running = True
        self.paused = False
        await self._set_state(SpiderState.IDLE, "Agent demarre — paper trading")
        await self._emit("SYSTEM_STARTED", "Spider Jarvis demarre en mode PAPER TRADING")
        self._task = asyncio.create_task(self._main_loop())

    async def pause(self) -> None:
        self.paused = True
        await self._set_state(SpiderState.IDLE, "En pause")
        await self._emit("SYSTEM_PAUSED", "Agent en pause")

    async def resume(self) -> None:
        if self.emergency_stop:
            return
        self.paused = False
        await self._set_state(SpiderState.IDLE, "Reprise")
        await self._emit("SYSTEM_RESUMED", "Agent repris")

    async def stop(self) -> None:
        self.running = False
        self.paused = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._set_state(SpiderState.IDLE, "Arrete")
        await self._emit("SYSTEM_STOPPED", "Agent arrete proprement")

    async def emergency_stop_now(self) -> None:
        self.emergency_stop = True
        self.risk.set_emergency_stop(True)
        self.running = False
        self.paused = True
        if self._task:
            self._task.cancel()
        await self._set_state(SpiderState.EMERGENCY_STOP, "ARRET D URGENCE")
        await self._emit("EMERGENCY_STOP", "Arret d urgence active — aucune nouvelle action", level="ERROR")

    async def clear_emergency(self) -> None:
        self.emergency_stop = False
        self.risk.set_emergency_stop(False)
        await self._set_state(SpiderState.IDLE, "Emergency stop leve")
        await self._emit("EMERGENCY_CLEARED", "Arret d urgence leve par l utilisateur")

    async def scan_now(self) -> None:
        if self.emergency_stop:
            return
        await self._run_scan_cycle()

    async def reset_paper(self) -> None:
        self.paper.reset()
        await self._emit("PAPER_RESET", "Paper trading reinitialise — solde 10 000 $")

    async def clear_graph(self) -> None:
        self.crawler.clear_graph()
        if self._broadcast:
            await self._broadcast({"type": "graph", "payload": {"nodes": []}})
        await self._emit("GRAPH_CLEARED", "Graphe efface")

    async def _main_loop(self) -> None:
        interval = self.settings.scan_interval_seconds
        while self.running:
            if not self.paused and not self.emergency_stop:
                try:
                    await self._run_scan_cycle()
                except Exception as e:
                    logger.exception("main_loop_error")
                    await self._set_state(SpiderState.ERROR, str(e))
                    await self._emit("ERROR", f"Erreur boucle: {e}", level="ERROR")
            await asyncio.sleep(interval)

    async def _run_scan_cycle(self) -> None:
        if self.emergency_stop:
            return

        await self._set_state(SpiderState.SCANNING, "Scan en cours...")
        nodes = await self.crawler.scan_once()
        self.last_data_update = datetime.utcnow()

        if self._broadcast:
            await self._broadcast({
                "type": "graph",
                "payload": {"nodes": [n.model_dump(mode="json") for n in nodes]},
            })
            await self._broadcast({
                "type": "status",
                "payload": self.get_status().model_dump(mode="json"),
            })

        candidates = [
            n for n in nodes
            if n.status == TokenStatus.DISCOVERED and n.risk_score < 0.65
        ]
        candidates.sort(key=lambda n: (n.risk_score, -n.change_24h))

        for node in candidates[:3]:
            if self.emergency_stop or self.paused:
                break
            await self._process_candidate(node.symbol)

        prices = {n.symbol: n.price for n in nodes}
        closed = self.paper.update_prices(prices)
        for trade in closed:
            await self._emit(
                trade.get("reason", "POSITION_CLOSED"),
                f"{trade['symbol']} ferme — PnL: {trade['pnl']:.2f} $",
                symbol=trade["symbol"],
                data=trade,
            )
            await self._set_state(SpiderState.POSITION_CLOSED, f"Position {trade['symbol']} fermee")

        self.risk.update_stats(
            daily_pnl=self.paper.daily_pnl,
            daily_trades=self.paper.daily_trades,
            open_positions=len(self.paper.positions),
        )

        await self._set_state(SpiderState.IDLE, "Cycle termine")
        if self._broadcast:
            await self._broadcast({
                "type": "status",
                "payload": self.get_status().model_dump(mode="json"),
            })
            await self._broadcast({
                "type": "paper_stats",
                "payload": self.paper.stats(),
            })

    async def _process_candidate(self, symbol: str) -> None:
        await self._set_state(SpiderState.TARGET_SELECTED, f"Cible: {symbol}")
        await asyncio.sleep(0.3)
        await self._set_state(SpiderState.TRAVELLING, f"Deplacement vers {symbol}")
        await asyncio.sleep(0.4)

        data = await self.provider.get_market_data(symbol)
        if not data:
            await self._set_state(SpiderState.ERROR, f"Pas de donnees pour {symbol}")
            return

        await self._set_state(SpiderState.ANALYSING, f"Analyse de {symbol}")
        analysis = self.analysis.analyze(data)
        await self._emit("RISK_ANALYSIS_STARTED", f"Analyse risque {symbol}", symbol=symbol, data=analysis)

        await self._set_state(SpiderState.WAITING_FOR_JEV, f"JEV evalue {symbol}")
        decision = self.jev.evaluate(data, analysis)
        self.latest_jev = decision.model_dump(mode="json")
        await self._emit(
            "JEV_DECISION",
            f"JEV: {decision.decision.value} ({decision.confidence:.0%}) — {decision.summary}",
            symbol=symbol,
            data=self.latest_jev,
        )
        if self._broadcast:
            await self._broadcast({"type": "jev", "payload": self.latest_jev})

        await self._set_state(SpiderState.RISK_CHECK, f"Risk Engine verifie {symbol}")
        amount = min(self.settings.max_trade_amount, 25.0)
        risk_result = self.risk.check(decision, data, amount)
        await self._emit(
            "RISK_ENGINE_APPROVED" if risk_result.approved else "RISK_ENGINE_REJECTED",
            f"Risk: {risk_result.final_decision.value} — {', '.join(risk_result.reasons) or 'OK'}",
            symbol=symbol,
            data=risk_result.model_dump(mode="json"),
        )

        if not risk_result.approved or risk_result.final_decision == DecisionType.REJECT:
            await self._set_state(SpiderState.REJECTED, f"{symbol} rejete par Risk Engine")
            if symbol in self.crawler.graph:
                self.crawler.graph[symbol].status = TokenStatus.BLOCKED_BY_RISK
            return

        if risk_result.final_decision == DecisionType.BUY:
            if self.settings.effective_trading_mode != "paper" and not self.settings.is_live_trading_allowed:
                await self._emit("ERROR", "Live trading non autorise — force en paper", level="ERROR")

            await self._set_state(SpiderState.PAPER_ORDER, f"Ordre paper BUY {symbol}")
            order = self.paper.create_order(
                symbol=symbol,
                side="BUY",
                amount_usd=amount,
                price=data.price,
                reason=decision.summary,
            )
            if order:
                await self._emit(
                    "PAPER_ORDER_CREATED",
                    f"Paper BUY {symbol} @ {order.price:.4f} — {amount}$",
                    symbol=symbol,
                    data=order.model_dump(mode="json"),
                )
                await self._set_state(SpiderState.POSITION_OPEN, f"Position paper ouverte: {symbol}")
                if symbol in self.crawler.graph:
                    self.crawler.graph[symbol].status = TokenStatus.SELECTED_FOR_PAPER
            else:
                await self._set_state(SpiderState.REJECTED, f"Ordre paper refuse pour {symbol}")

        elif risk_result.final_decision in (DecisionType.HOLD, DecisionType.WATCH):
            await self._set_state(SpiderState.IDLE, f"{symbol}: {risk_result.final_decision.value}")


orchestrator = Orchestrator()
