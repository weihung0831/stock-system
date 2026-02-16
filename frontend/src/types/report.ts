export interface LLMReport {
  id: number
  stock_id: string
  stock_name: string
  report_date: string
  chip_analysis: string
  fundamental_analysis: string
  technical_analysis: string
  news_sentiment: string
  news_summary: string
  risk_alerts: string[]
  recommendation: string
  confidence: string
}
