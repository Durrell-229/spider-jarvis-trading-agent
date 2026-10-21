"""REST API routes for Spider Jarvis."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.orchestrator import orchestrator

router = APIRouter()


class CommandBody(BaseModel):
    action: str
    params: dict = {}


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "app": get_settings().app_name,
        "version": get_settings().app_version,
        "trading_mode": get_settings().effective_trading_mode,
        "live_enabled": get_settings().is_live_trading_allowed,
    }


@router.get("/status")
async def status():
    return orchestrator.get_status().model_dump(mode="json")


@router.get("/graph")
async def graph():
    nodes = orchestrator.crawler.get_graph_snapshot()
    return {"nodes": [n.model_dump(mode="json") for n in nodes]}


@router.get("/events")
async def events(limit: int = 100):
    logs = orchestrator.event_log[-limit:]
    return {"events": [e.model_dump(mode="json") for e in logs]}


@router.get("/paper/stats")
async def paper_stats():
    return orchestrator.paper.stats()


@router.get("/paper/positions")
async def paper_positions():
    return {
        "positions": [p.model_dump(mode="json") for p in orchestrator.paper.positions.values()]
    }


@router.get("/jev/latest")
async def jev_latest():
    return orchestrator.latest_jev or {}


@router.get("/safety")
async def safety_center():
    s = get_settings()
    return {
        "title": "Safety Center — Spider Jarvis",
        "what_it_can_do": [
            "Analyser des données de marché (mock / historiques)",
            "Calculer des scores de risque",
            "Produire des décisions JEV structurées",
            "Exécuter du paper trading simulé",
            "Backtester sur données historiques",
            "Afficher une interface temps réel avec araignée",
        ],
        "what_it_cannot_do": [
            "Garantir des profits",
            "Envoyer des ordres réels sans configuration explicite et confirmation",
            "Contourner CAPTCHA / authentification d'exchanges",
            "Accéder à des clés privées de wallet",
            "Fonctionner sans limites de risque",
        ],
        "paper_trading": {
            "description": "Toutes les opérations sont simulées. Aucun argent réel n'est engagé.",
            "initial_balance": 10000,
            "fees_simulated": True,
            "slippage_simulated": True,
        },
        "live_trading": {
            "enabled": s.is_live_trading_allowed,
            "requirements": [
                "TRADING_MODE=live",
                "LIVE_TRADING_CONFIRMATION=I_UNDERSTAND_THE_RISK",
                "Limites de risque obligatoires toujours actives",
            ],
            "warning": "Le trading réel comporte un risque de perte totale du capital.",
        },
        "risk_limits": {
            "max_trade_amount": s.max_trade_amount,
            "max_daily_loss": s.max_daily_loss,
            "max_open_positions": s.max_open_positions,
            "max_daily_trades": s.max_daily_trades,
            "stop_loss_pct": s.default_stop_loss_percent,
            "take_profit_pct": s.default_take_profit_percent,
        },
        "emergency_stop": orchestrator.emergency_stop,
    }


@router.post("/control")
async def control(body: CommandBody):
    action = body.action.lower()
    if action == "start":
        await orchestrator.start()
    elif action == "pause":
        await orchestrator.pause()
    elif action == "resume":
        await orchestrator.resume()
    elif action == "stop":
        await orchestrator.stop()
    elif action == "scan_now":
        await orchestrator.scan_now()
    elif action == "reset_paper":
        await orchestrator.reset_paper()
    elif action == "emergency_stop":
        await orchestrator.emergency_stop_now()
    elif action == "clear_emergency":
        await orchestrator.clear_emergency()
    elif action == "clear_graph":
        await orchestrator.clear_graph()
    else:
        raise HTTPException(400, f"Action inconnue: {action}")
    return {"ok": True, "action": action, "status": orchestrator.get_status().model_dump(mode="json")}
