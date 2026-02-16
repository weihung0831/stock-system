import apiClient from './client'

interface InstitutionalTrend {
  trade_date: string
  foreign_net: number
  trust_net: number
  dealer_net: number
}

interface MarginTrend {
  trade_date: string
  margin_balance: number
  short_balance: number
}

interface ChipStatsParams {
  days: number
  stock_id?: string
}

export async function getInstitutionalTrend(params: ChipStatsParams): Promise<InstitutionalTrend[]> {
  const { data } = await apiClient.get('/chip-stats/institutional', { params })
  return data.data ?? []
}

export async function getMarginTrend(params: ChipStatsParams): Promise<MarginTrend[]> {
  const { data } = await apiClient.get('/chip-stats/margin', { params })
  return data.data ?? []
}
