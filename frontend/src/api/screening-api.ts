import apiClient from './client'
import type { ScoreResult, ScreeningRequest, SectorRankItem } from '@/types/screening'

export interface ScreeningResultsResponse {
  items: ScoreResult[]
  total: number
  threshold: number
  market_status?: string
  top_sectors?: SectorRankItem[]
}

export async function runScreening(request: ScreeningRequest): Promise<void> {
  await apiClient.post('/screening/run', request)
}

export async function getResults(date?: string): Promise<ScreeningResultsResponse> {
  const { data } = await apiClient.get('/screening/results', {
    params: { score_date: date },
  })
  return data
}

export async function getStockScore(stockId: string): Promise<ScoreResult> {
  const { data } = await apiClient.get<ScoreResult>(`/screening/results/${stockId}`)
  return data
}
