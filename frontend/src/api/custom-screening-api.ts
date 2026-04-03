import apiClient from './client'
import type { ScoreResult } from '@/types/screening'

interface CustomScreeningFilters {
  industry?: string
  min_momentum_score?: number
  classification?: string
  min_close_price?: number
  max_close_price?: number
}

export async function runCustomScreening(filters: CustomScreeningFilters): Promise<ScoreResult[]> {
  const { data } = await apiClient.post('/custom-screening', filters)
  // Backend returns { success, count, results }
  return data.results ?? data
}
