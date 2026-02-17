import apiClient from './client'
import type { LLMReport } from '@/types/report'
import type { PaginatedResponse } from '@/types/stock'

export async function getLatestReports(): Promise<LLMReport[]> {
  const { data } = await apiClient.get<LLMReport[]>('/reports/latest')
  return data
}

export async function getStockReport(stockId: string): Promise<LLMReport | null> {
  const { data } = await apiClient.get<LLMReport | null>(`/reports/${stockId}`)
  return data
}

export async function generateStockReport(stockId: string): Promise<LLMReport> {
  const { data } = await apiClient.post<LLMReport>(`/reports/${stockId}/generate`)
  return data
}

export async function getReportHistory(
  stockId: string,
  page: number = 1,
): Promise<PaginatedResponse<LLMReport>> {
  const { data } = await apiClient.get<PaginatedResponse<LLMReport>>(`/reports/history/${stockId}`, {
    params: { page },
  })
  return data
}
