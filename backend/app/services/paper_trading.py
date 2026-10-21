"""
Paper Trading engine — simulation only.
Never sends real orders. Clear separation from any live path.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import PaperOrder, Position

logger = get_logger("paper_trading")

FEE_RATE = 0.001
SLIPPAGE_PCT = 0.05


class PaperTradingEngine:
    def __init__(self, initial_balance: float = 10_000.0):
        self.settings = get_settings()
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.positions: dict[str, Position] = {}
        self.orders: list[PaperOrder] = []
        self.closed_trades: list[dict] = []
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.total_fees = 0.0
        self._day = datetime.utcnow().date()

    def _reset_daily(self) -> None:
        today = datetime.utcnow().date()
        if today != self._day:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self._day = today

    def create_order(
        self,
        symbol: str,
        side: str,
        amount_usd: float,
        price: float,
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
        reason: str = "",
    ) -> Optional[PaperOrder]:
        self._reset_daily()
        settings = self.settings

        if amount_usd > settings.max_trade_amount:
            logger.warning("paper_order_rejected_amount", amount=amount_usd)
            return None
        if self.daily_trades >= settings.max_daily_trades:
            logger.warning("paper_order_rejected_daily_limit")
            return None
        if side == "BUY" and len(self.positions) >= settings.max_open_positions:
            logger.warning("paper_order_rejected_max_positions")
            return None
        if side == "BUY" and amount_usd > self.balance:
            logger.warning("paper_order_rejected_insufficient_balance")
            return None

        slip = price * (SLIPPAGE_PCT / 100)
        fill_price = price + slip if side == "BUY" else price - slip
        qty = amount_usd / fill_price
        fees = amount_usd * FEE_RATE

        sl_pct = stop_loss_pct or settings.default_stop_loss_percent
        tp_pct = take_profit_pct or settings.default_take_profit_percent

        if side == "BUY":
            stop_loss = fill_price * (1 - sl_pct / 100)
            take_profit = fill_price * (1 + tp_pct / 100)
        else:
            stop_loss = fill_price * (1 + sl_pct / 100)
            take_profit = fill_price * (1 - tp_pct / 100)

        order = PaperOrder(
            id=str(uuid4()),
            symbol=symbol,
            side=side,
            amount_usd=amount_usd,
            price=fill_price,
            quantity=qty,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status="FILLED",
            created_at=datetime.utcnow(),
            filled_at=datetime.utcnow(),
            fees=fees,
            reason=reason,
        )

        if side == "BUY":
            self.balance -= amount_usd + fees
            pos = Position(
                id=order.id,
                symbol=symbol,
                side=side,
                entry_price=fill_price,
                quantity=qty,
                amount_usd=amount_usd,
                stop_loss=stop_loss,
                take_profit=take_profit,
                current_price=fill_price,
                opened_at=datetime.utcnow(),
            )
            self.positions[symbol] = pos
        else:
            if symbol in self.positions:
                self._close_position(symbol, fill_price, "MANUAL_SELL")

        self.orders.append(order)
        self.daily_trades += 1
        self.total_fees += fees

        logger.info(
            "paper_order_created",
            order_id=order.id,
            symbol=symbol,
            side=side,
            amount=amount_usd,
            price=fill_price,
            mode="PAPER",
        )
        return order

    def update_prices(self, prices: dict[str, float]) -> list[dict]:
        events = []
        for symbol, pos in list(self.positions.items()):
            if symbol not in prices:
                continue
            price = prices[symbol]
            pos.current_price = price
            if pos.side == "BUY":
                pos.unrealized_pnl = (price - pos.entry_price) * pos.quantity
            else:
                pos.unrealized_pnl = (pos.entry_price - price) * pos.quantity

            if pos.side == "BUY" and price <= pos.stop_loss:
                events.append(self._close_position(symbol, price, "STOP_LOSS_TRIGGERED"))
            elif pos.side == "BUY" and price >= pos.take_profit:
                events.append(self._close_position(symbol, price, "TAKE_PROFIT_TRIGGERED"))
        return [e for e in events if e]

    def _close_position(self, symbol: str, price: float, reason: str) -> dict:
        pos = self.positions.pop(symbol, None)
        if not pos:
            return {}
        fees = pos.amount_usd * FEE_RATE
        if pos.side == "BUY":
            pnl = (price - pos.entry_price) * pos.quantity - fees
            self.balance += pos.quantity * price - fees
        else:
            pnl = (pos.entry_price - price) * pos.quantity - fees
            self.balance += pos.amount_usd + pnl

        self.daily_pnl += pnl
        self.total_fees += fees
        trade = {
            "id": pos.id,
            "symbol": symbol,
            "side": pos.side,
            "entry": pos.entry_price,
            "exit": price,
            "pnl": round(pnl, 4),
            "reason": reason,
            "closed_at": datetime.utcnow().isoformat(),
        }
        self.closed_trades.append(trade)
        logger.info("position_closed", **trade)
        return trade

    def reset(self) -> None:
        self.balance = self.initial_balance
        self.positions.clear()
        self.orders.clear()
        self.closed_trades.clear()
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.total_fees = 0.0
        logger.info("paper_trading_reset", balance=self.balance)

    def stats(self) -> dict:
        realized = sum(t["pnl"] for t in self.closed_trades)
        unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        wins = sum(1 for t in self.closed_trades if t["pnl"] > 0)
        total = len(self.closed_trades)
        return {
            "paper_balance": round(self.balance, 2),
            "initial_balance": self.initial_balance,
            "realized_pnl": round(realized, 2),
            "unrealized_pnl": round(unrealized, 2),
            "total_pnl": round(realized + unrealized, 2),
            "win_rate": round(wins / total, 3) if total else 0.0,
            "trade_count": total,
            "open_positions": len(self.positions),
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_trades": self.daily_trades,
            "total_fees": round(self.total_fees, 4),
            "exposure": round(sum(p.amount_usd for p in self.positions.values()), 2),
        }
