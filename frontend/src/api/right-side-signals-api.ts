import apiClient from './client'
import type { RightSideSignalResult, RightSideScreenResponse } from '@/types/right-side-signals'

export async function getStockSignals(stockId: string): Promise<RightSideSignalResult> {
  const { data } = await apiClient.get<RightSideSignalResult>(`/right-side-signals/${stockId}`)
  return data
}

export async function screenRightSideSignals(minSignals = 2): Promise<RightSideScreenResponse> {
  const { data } = await apiClient.get<RightSideScreenResponse>('/right-side-signals/screen/batch', {
    params: { min_signals: minSignals },
  })
  return data
}
