export interface Portfolio {
  id: number
  stock_id: string
  stock_name: string
  cost_price: number
  quantity: number
  target_return_pct: number
  entry_momentum_grade: string | null
}

export interface PortfolioCreate {
  stock_id: string
  cost_price: number
  quantity: number
  target_return_pct: number
}

export interface PortfolioUpdate {
  cost_price?: number
  quantity?: number
  target_return_pct?: number
}

export interface RealtimeItem {
  portfolio_id: number
  stock_id: string
  stock_name: string
  cost_price: number
  current_price: number
  quantity: number
  profit_amount: number
  profit_pct: number
  target_return_pct: number
  target_reached: boolean
  is_realtime: boolean
  entry_momentum_grade: string | null
  current_momentum_grade: string | null
  momentum_status: string
}

export interface AlertItem {
  portfolio_id: number
  stock_id: string
  stock_name: string
  profit_pct: number
  target_return_pct: number
}

export interface RealtimeResponse {
  is_market_open: boolean
  is_realtime: boolean
  total_profit_amount: number
  total_profit_pct: number
  items: RealtimeItem[]
  new_alerts: AlertItem[]
}
