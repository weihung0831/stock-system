export interface ScoreResult {
  stock_id: string
  stock_name: string
  score_date: string
  momentum_score: number
  total_score: number
  classification: string
  buy_price: number | null
  stop_price: number | null
  add_price: number | null
  target_price: number | null
  sector_name: string | null
  sector_rank: number | null
  market_status: string | null
  rank: number
  industry: string | null
  close_price: number
  change_percent: number
}

export interface SectorRankItem {
  name: string
  return_pct: number
}

export interface ScreeningRequest {
  threshold: number
}
