import apiClient from './client'
import type { ScoreResult, ScreeningRequest, ScreeningWeights } from '@/types/screening'

export async function runScreening(request: ScreeningRequest): Promise<void> {
  await apiClient.post('/screening/run', request)
}

export async function getResults(date?: string): Promise<ScoreResult[]> {
  const { data } = await apiClient.get('/screening/results', {
    params: { score_date: date },
  })
  // Backend returns { items: [], total, threshold, weights }
  return data.items ?? []
}

export async function getStockScore(stockId: string): Promise<ScoreResult> {
  const { data } = await apiClient.get<ScoreResult>(`/screening/results/${stockId}`)
  return data
}

export async function getAutoWeights(): Promise<{ weights: ScreeningWeights; threshold: number }> {
  const { data } = await apiClient.get('/screening/settings/auto-weights')
  return data
}
