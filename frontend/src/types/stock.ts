export interface Stock {
  id: number
  stock_id: string
  stock_name: string
  market: string
  industry: string | null
}

export interface DailyPrice {
  stock_id: string
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  change_price: number
  change_percent: number
}

export interface InstitutionalData {
  stock_id: string
  trade_date: string
  foreign_buy: number
  foreign_sell: number
  foreign_net: number
  trust_buy: number
  trust_sell: number
  trust_net: number
  dealer_net: number
  total_net: number
}

export interface MarginData {
  stock_id: string
  trade_date: string
  margin_balance: number
  margin_change: number
  short_balance: number
  short_change: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
}
