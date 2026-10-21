"""WebSocket endpoint for real-time events."""

import asyncio
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.orchestrator import orchestrator

logger = get_logger("websocket")
router = APIRouter()

_clients: Set[WebSocket] = set()


async def broadcast(message: dict) -> None:
    dead = []
    for ws in _clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.discard(ws)


orchestrator.set_broadcast(broadcast)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)
    logger.info("ws_connected", clients=len(_clients))

    try:
        await websocket.send_json({
            "type": "status",
            "payload": orchestrator.get_status().model_dump(mode="json"),
        })
        nodes = orchestrator.crawler.get_graph_snapshot()
        await websocket.send_json({
            "type": "graph",
            "payload": {"nodes": [n.model_dump(mode="json") for n in nodes]},
        })
        await websocket.send_json({
            "type": "paper_stats",
            "payload": orchestrator.paper.stats(),
        })

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                if isinstance(data, dict) and data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif isinstance(data, dict) and data.get("type") == "control":
                    action = data.get("action")
                    if action:
                        mapping = {
                            "start": orchestrator.start,
                            "pause": orchestrator.pause,
                            "resume": orchestrator.resume,
                            "stop": orchestrator.stop,
                            "scan_now": orchestrator.scan_now,
                            "reset_paper": orchestrator.reset_paper,
                            "emergency_stop": orchestrator.emergency_stop_now,
                            "clear_emergency": orchestrator.clear_emergency,
                            "clear_graph": orchestrator.clear_graph,
                        }
                        fn = mapping.get(action)
                        if fn:
                            await fn()
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("ws_error", error=str(e))
    finally:
        _clients.discard(websocket)
        logger.info("ws_disconnected", clients=len(_clients))
