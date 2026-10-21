"""
JEV — Decision Evaluation Module.
Receives structured data only, returns strictly validated JSON decisions.
Never bypasses the Risk Engine.
"""

from datetime import datetime, timedelta
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import DecisionType, JEVDecision, MarketData

logger = get_logger("jev")


class JEVEngine:
    """
    Rule-based JEV for MVP.
    Can later be replaced by an LLM provider without changing the interface.
    """

    def __init__(self):
        self.settings = get_settings()

    def evaluate(self, market: MarketData, analysis: dict) -> JEVDecision:
        """
        Produce a decision from market data + analysis results.
        Output is always a valid JEVDecision.
        """
        risk_score = float(analysis.get("risk_score", 0.5))
        liquidity_score = float(analysis.get("liquidity_score", 0.5))
        momentum_score = float(analysis.get("momentum_score", 0.0))
        volatility_flag = bool(analysis.get("extreme_volatility", False))
        low_liquidity = bool(analysis.get("low_liquidity", False))
        suspicious = bool(analysis.get("suspicious_contract", False))

        reason_codes: list[str] = []
        confidence = 0.5
        decision = DecisionType.HOLD
        summary = ""
        required_action = "NONE"

        if suspicious:
            decision = DecisionType.REJECT
            reason_codes.append("SUSPICIOUS_CONTRACT")
            confidence = 0.9
            risk_score = max(risk_score, 0.9)
            summary = f"{market.symbol}: contrat suspect détecté"
            required_action = "BLOCK"
        elif low_liquidity:
            decision = DecisionType.REJECT
            reason_codes.append("LOW_LIQUIDITY")
            confidence = 0.85
            risk_score = max(risk_score, 0.75)
            summary = f"{market.symbol}: liquidité insuffisante"
            required_action = "FILTER"
        elif volatility_flag:
            decision = DecisionType.WATCH
            reason_codes.append("EXTREME_VOLATILITY")
            confidence = 0.7
            risk_score = max(risk_score, 0.7)
            summary = f"{market.symbol}: volatilité extrême — surveillance"
            required_action = "MONITOR"
        elif risk_score >= 0.8:
            decision = DecisionType.REJECT
            reason_codes.append("HIGH_RISK_SCORE")
            confidence = 0.8
            summary = f"{market.symbol}: score de risque trop élevé ({risk_score:.2f})"
            required_action = "BLOCK"
        elif momentum_score > 0.6 and liquidity_score > 0.5 and risk_score < 0.5:
            decision = DecisionType.BUY
            reason_codes.append("POSITIVE_MOMENTUM")
            reason_codes.append("ADEQUATE_LIQUIDITY")
            confidence = min(0.9, 0.5 + momentum_score * 0.4)
            summary = f"{market.symbol}: momentum positif, liquidité ok, risque modéré"
            required_action = "PAPER_BUY"
        elif momentum_score < -0.5 and risk_score < 0.6:
            decision = DecisionType.SELL
            reason_codes.append("NEGATIVE_MOMENTUM")
            confidence = min(0.85, 0.5 + abs(momentum_score) * 0.3)
            summary = f"{market.symbol}: momentum négatif"
            required_action = "PAPER_SELL"
        else:
            decision = DecisionType.HOLD
            reason_codes.append("NO_CLEAR_SIGNAL")
            confidence = 0.55
            summary = f"{market.symbol}: aucun signal clair — hold"
            required_action = "WAIT"

        expires = datetime.utcnow() + timedelta(minutes=5)

        result = JEVDecision(
            decision=decision,
            confidence=round(confidence, 3),
            risk_score=round(risk_score, 3),
            reason_codes=reason_codes,
            summary=summary,
            required_action=required_action,
            expires_at=expires,
            symbol=market.symbol,
            timestamp=datetime.utcnow(),
        )

        logger.info(
            "jev_decision",
            symbol=market.symbol,
            decision=decision.value,
            confidence=confidence,
            risk_score=risk_score,
            reasons=reason_codes,
        )
        return result
