<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useNotificationStore } from '@/stores/notification-store'

const store = useNotificationStore()
const open = ref(false)
const bellRef = ref<HTMLDivElement>()

function toggle() {
  open.value = !open.value
  if (open.value) {
    store.fetchNotifications()
  }
}

function handleClickOutside(e: MouseEvent) {
  if (bellRef.value && !bellRef.value.contains(e.target as Node)) {
    open.value = false
  }
}

function formatTime(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '剛剛'
  if (mins < 60) return `${mins} 分鐘前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小時前`
  return d.toLocaleDateString('zh-TW')
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <div ref="bellRef" class="notification-bell">
    <button class="bell-btn" @click.stop="toggle">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
      <span v-if="store.unreadCount > 0" class="badge">
        {{ store.unreadCount > 99 ? '99+' : store.unreadCount }}
      </span>
    </button>

    <Transition name="dropdown">
      <div v-if="open" class="dropdown">
        <div class="dropdown-header">
          <span class="dropdown-title">通知</span>
          <button
            v-if="store.unreadCount > 0"
            class="mark-all-btn"
            @click="store.markAllRead()"
          >
            全部已讀
          </button>
        </div>
        <div class="dropdown-body">
          <div
            v-if="store.notifications.length === 0"
            class="empty-state"
          >
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.3">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <div style="margin-top:8px">暫無通知</div>
          </div>
          <div
            v-for="n in store.notifications"
            :key="n.id"
            class="notification-item"
            :class="{ unread: !n.is_read }"
            @click="store.markRead(n.id)"
          >
            <div class="notification-row">
              <div class="notification-icon">
                <span v-if="n.type === 'target_reached'">🎯</span>
                <span v-else>🔔</span>
              </div>
              <div class="notification-content">
                <div class="notification-title">{{ n.title }}</div>
                <div v-if="n.message" class="notification-msg">{{ n.message }}</div>
                <div class="notification-time">{{ formatTime(n.created_at) }}</div>
              </div>
              <div v-if="!n.is_read" class="unread-dot" />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.notification-bell {
  position: relative;
  display: inline-flex;
}

.bell-btn {
  position: relative;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary, #8c9ab5);
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.bell-btn:hover {
  color: var(--amber, #f59e0b);
  border-color: var(--border, #243049);
  background: rgba(245, 158, 11, 0.06);
}

.badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 17px;
  height: 17px;
  padding: 0 5px;
  border-radius: 9px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  box-shadow: 0 0 0 2px var(--bg-dark, #0e1525);
}

.dropdown {
  position: absolute;
  top: calc(100% + 10px);
  right: -8px;
  width: 360px;
  max-height: 440px;
  background: var(--bg-card, #1a1f2e);
  border: 1px solid var(--border, #243049);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,255,255,0.03);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dropdown-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px 12px;
  border-bottom: 1px solid var(--border, #243049);
}

.dropdown-title {
  font-weight: 700;
  color: var(--text, #e8ecf4);
  font-size: 15px;
  letter-spacing: -0.01em;
}

.mark-all-btn {
  background: none;
  border: 1px solid rgba(245, 158, 11, 0.2);
  color: var(--amber, #f59e0b);
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 6px;
  transition: all 0.15s;
}

.mark-all-btn:hover {
  background: rgba(245, 158, 11, 0.08);
  border-color: var(--amber, #f59e0b);
}

.dropdown-body {
  overflow-y: auto;
  flex: 1;
}

.empty-state {
  padding: 36px 16px;
  text-align: center;
  color: var(--text-secondary, #8c9ab5);
  font-size: 13px;
}

.notification-item {
  padding: 12px 18px;
  border-bottom: 1px solid rgba(36, 48, 73, 0.5);
  cursor: pointer;
  transition: background 0.15s;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.notification-item.unread {
  background: rgba(245, 158, 11, 0.04);
}

.notification-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.notification-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text, #e8ecf4);
  margin-bottom: 3px;
  line-height: 1.3;
}

.notification-msg {
  font-size: 12px;
  color: var(--text-secondary, #8c9ab5);
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-time {
  font-size: 11px;
  color: var(--text-muted, #5a6a87);
  font-family: 'JetBrains Mono', monospace;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--amber, #f59e0b);
  flex-shrink: 0;
  margin-top: 4px;
}
</style>
