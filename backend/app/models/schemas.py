"""
Pydantic schemas for Spider Jarvis.
All decisions and market data are strictly validated.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class DecisionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REJECT = "REJECT"
    WATCH = "WATCH"


class SpiderState(str, Enum):
    IDLE = "IDLE"
    SCANNING = "SCANNING"
    TARGET_SELECTED = "TARGET_SELECTED"
    TRAVELLING = "TRAVELLING"
    ANALYSING = "ANALYSING"
    WAITING_FOR_JEV = "WAITING_FOR_JEV"
    RISK_CHECK = "RISK_CHECK"
    PAPER_ORDER = "PAPER_ORDER"
    POSITION_OPEN = "POSITION_OPEN"
    POSITION_CLOSED = "POSITION_CLOSED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class TokenStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    FILTERED = "FILTERED"
    ANALYSING = "ANALYSING"
    HIGH_RISK = "HIGH_RISK"
    REJECTED = "REJECTED"
    PASSED_TO_JEV = "PASSED_TO_JEV"
    SELECTED_FOR_PAPER = "SELECTED_FOR_PAPER"
    POSITION_OPEN = "POSITION_OPEN"
    POSITION_CLOSED = "POSITION_CLOSED"
    BLOCKED_BY_RISK = "BLOCKED_BY_RISK"


class MarketData(BaseModel):
    symbol: str
    price: float
    change_24h: float = 0.0
    volume_24h: float = 0.0
    liquidity_usd: float = 0.0
    market_cap: Optional[float] = None
    holders_count: Optional[int] = None
    top_holder_pct: Optional[float] = None
    contract_age_hours: Optional[float] = None
    spread_pct: float = 0.0
    volatility_1h: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "mock"

    @field_validator("price", "volume_24h", "liquidity_usd")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("must be non-negative")
        return v


class TokenNode(BaseModel):
    id: str
    symbol: str
    price: float
    change_24h: float = 0.0
    liquidity_usd: float = 0.0
    volume_24h: float = 0.0
    risk_score: float = 0.0
    status: TokenStatus = TokenStatus.DISCOVERED
    last_update: datetime = Field(default_factory=datetime.utcnow)
    explanation: str = ""
    x: float = 0.0
    y: float = 0.0


class JEVDecision(BaseModel):
    """Strict decision format returned by JEV. Never bypasses Risk Engine."""
    decision: DecisionType
    confidence: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)
    summary: str = ""
    required_action: str = ""
    expires_at: datetime
    symbol: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("confidence", "risk_score")
    @classmethod
    def clamp(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class RiskCheckResult(BaseModel):
    approved: bool
    original_decision: DecisionType
    final_decision: DecisionType
    reasons: list[str] = Field(default_factory=list)
    risk_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaperOrder(BaseModel):
    id: str
    symbol: str
    side: str
    amount_usd: float
    price: float
    quantity: float
    stop_loss: float
    take_profit: float
    status: str = "CREATED"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    pnl: float = 0.0
    fees: float = 0.0
    reason: str = ""


class Position(BaseModel):
    id: str
    symbol: str
    side: str
    entry_price: float
    quantity: float
    amount_usd: float
    stop_loss: float
    take_profit: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "OPEN"


class SystemStatus(BaseModel):
    trading_mode: str
    live_trading_enabled: bool
    spider_state: SpiderState
    emergency_stop: bool
    data_connection: str
    last_data_update: Optional[datetime] = None
    risk_engine_status: str
    paper_balance: float
    open_positions: int
    daily_trades: int
    daily_pnl: float
    scans_count: int
    last_action: str = ""


class EventLog(BaseModel):
    id: str
    event_type: str
    message: str
    symbol: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "INFO"


class WSMessage(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ControlCommand(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
