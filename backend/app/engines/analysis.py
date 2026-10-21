"""
Market analysis engine: indicators, liquidity, volatility, risk scoring.
"""

from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.models.schemas import MarketData

logger = get_logger("analysis")


class AnalysisEngine:
    """Produces structured analysis dicts consumed by JEV."""

    def analyze(self, market: MarketData) -> dict[str, Any]:
        risk_score = 0.0
        reasons: list[str] = []

        if market.liquidity_usd >= 500_000:
            liquidity_score = 1.0
        elif market.liquidity_usd >= 100_000:
            liquidity_score = 0.8
        elif market.liquidity_usd >= 50_000:
            liquidity_score = 0.6
        elif market.liquidity_usd >= 10_000:
            liquidity_score = 0.4
        else:
            liquidity_score = 0.1
            risk_score += 0.35
            reasons.append("low_liquidity")

        low_liquidity = market.liquidity_usd < 10_000

        vol = market.volatility_1h
        extreme_volatility = vol > 12.0
        if extreme_volatility:
            risk_score += 0.3
            reasons.append("extreme_volatility")
        elif vol > 6.0:
            risk_score += 0.15
            reasons.append("elevated_volatility")

        if market.spread_pct > 1.5:
            risk_score += 0.2
            reasons.append("wide_spread")
        elif market.spread_pct > 0.8:
            risk_score += 0.1

        if market.top_holder_pct is not None:
            if market.top_holder_pct > 50:
                risk_score += 0.35
                reasons.append("extreme_holder_concentration")
            elif market.top_holder_pct > 30:
                risk_score += 0.2
                reasons.append("high_holder_concentration")

        suspicious_contract = False
        if market.contract_age_hours is not None:
            if market.contract_age_hours < 6:
                risk_score += 0.4
                suspicious_contract = True
                reasons.append("very_new_contract")
            elif market.contract_age_hours < 48:
                risk_score += 0.2
                reasons.append("new_contract")

        change = market.change_24h
        if change > 15:
            momentum_score = 0.8
        elif change > 5:
            momentum_score = 0.5
        elif change > 0:
            momentum_score = 0.2
        elif change > -5:
            momentum_score = -0.2
        elif change > -15:
            momentum_score = -0.5
        else:
            momentum_score = -0.8
            risk_score += 0.1
            reasons.append("strong_negative_momentum")

        if market.liquidity_usd > 0:
            vol_liq_ratio = market.volume_24h / market.liquidity_usd
            if vol_liq_ratio > 5:
                risk_score += 0.15
                reasons.append("abnormal_volume_spike")

        risk_score = min(1.0, max(0.0, risk_score))

        result = {
            "symbol": market.symbol,
            "risk_score": round(risk_score, 3),
            "liquidity_score": round(liquidity_score, 3),
            "momentum_score": round(momentum_score, 3),
            "extreme_volatility": extreme_volatility,
            "low_liquidity": low_liquidity,
            "suspicious_contract": suspicious_contract,
            "reasons": reasons,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "analysis_completed",
            symbol=market.symbol,
            risk_score=risk_score,
            liquidity_score=liquidity_score,
            momentum=momentum_score,
        )
        return result
