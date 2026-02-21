export interface RightSideSignal {
  id: string
  label: string
  weight: number
  triggered: boolean
  description: string
}

export interface TradePrediction {
  entry: number
  stop_loss: number
  target: number
  risk_reward: number
  action: 'buy' | 'hold' | 'avoid'
  action_label: string
}

export interface RightSideSignalResult {
  stock_id: string
  signals: RightSideSignal[]
  triggered_count: number
  score: number
  prediction: TradePrediction | null
}

export interface RightSideScreenItem {
  stock_id: string
  stock_name: string
  signals: RightSideSignal[]
  triggered_count: number
  score: number
  prediction: TradePrediction | null
}

export interface RightSideScreenResponse {
  items: RightSideScreenItem[]
  total: number
  min_signals: number
}
