import apiClient from './client'
import type { NotificationList } from '@/types/notification'

export async function getNotifications(): Promise<NotificationList> {
  const { data } = await apiClient.get<NotificationList>('/notifications')
  return data
}

export async function getUnreadCount(): Promise<number> {
  const { data } = await apiClient.get<{ count: number }>('/notifications/unread-count')
  return data.count
}

export async function markRead(id: number): Promise<void> {
  await apiClient.put(`/notifications/${id}/read`)
}

export async function markAllRead(): Promise<void> {
  await apiClient.put('/notifications/batch-read')
}
