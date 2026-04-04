export interface Notification {
  id: number
  type: string
  title: string
  message: string | null
  is_read: boolean
  created_date: string
  created_at: string | null
}

export interface NotificationList {
  items: Notification[]
  total: number
}
