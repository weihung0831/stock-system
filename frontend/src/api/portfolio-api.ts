import apiClient from './client'
import type { Portfolio, PortfolioCreate, PortfolioUpdate, RealtimeResponse } from '@/types/portfolio'

export async function getPortfolios(): Promise<Portfolio[]> {
  const { data } = await apiClient.get<Portfolio[]>('/portfolio')
  return data
}

export async function createPortfolio(payload: PortfolioCreate): Promise<Portfolio> {
  const { data } = await apiClient.post<Portfolio>('/portfolio', payload)
  return data
}

export async function updatePortfolio(id: number, payload: PortfolioUpdate): Promise<Portfolio> {
  const { data } = await apiClient.put<Portfolio>(`/portfolio/${id}`, payload)
  return data
}

export async function deletePortfolio(id: number): Promise<void> {
  await apiClient.delete(`/portfolio/${id}`)
}

export async function getRealtimeData(): Promise<RealtimeResponse> {
  const { data } = await apiClient.get<RealtimeResponse>('/portfolio/realtime')
  return data
}
