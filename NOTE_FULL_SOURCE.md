# Source complète

Le dépôt GitHub contient l'architecture et les fichiers principaux.

Certains modules volumineux (orchestrator, risk engine complet, mock provider, araignée canvas, dashboard) sont présents dans le workspace local :

`/home/workdir/artifacts/spider-jarvis-trading-agent/`

Pour une copie complète, cloner ce repo puis fusionner avec le dossier local, ou me demander de continuer le push des fichiers restants.

Fichiers critiques à vérifier :
- backend/app/services/orchestrator.py
- backend/app/risk/engine.py
- backend/app/services/paper_trading.py
- backend/app/data_providers/mock.py
- backend/app/models/schemas.py
- backend/app/crawler/crawler.py
- backend/app/jev/engine.py
- backend/app/engines/analysis.py
- frontend/src/components/Spider.tsx
- frontend/src/components/Dashboard.tsx
- frontend/src/App.css
