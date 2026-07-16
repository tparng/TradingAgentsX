/**
 * TypeScript type definitions for TradingAgentsX API
 */

export interface AnalysisRequest {
  ticker: string;
  analysis_date: string;
  analysts?: string[];
  research_depth?: number;
  market_type?: "us" | "twse" | "tpex";  // 市場類型：美股、上市、上櫃/興櫃
  quick_think_llm?: string;
  deep_think_llm?: string;

  // API Configuration
  openai_api_key?: string;
  openai_base_url?: string;
  quick_think_base_url?: string;
  deep_think_base_url?: string;
  quick_think_api_key?: string;
  deep_think_api_key?: string;
  embedding_base_url?: string;
  embedding_api_key?: string;
  embedding_model?: string;  // Embedding model: 'all-MiniLM-L6-v2' (local), 'text-embedding-3-small' (OpenAI), etc.
  alpha_vantage_api_key?: string;
  finmind_api_key?: string;  // 台灣股市資料 API
  language?: "en" | "zh-TW";  // Language for agent reports
}

export interface PriceData {
  Date: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  "Adj Close"?: number; // Optional adjusted close price
  Volume: number;
}

export interface PriceStats {
  growth_rate: number;
  duration_days: number;
  start_date: string;
  end_date: string;
  start_price: number;
  end_price: number;
}

export interface AnalysisResponse {
  status: string;
  ticker: string;
  analysis_date: string;
  market_type?: "us" | "twse" | "tpex";  // 市場類型：美股、上市、上櫃/興櫃
  decision?: any;
  reports?: any;
  error?: string;
  error_type?: string;
  retry_after?: number;
  quota_limit?: number;
  price_data?: PriceData[];
  price_stats?: PriceStats;
  deep_think_llm?: string;   // Deep thinking model used for this analysis
  quick_think_llm?: string;  // Quick thinking model used for this analysis
}

export interface Decision {
  action: string;
  quantity?: number;
  reasoning?: string;
  confidence?: number;
}

export interface Reports {
  market_report?: string;
  sentiment_report?: string;
  news_report?: string;
  fundamentals_report?: string;
  investment_plan?: string;
  trader_investment_plan?: string;
  final_trade_decision?: string;
  investment_debate_state?: DebateState;
  risk_debate_state?: DebateState;
}

export interface DebateState {
  bull_history?: string;
  bear_history?: string;
  risky_history?: string;
  safe_history?: string;
  neutral_history?: string;
  judge_decision?: string;
}

export interface ConfigResponse {
  available_analysts: string[];
  available_llms: {
    [provider: string]: string[];
  };
  default_config: {
    [key: string]: any;
  };
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface Ticker {
  symbol: string;
  name: string;
}

// Task Management Types

export interface TaskCreatedResponse {
  task_id: string;
  status: "pending";
  message: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelling" | "cancelled";
  created_at: string;
  updated_at: string;
  progress?: string;
  result?: AnalysisResponse;
  error?: string;
  completed_at?: string;
}

// Chat Types

export interface ChatMessageRequest {
  message: string;
  reports: any;
  ticker: string;
  analysis_date: string;
  history?: { role: string; content: string }[];
  model: string;
  api_key: string;
  base_url: string;
  language?: "en" | "zh-TW";
}

export interface ChatMessageResponse {
  reply: string;
}

// Watchlist Types

export interface WatchlistItem {
  id: string;
  ticker: string;
  market_type: string;
  notes?: string;
  added_at: string;
  last_analyzed_at?: string;
  last_recommendation?: string;
  last_score?: number;
}

export interface WatchlistStatus {
  jobs: { id: string; next_run: string | null }[];
  sheets_configured: boolean;
  telegram_configured: boolean;
}

export interface ScreenerParams {
  min_price_change_pct: number;
  min_volume_ratio: number;
  price_change_weight: number;
  include_us: boolean;
  include_tw: boolean;
  max_screener_candidates: number;
  llm_top_n: number;
}

export const DEFAULT_SCREENER_PARAMS: ScreenerParams = {
  min_price_change_pct: 1.5,
  min_volume_ratio: 1.5,
  price_change_weight: 0.6,
  include_us: true,
  include_tw: true,
  max_screener_candidates: 20,
  llm_top_n: 8,
};

export interface CandidateDetail {
  ticker: string;
  market_type: string;
  signal?: string;
  price_change_pct?: number;
  volume_ratio?: number;
  rsi?: number;
  current_price?: number;
  price_low_30d?: number;
  price_high_30d?: number;
  report_md: string;
  generated_at: string;
}

export interface WatchlistCandidate {
  id: string;
  ticker: string;
  market_type: string;
  price_change_pct?: number;
  volume_ratio?: number;
  rsi?: number;
  rationale?: string;
  rank?: number;
  signal?: "BULLISH" | "BEARISH" | "NEUTRAL";
  screened_at: string;
  status: "pending" | "added" | "dismissed";
}
