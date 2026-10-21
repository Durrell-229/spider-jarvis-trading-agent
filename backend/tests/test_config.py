"""Security tests: trading mode never auto-enables live."""

from app.core.config import Settings


def test_default_is_paper():
    s = Settings(trading_mode="paper", live_trading_confirmation="")
    assert s.effective_trading_mode == "paper"
    assert s.is_live_trading_allowed is False


def test_live_without_confirmation_blocked():
    s = Settings(trading_mode="live", live_trading_confirmation="")
    assert s.is_live_trading_allowed is False
    assert s.effective_trading_mode == "paper"


def test_live_with_wrong_confirmation_blocked():
    s = Settings(trading_mode="live", live_trading_confirmation="yes")
    assert s.is_live_trading_allowed is False


def test_live_only_with_exact_confirmation():
    s = Settings(
        trading_mode="live",
        live_trading_confirmation="I_UNDERSTAND_THE_RISK",
    )
    assert s.is_live_trading_allowed is True
    assert s.effective_trading_mode == "live"
