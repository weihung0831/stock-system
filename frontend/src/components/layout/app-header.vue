<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

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
    <div class="header-title">{{ pageTitle }}</div>
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
</style>
