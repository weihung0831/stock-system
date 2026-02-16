import apiClient from './client'
import type { Stock, DailyPrice, InstitutionalData, MarginData, PaginatedResponse } from '@/types/stock'

export async function getStocks(params: {
  page?: number
  limit?: number
  search?: string
}): Promise<PaginatedResponse<Stock>> {
  const { data } = await apiClient.get<PaginatedResponse<Stock>>('/stocks', { params })
  return data
}

export async function getStockPrices(
  stockId: string,
  startDate?: string,
  endDate?: string,
): Promise<DailyPrice[]> {
  const { data } = await apiClient.get<DailyPrice[]>(`/stocks/${stockId}/prices`, {
    params: { start_date: startDate, end_date: endDate },
  })
  return data
}

export async function getStockInstitutional(
  stockId: string,
  startDate?: string,
  endDate?: string,
): Promise<InstitutionalData[]> {
  const { data } = await apiClient.get<InstitutionalData[]>(`/stocks/${stockId}/institutional`, {
    params: { start_date: startDate, end_date: endDate },
  })
  return data
}

export async function getStockMargin(
  stockId: string,
  startDate?: string,
  endDate?: string,
): Promise<MarginData[]> {
  const { data } = await apiClient.get<MarginData[]>(`/stocks/${stockId}/margin`, {
    params: { start_date: startDate, end_date: endDate },
  })
  return data
}
