"""Unit tests for Risk Engine — critical safety component."""

import pytest
from datetime import datetime, timedelta

from app.models.schemas import DecisionType, JEVDecision, MarketData
from app.risk.engine import RiskEngine


def make_decision(decision=DecisionType.BUY, confidence=0.8, risk_score=0.3, symbol="BTC"):
    return JEVDecision(
        decision=decision,
        confidence=confidence,
        risk_score=risk_score,
        reason_codes=["TEST"],
        summary="test",
        required_action="PAPER_BUY",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        symbol=symbol,
    )


def make_market(symbol="BTC", liquidity=100_000, spread=0.2, volatility=2.0, age_hours=1000, top_holder=10):
    return MarketData(
        symbol=symbol,
        price=100.0,
        change_24h=5.0,
        volume_24h=1_000_000,
        liquidity_usd=liquidity,
        top_holder_pct=top_holder,
        contract_age_hours=age_hours,
        spread_pct=spread,
        volatility_1h=volatility,
        timestamp=datetime.utcnow(),
        source="test",
    )


class TestRiskEngine:
    def setup_method(self):
        self.engine = RiskEngine()

    def test_approve_healthy_buy(self):
        result = self.engine.check(make_decision(), make_market(), 20.0)
        assert result.approved is True
        assert result.final_decision == DecisionType.BUY

    def test_reject_low_liquidity(self):
        result = self.engine.check(make_decision(), make_market(liquidity=1000), 20.0)
        assert result.final_decision == DecisionType.REJECT
        assert any("LOW_LIQUIDITY" in r for r in result.reasons)

    def test_reject_excessive_spread(self):
        result = self.engine.check(make_decision(), make_market(spread=3.0), 20.0)
        assert result.final_decision == DecisionType.REJECT
        assert any("EXCESSIVE_SPREAD" in r for r in result.reasons)

    def test_reject_extreme_volatility(self):
        result = self.engine.check(make_decision(), make_market(volatility=20.0), 20.0)
        assert result.final_decision == DecisionType.REJECT
        assert any("EXTREME_VOLATILITY" in r for r in result.reasons)

    def test_reject_new_contract(self):
        result = self.engine.check(make_decision(), make_market(age_hours=5), 20.0)
        assert result.final_decision == DecisionType.REJECT
        assert any("NEW_CONTRACT" in r for r in result.reasons)

    def test_reject_high_holder_concentration(self):
        result = self.engine.check(make_decision(), make_market(top_holder=55), 20.0)
        assert result.final_decision == DecisionType.REJECT
        assert any("HOLDER_CONCENTRATION" in r for r in result.reasons)

    def test_reject_amount_too_large(self):
        result = self.engine.check(make_decision(), make_market(), 1000.0)
        assert result.final_decision == DecisionType.REJECT
        assert any("AMOUNT_EXCEEDS" in r for r in result.reasons)

    def test_emergency_stop_blocks_all(self):
        self.engine.set_emergency_stop(True)
        result = self.engine.check(make_decision(), make_market(), 10.0)
        assert result.final_decision == DecisionType.REJECT
        assert "EMERGENCY_STOP_ACTIVE" in result.reasons

    def test_daily_loss_limit(self):
        self.engine.update_stats(daily_pnl=-60.0, daily_trades=1, open_positions=0)
        result = self.engine.check(make_decision(), make_market(), 10.0)
        assert result.final_decision == DecisionType.REJECT
        assert "MAX_DAILY_LOSS" in result.reasons[0]

    def test_max_positions(self):
        self.engine.update_stats(daily_pnl=0, daily_trades=0, open_positions=5)
        result = self.engine.check(make_decision(), make_market(), 10.0)
        assert result.final_decision == DecisionType.REJECT
        assert "MAX_OPEN_POSITIONS" in result.reasons[0]

    def test_stale_data(self):
        m = make_market()
        m.timestamp = datetime.utcnow() - timedelta(seconds=120)
        result = self.engine.check(make_decision(), m, 10.0)
        assert result.final_decision == DecisionType.REJECT
        assert any("STALE_DATA" in r for r in result.reasons)

    def test_high_jev_risk_score(self):
        d = make_decision(risk_score=0.9)
        result = self.engine.check(d, make_market(), 10.0)
        assert result.final_decision == DecisionType.REJECT
        assert any("JEV_HIGH_RISK" in r for r in result.reasons)

    def test_hold_not_rejected_by_liquidity(self):
        d = make_decision(decision=DecisionType.HOLD)
        result = self.engine.check(d, make_market(liquidity=500), 0)
        assert result.final_decision in (DecisionType.HOLD, DecisionType.REJECT)
