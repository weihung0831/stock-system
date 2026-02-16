import apiClient from './client'

interface HistoricalResult {
  score_date: string
  stocks: Array<{
    stock_id: string
    stock_name: string
    total_score: number
    rank: number
  }>
}

interface BacktestPerformance {
  stock_id: string
  stock_name: string
  total_score: number
  return_5d: number
  return_10d: number
  return_20d: number
}

export interface ScoreDateInfo {
  date: string
  backtestable: boolean
}

export async function getScoreDates(): Promise<ScoreDateInfo[]> {
  const { data } = await apiClient.get('/backtest/score-dates')
  return data.dates ?? []
}

export async function getHistoricalTopStocks(
  startDate: string,
  endDate: string,
): Promise<HistoricalResult[]> {
  const { data } = await apiClient.get('/backtest/history', {
    params: { start_date: startDate, end_date: endDate },
  })
  return data
}

export async function getBacktestPerformance(
  date: string,
  topN: number = 10,
): Promise<BacktestPerformance[]> {
  const { data } = await apiClient.get('/backtest/performance', {
    params: { score_date: date, top_n: topN },
  })
  return data.stocks ?? []
}
