"""Paper trading tests."""

from app.services.paper_trading import PaperTradingEngine


def test_create_buy_order():
    eng = PaperTradingEngine(initial_balance=1000)
    order = eng.create_order("BTC", "BUY", 25.0, 100.0)
    assert order is not None
    assert order.status == "FILLED"
    assert "BTC" in eng.positions
    assert eng.balance < 1000


def test_reject_over_max_amount():
    eng = PaperTradingEngine()
    order = eng.create_order("BTC", "BUY", 500.0, 100.0)
    assert order is None


def test_stop_loss_triggers():
    eng = PaperTradingEngine()
    eng.create_order("ETH", "BUY", 20.0, 100.0)
    events = eng.update_prices({"ETH": 90.0})
    assert len(events) == 1
    assert events[0]["reason"] == "STOP_LOSS_TRIGGERED"
    assert "ETH" not in eng.positions


def test_take_profit_triggers():
    eng = PaperTradingEngine()
    eng.create_order("SOL", "BUY", 20.0, 100.0)
    events = eng.update_prices({"SOL": 110.0})
    assert len(events) == 1
    assert events[0]["reason"] == "TAKE_PROFIT_TRIGGERED"


def test_reset():
    eng = PaperTradingEngine(initial_balance=5000)
    eng.create_order("BTC", "BUY", 20.0, 50.0)
    eng.reset()
    assert eng.balance == 5000
    assert len(eng.positions) == 0
