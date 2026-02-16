<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

defineProps<{
  sidebarVisible: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/screening': '自訂篩選',
  '/chip-stats': '籌碼統計',
  '/reports': 'AI 報告',
  '/history': '歷史回測',
  '/settings': '系統設定',
}

const pageTitle = computed(() => {
  const path = route.path
  if (path.startsWith('/stock/')) return '個股詳情'
  return pageTitles[path] ?? ''
})
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <button class="mobile-menu-btn" @click="emit('toggle-sidebar')">
        <svg v-if="!sidebarVisible" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
      <div class="header-title">{{ pageTitle }}</div>
    </div>
    <div class="header-meta">
      <div class="status-dot" />
      <span class="meta-text">系統運行中</span>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 28px;
  background: var(--bg-dark, #0e1525);
  border-bottom: 1px solid var(--border, #243049);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mobile-menu-btn {
  display: none;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  cursor: pointer;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
}

.mobile-menu-btn:hover {
  border-color: var(--amber);
  color: var(--amber);
}

.header-title {
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text, #e8ecf4);
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  animation: blink 2s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.meta-text {
  font-size: 0.8rem;
  color: var(--text-secondary, #8c9ab5);
  font-family: 'JetBrains Mono', monospace;
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }

  .app-header {
    padding: 0 16px;
  }

  .header-title {
    font-size: 1rem;
  }
}
</style>
