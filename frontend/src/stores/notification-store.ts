import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getNotifications,
  getUnreadCount,
  markRead as apiMarkRead,
  markAllRead as apiMarkAllRead,
} from '@/api/notification-api'
import type { Notification } from '@/types/notification'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)

  let pollingTimer: ReturnType<typeof setInterval> | null = null

  async function fetchNotifications() {
    loading.value = true
    try {
      const res = await getNotifications()
      notifications.value = res.items
    } finally {
      loading.value = false
    }
  }

  async function fetchUnreadCount() {
    try {
      const count = await getUnreadCount()
      if (count !== unreadCount.value) unreadCount.value = count
    } catch {
      // ignore
    }
  }

  async function markRead(id: number) {
    await apiMarkRead(id)
    const item = notifications.value.find(n => n.id === id)
    if (item) item.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  async function markAllRead() {
    await apiMarkAllRead()
    notifications.value.forEach(n => (n.is_read = true))
    unreadCount.value = 0
  }

  function startPolling() {
    stopPolling()
    fetchUnreadCount()
    pollingTimer = setInterval(fetchUnreadCount, 10000)
  }

  function stopPolling() {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  return {
    notifications,
    unreadCount,
    loading,
    fetchNotifications,
    fetchUnreadCount,
    markRead,
    markAllRead,
    startPolling,
    stopPolling,
  }
})
