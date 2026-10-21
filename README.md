# SPIDER JARVIS TRADING AGENT

Agent IA de surveillance et d'analyse des marchés crypto, avec interface futuriste (araignée animée temps réel).

**Mode par défaut : PAPER TRADING uniquement.**
Aucun ordre réel n'est envoyé tant que vous n'avez pas explicitement configuré le mode live avec confirmation.

## Architecture

```
spider-jarvis-trading-agent/
├── backend/                 # FastAPI + WebSocket
│   ├── app/
│   │   ├── api/             # REST + WebSocket
│   │   ├── core/            # Config, logging
│   │   ├── crawler/         # Scan & graphe de tokens
│   │   ├── data_providers/  # Mock (offline)
│   │   ├── engines/         # Analyse
│   │   ├── jev/             # Module de décision JEV
│   │   ├── risk/            # Risk Engine
│   │   ├── services/        # Orchestrateur + Paper Trading
│   │   └── models/          # Schémas Pydantic
│   └── tests/
├── frontend/                # React + TypeScript + Vite
├── scripts/
├── .env.example
└── README.md
```

## Installation

### Windows
```powershell
.\scripts\install_windows.ps1
.\scripts\start_windows.ps1
```

### Linux / macOS
```bash
cp .env.example .env
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../frontend && npm install && npm install zustand
# Terminal 1
cd backend && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Terminal 2
cd frontend && npm run dev -- --host
```

### URLs
| Service   | URL                        |
|-----------|----------------------------|
| Frontend  | http://localhost:5173      |
| Backend   | http://localhost:8000      |
| API Docs  | http://localhost:8000/docs |
| Safety    | http://localhost:8000/api/safety |

## Sécurité

Live trading UNIQUEMENT si:
```
TRADING_MODE=live
LIVE_TRADING_CONFIRMATION=I_UNDERSTAND_THE_RISK
```

Sans cette confirmation exacte, le système **reste en paper trading**.

## Avertissement

Logiciel éducatif. Aucune garantie de profit. Risque de perte en capital sur les marchés crypto.
