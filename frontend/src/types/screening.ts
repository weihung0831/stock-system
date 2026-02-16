export interface ScoreResult {
  stock_id: string
  stock_name: string
  score_date: string
  chip_score: number
  fundamental_score: number
  technical_score: number
  total_score: number
  rank: number
  industry: string | null
  close_price: number
  change_percent: number
}

export interface ScreeningWeights {
  chip: number
  fundamental: number
  technical: number
}

export interface ScreeningRequest {
  weights: ScreeningWeights
  threshold: number
}
