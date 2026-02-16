import apiClient from './client'

export interface SectorTag {
  id: number
  name: string
  color: string
  keywords: string
  sort_order: number
}

export interface SectorTagCreate {
  name: string
  color?: string
  keywords?: string
  sort_order?: number
}

export interface SectorTagUpdate {
  name?: string
  color?: string
  keywords?: string
  sort_order?: number
}

export async function getSectorTags(): Promise<SectorTag[]> {
  const { data } = await apiClient.get<SectorTag[]>('/sector-tags')
  return data
}

export async function createSectorTag(body: SectorTagCreate): Promise<SectorTag> {
  const { data } = await apiClient.post<SectorTag>('/sector-tags', body)
  return data
}

export async function updateSectorTag(id: number, body: SectorTagUpdate): Promise<SectorTag> {
  const { data } = await apiClient.put<SectorTag>(`/sector-tags/${id}`, body)
  return data
}

export async function deleteSectorTag(id: number): Promise<void> {
  await apiClient.delete(`/sector-tags/${id}`)
}

export async function seedSectorTags(): Promise<SectorTag[]> {
  const { data } = await apiClient.post<SectorTag[]>('/sector-tags/seed')
  return data
}
