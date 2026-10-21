export type SpiderState =
  | 'IDLE'
  | 'SCANNING'
  | 'TARGET_SELECTED'
  | 'TRAVELLING'
  | 'ANALYSING'
  | 'WAITING_FOR_JEV'
  | 'RISK_CHECK'
  | 'PAPER_ORDER'
  | 'POSITION_OPEN'
  | 'POSITION_CLOSED'
  | 'REJECTED'
  | 'ERROR'
  | 'EMERGENCY_STOP';

export interface TokenNode {
  id: string;
  symbol: string;
  price: number;
  change_24h: number;
  liquidity_usd: number;
  volume_24h: number;
  risk_score: number;
  status: string;
  last_update: string;
  explanation: string;
  x: number;
  y: number;
}

export interface SystemStatus {
  trading_mode: string;
  live_trading_enabled: boolean;
  spider_state: SpiderState;
  emergency_stop: boolean;
  data_connection: string;
  last_data_update: string | null;
  risk_engine_status: string;
  paper_balance: number;
  open_positions: number;
  daily_trades: number;
  daily_pnl: number;
  scans_count: number;
  last_action: string;
}

export interface EventLog {
  id: string;
  event_type: string;
  message: string;
  symbol?: string;
  data: Record<string, unknown>;
  timestamp: string;
  level: string;
}

export interface JEVDecision {
  decision: string;
  confidence: number;
  risk_score: number;
  reason_codes: string[];
  summary: string;
  required_action: string;
  expires_at: string;
  symbol: string;
  timestamp: string;
}

export interface PaperStats {
  paper_balance: number;
  initial_balance: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  win_rate: number;
  trade_count: number;
  open_positions: number;
  daily_pnl: number;
  daily_trades: number;
  total_fees: number;
  exposure: number;
}

export const STATE_COLORS: Record<SpiderState, string> = {
  IDLE: '#3b82f6',
  SCANNING: '#22d3ee',
  TARGET_SELECTED: '#22d3ee',
  TRAVELLING: '#22d3ee',
  ANALYSING: '#eab308',
  WAITING_FOR_JEV: '#a855f7',
  RISK_CHECK: '#eab308',
  PAPER_ORDER: '#22c55e',
  POSITION_OPEN: '#22c55e',
  POSITION_CLOSED: '#22c55e',
  REJECTED: '#ef4444',
  ERROR: '#ef4444',
  EMERGENCY_STOP: '#ef4444',
};
