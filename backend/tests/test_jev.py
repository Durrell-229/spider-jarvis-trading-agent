"""Tests for JEV decision validation."""

from datetime import datetime, timedelta

import pytest

from app.jev.engine import JEVEngine
from app.models.schemas import DecisionType, MarketData


def make_market(**kwargs):
    defaults = dict(
        symbol="TEST",
        price=10.0,
        change_24h=8.0,
        volume_24h=500_000,
        liquidity_usd=80_000,
        spread_pct=0.3,
        volatility_1h=3.0,
        timestamp=datetime.utcnow(),
        source="test",
    )
    defaults.update(kwargs)
    return MarketData(**defaults)


class TestJEV:
    def setup_method(self):
        self.jev = JEVEngine()

    def test_buy_on_positive_momentum(self):
        analysis = {
            "risk_score": 0.3,
            "liquidity_score": 0.7,
            "momentum_score": 0.7,
            "extreme_volatility": False,
            "low_liquidity": False,
            "suspicious_contract": False,
        }
        d = self.jev.evaluate(make_market(), analysis)
        assert d.decision == DecisionType.BUY
        assert 0 <= d.confidence <= 1
        assert d.expires_at > datetime.utcnow()

    def test_reject_suspicious(self):
        analysis = {
            "risk_score": 0.9,
            "liquidity_score": 0.2,
            "momentum_score": 0.0,
            "extreme_volatility": False,
            "low_liquidity": False,
            "suspicious_contract": True,
        }
        d = self.jev.evaluate(make_market(), analysis)
        assert d.decision == DecisionType.REJECT
        assert "SUSPICIOUS_CONTRACT" in d.reason_codes

    def test_reject_low_liquidity(self):
        analysis = {
            "risk_score": 0.5,
            "liquidity_score": 0.1,
            "momentum_score": 0.5,
            "extreme_volatility": False,
            "low_liquidity": True,
            "suspicious_contract": False,
        }
        d = self.jev.evaluate(make_market(), analysis)
        assert d.decision == DecisionType.REJECT

    def test_schema_strict(self):
        analysis = {
            "risk_score": 0.4,
            "liquidity_score": 0.6,
            "momentum_score": 0.1,
            "extreme_volatility": False,
            "low_liquidity": False,
            "suspicious_contract": False,
        }
        d = self.jev.evaluate(make_market(), analysis)
        assert d.decision in list(DecisionType)
        assert isinstance(d.reason_codes, list)
        assert isinstance(d.summary, str)
