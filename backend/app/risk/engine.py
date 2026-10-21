"""
Risk Engine — always has the final word.
Transforms BUY/SELL into REJECT when rules are violated.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import (
    DecisionType,
    JEVDecision,
    MarketData,
    RiskCheckResult,
)

logger = get_logger("risk_engine")


class RiskEngine:
    """Independent Risk Engine. JEV decisions MUST pass through here."""

    def __init__(self):
        self.settings = get_settings()
        self._daily_pnl: float = 0.0
        self._daily_trades: int = 0
        self._open_positions: int = 0
        self._last_loss_time: Optional[datetime] = None
        self._consecutive_losses: int = 0
        self._emergency_stop: bool = False
        self._day_start = datetime.utcnow().date()

    def reset_daily_if_needed(self) -> None:
        today = datetime.utcnow().date()
        if today != self._day_start:
            self._daily_pnl = 0.0
            self._daily_trades = 0
            self._day_start = today
            logger.info("risk_engine_daily_reset", date=str(today))

    def set_emergency_stop(self, value: bool) -> None:
        self._emergency_stop = value
        logger.warning("emergency_stop_set", value=value)

    @property
    def is_emergency_stopped(self) -> bool:
        return self._emergency_stop

    def update_stats(
        self,
        daily_pnl: float,
        daily_trades: int,
        open_positions: int,
        consecutive_losses: int = 0,
        last_loss_time: Optional[datetime] = None,
    ) -> None:
        self._daily_pnl = daily_pnl
        self._daily_trades = daily_trades
        self._open_positions = open_positions
        self._consecutive_losses = consecutive_losses
        self._last_loss_time = last_loss_time

    def check(
        self,
        decision: JEVDecision,
        market: MarketData,
        proposed_amount: float,
    ) -> RiskCheckResult:
        self.reset_daily_if_needed()
        reasons: list[str] = []
        original = decision.decision
        final = original
        risk_score = decision.risk_score

        if self._emergency_stop:
            reasons.append("EMERGENCY_STOP_ACTIVE")
            final = DecisionType.REJECT
            return self._result(False, original, final, reasons, 1.0)

        if self.settings.effective_trading_mode != "paper":
            pass

        age = (datetime.utcnow() - market.timestamp).total_seconds()
        if age > self.settings.max_data_age_seconds:
            reasons.append(f"STALE_DATA_AGE_{int(age)}s")
            final = DecisionType.REJECT

        if self._daily_pnl <= -self.settings.max_daily_loss:
            reasons.append("MAX_DAILY_LOSS_REACHED")
            final = DecisionType.REJECT

        if self._daily_trades >= self.settings.max_daily_trades:
            reasons.append("MAX_DAILY_TRADES_REACHED")
            final = DecisionType.REJECT

        if original == DecisionType.BUY and self._open_positions >= self.settings.max_open_positions:
            reasons.append("MAX_OPEN_POSITIONS_REACHED")
            final = DecisionType.REJECT

        if proposed_amount > self.settings.max_trade_amount:
            reasons.append(f"AMOUNT_EXCEEDS_MAX_{self.settings.max_trade_amount}")
            final = DecisionType.REJECT

        if proposed_amount <= 0 and original in (DecisionType.BUY, DecisionType.SELL):
            reasons.append("INVALID_AMOUNT")
            final = DecisionType.REJECT

        min_liquidity = 10_000.0
        if market.liquidity_usd < min_liquidity:
            reasons.append(f"LOW_LIQUIDITY_{market.liquidity_usd:.0f}")
            risk_score = max(risk_score, 0.8)
            if original == DecisionType.BUY:
                final = DecisionType.REJECT

        if market.spread_pct > 2.0:
            reasons.append(f"EXCESSIVE_SPREAD_{market.spread_pct:.2f}%")
            risk_score = max(risk_score, 0.7)
            if original == DecisionType.BUY:
                final = DecisionType.REJECT

        if market.volatility_1h > 15.0:
            reasons.append(f"EXTREME_VOLATILITY_{market.volatility_1h:.1f}%")
            risk_score = max(risk_score, 0.85)
            if original == DecisionType.BUY:
                final = DecisionType.REJECT

        if market.contract_age_hours is not None and market.contract_age_hours < 24:
            reasons.append("NEW_CONTRACT_INSUFFICIENT_DATA")
            risk_score = max(risk_score, 0.75)
            if original == DecisionType.BUY:
                final = DecisionType.REJECT

        if market.top_holder_pct is not None and market.top_holder_pct > 40:
            reasons.append(f"HIGH_HOLDER_CONCENTRATION_{market.top_holder_pct:.0f}%")
            risk_score = max(risk_score, 0.7)
            if original == DecisionType.BUY:
                final = DecisionType.REJECT

        if self._consecutive_losses >= 3 and self._last_loss_time:
            elapsed = (datetime.utcnow() - self._last_loss_time).total_seconds()
            if elapsed < self.settings.cooldown_after_losses_seconds:
                reasons.append("COOLDOWN_AFTER_LOSSES")
                final = DecisionType.REJECT

        if decision.risk_score >= 0.8 and original == DecisionType.BUY:
            reasons.append("JEV_HIGH_RISK_SCORE")
            final = DecisionType.REJECT

        if decision.confidence < 0.4 and original in (DecisionType.BUY, DecisionType.SELL):
            reasons.append("LOW_CONFIDENCE")
            final = DecisionType.HOLD if final != DecisionType.REJECT else final

        approved = final in (DecisionType.BUY, DecisionType.SELL, DecisionType.HOLD, DecisionType.WATCH)
        if final == DecisionType.REJECT:
            approved = False

        result = self._result(approved, original, final, reasons, risk_score)
        logger.info(
            "risk_check_completed",
            symbol=decision.symbol,
            original=original.value,
            final=final.value,
            approved=approved,
            reasons=reasons,
        )
        return result

    def _result(
        self,
        approved: bool,
        original: DecisionType,
        final: DecisionType,
        reasons: list[str],
        risk_score: float,
    ) -> RiskCheckResult:
        return RiskCheckResult(
            approved=approved,
            original_decision=original,
            final_decision=final,
            reasons=reasons,
            risk_score=risk_score,
            timestamp=datetime.utcnow(),
        )
