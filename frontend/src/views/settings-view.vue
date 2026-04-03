<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useScreeningStore } from '@/stores/screening-store'
import { ElMessage } from 'element-plus'
import WeightSliderGroup from '@/components/settings/weight-slider-group.vue'
import SchedulerConfigForm from '@/components/settings/scheduler-config-form.vue'
import { useSettingsStore } from '@/stores/settings-store'
import apiClient from '@/api/client'

const screeningStore = useScreeningStore()
const settingsStore = useSettingsStore()

const handleRunScreening = async () => {
  try {
    await screeningStore.runScreening(settingsStore.threshold)
    ElMessage.success('評分計算已完成')
  } catch {
    ElMessage.error('評分計算失敗')
  }
}

const handleTriggerPipeline = async () => {
  try {
    ElMessage.info('手動觸發 Pipeline...')
    await apiClient.post('/scheduler/trigger')
    ElMessage.success('Pipeline 已觸發，背景執行中')
    setTimeout(fetchLogs, 2000)
  } catch (error: any) {
    const detail = error.response?.data?.detail ?? '觸發失敗，請稍後再試'
    ElMessage.error(detail)
  }
}

// Execution logs
interface PipelineLog {
  id: number
  started_at: string
  finished_at: string | null
  status: string
  steps_completed: number
  total_steps: number
  error: string | null
  trigger_type: string
}

const recentLogs = ref<PipelineLog[]>([])
const logSortKey = ref<string>('')
const logSortOrder = ref<'asc' | 'desc'>('asc')
const logCurrentPage = ref(1)
const logPageSize = 10
let logPollTimer: ReturnType<typeof setInterval> | null = null

const fetchLogs = async () => {
  try {
    const { data } = await apiClient.get('/scheduler/logs', { params: { limit: 100 } })
    recentLogs.value = data.logs ?? []
    // Auto-poll while any log is still running
    const hasRunning = recentLogs.value.some(l => l.status === 'running')
    if (hasRunning && !logPollTimer) {
      logPollTimer = setInterval(fetchLogs, 5000)
    } else if (!hasRunning && logPollTimer) {
      clearInterval(logPollTimer)
      logPollTimer = null
    }
  } catch {
    // Logs are optional
  }
}

const sortedLogs = computed(() => {
  if (!logSortKey.value) return recentLogs.value
  const arr = [...recentLogs.value]
  const key = logSortKey.value as keyof PipelineLog
  const dir = logSortOrder.value === 'asc' ? 1 : -1
  arr.sort((a, b) => {
    const va = a[key] ?? ''
    const vb = b[key] ?? ''
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir
    return String(va).localeCompare(String(vb)) * dir
  })
  return arr
})

const logTotalPages = computed(() => Math.ceil(sortedLogs.value.length / logPageSize))

const pagedLogs = computed(() => {
  const start = (logCurrentPage.value - 1) * logPageSize
  return sortedLogs.value.slice(start, start + logPageSize)
})

function toggleLogSort(key: string) {
  if (logSortKey.value === key) {
    logSortOrder.value = logSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    logSortKey.value = key
    logSortOrder.value = 'desc'
  }
  logCurrentPage.value = 1
}

function logSortIcon(key: string): string {
  if (logSortKey.value !== key) return '⇅'
  return logSortOrder.value === 'asc' ? '↑' : '↓'
}

function handleLogPageChange(page: number) {
  logCurrentPage.value = page
}

const formatDate = (d: string) => new Date(d).toLocaleString('zh-TW')

const formatDuration = (s: string, f: string | null) => {
  if (!f) return '執行中...'
  const sec = Math.round((new Date(f).getTime() - new Date(s).getTime()) / 1000)
  return sec >= 60 ? `${Math.floor(sec / 60)}m ${sec % 60}s` : `${sec}s`
}

const statusText = (s: string) =>
  s === 'success' ? '成功' : s === 'running' ? '執行中' : s === 'skipped' ? '跳過' : '失敗'

const statusClass = (s: string) =>
  s === 'success' ? 'st-ok' : s === 'running' ? 'st-run' : 'st-err'

const handleClearLogs = async () => {
  try {
    await apiClient.delete('/scheduler/logs')
    recentLogs.value = []
    ElMessage.success('執行記錄已清除')
  } catch {
    ElMessage.error('清除失敗')
  }
}

onMounted(() => {
  fetchLogs()
})

onUnmounted(() => {
  if (logPollTimer) {
    clearInterval(logPollTimer)
    logPollTimer = null
  }
})
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系統設定</h2>
      <button
        class="btn-primary"
        :disabled="screeningStore.loading"
        @click="handleRunScreening"
      >
        {{ screeningStore.loading ? '計算中...' : '執行評分計算' }}
      </button>
    </div>
    <div class="settings-grid">
      <div class="settings-card">
        <h3>因子權重配置</h3>
        <WeightSliderGroup />
      </div>

      <div class="settings-card">
        <h3>排程與篩選設定</h3>
        <SchedulerConfigForm @trigger-pipeline="handleTriggerPipeline" />
      </div>
    </div>

    <!-- 族群分類已改用 custom_sectors.json，舊的標籤管理已移除 -->

    <!-- Execution logs card (full width) -->
    <div v-if="recentLogs.length > 0" class="settings-card logs-card">
      <div class="logs-header">
        <h3>最近執行記錄</h3>
        <div class="logs-actions">
          <button class="btn-text" @click="fetchLogs">重新整理</button>
          <button class="btn-text danger" @click="handleClearLogs">清除記錄</button>
        </div>
      </div>
      <div class="logs-scroll">
        <table class="logs-table">
          <thead>
            <tr>
              <th class="sortable-th" @click="toggleLogSort('started_at')">
                執行時間 <span class="sort-icon">{{ logSortIcon('started_at') }}</span>
              </th>
              <th class="sortable-th" @click="toggleLogSort('status')">
                狀態 <span class="sort-icon">{{ logSortIcon('status') }}</span>
              </th>
              <th class="sortable-th" @click="toggleLogSort('steps_completed')">
                步驟 <span class="sort-icon">{{ logSortIcon('steps_completed') }}</span>
              </th>
              <th>耗時</th>
              <th class="sortable-th" @click="toggleLogSort('trigger_type')">
                觸發 <span class="sort-icon">{{ logSortIcon('trigger_type') }}</span>
              </th>
              <th>錯誤</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in pagedLogs" :key="log.id">
              <td class="mono">{{ formatDate(log.started_at) }}</td>
              <td><span class="status-badge" :class="statusClass(log.status)">{{ statusText(log.status) }}</span></td>
              <td class="mono">{{ log.steps_completed }}/{{ log.total_steps }}</td>
              <td class="mono">{{ formatDuration(log.started_at, log.finished_at) }}</td>
              <td>{{ log.trigger_type === 'manual' ? '手動' : '排程' }}</td>
              <td class="error-cell">{{ log.error || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="logTotalPages > 1" class="pagination">
        <button class="page-btn" :disabled="logCurrentPage === 1" @click="handleLogPageChange(logCurrentPage - 1)">‹</button>
        <button
          v-for="p in logTotalPages"
          :key="p"
          :class="['page-btn', { active: p === logCurrentPage }]"
          @click="handleLogPageChange(p)"
        >{{ p }}</button>
        <button class="page-btn" :disabled="logCurrentPage === logTotalPages" @click="handleLogPageChange(logCurrentPage + 1)">›</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  padding: 24px 28px;
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.settings-card {
  background: var(--bg-card, #151d2e);
  border: 1px solid var(--border, #243049);
  border-radius: 10px;
  padding: 28px;
  display: flex;
  flex-direction: column;
}

.settings-card h3 {
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border, #243049);
  color: var(--text, #e8ecf4);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0;
  color: var(--text, #e8ecf4);
}

.btn-primary {
  padding: 10px 24px;
  background: linear-gradient(135deg, #d4960a, #e5a91a);
  border: none;
  border-radius: 6px;
  color: #0e1525;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.2s;
  font-size: 0.88rem;
  font-family: 'Noto Sans TC', system-ui, sans-serif;
}
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 0 20px rgba(240, 185, 41, 0.5); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

/* Logs card */
.logs-card {
  margin-top: 24px;
}

.logs-card h3 {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border, #243049);
}

.btn-text {
  background: none;
  border: none;
  color: var(--text-muted, #556178);
  font-size: 0.8rem;
  cursor: pointer;
  font-family: 'Noto Sans TC', system-ui, sans-serif;
  transition: color 0.15s;
}
.btn-text:hover { color: #e5a91a; }
.btn-text.danger:hover { color: #ef4444; }

.logs-actions {
  display: flex;
  gap: 12px;
}

.logs-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  min-width: 800px;
}

.logs-table thead { background: var(--bg-surface, #1e2a3f); }

.logs-table th {
  padding: 10px 14px;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted, #556178);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border, #243049);
  white-space: nowrap;
}

.logs-table td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border, #243049);
  color: var(--text-secondary, #8c9ab5);
  white-space: nowrap;
}

.logs-table tbody tr:last-child td { border-bottom: none; }
.logs-table tbody tr:hover { background: var(--bg-card-hover, #1a2338); }

.mono { font-family: 'JetBrains Mono', monospace; }

.error-cell {
  color: var(--text-muted, #556178);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}
.st-ok { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
.st-run { background: rgba(234, 179, 8, 0.1); color: #eab308; }
.st-err { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

.sortable-th {
  cursor: pointer;
  user-select: none;
  transition: color 0.15s;
}
.sortable-th:hover {
  color: #e5a91a;
}
.sort-icon {
  font-size: 0.7rem;
  color: var(--text-muted, #556178);
  margin-left: 2px;
}
.sortable-th:hover .sort-icon {
  color: #e5a91a;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  gap: 4px;
  padding: 16px 0 0;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  border: 1px solid var(--border, #243049);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary, #8c9ab5);
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { border-color: #e5a91a; color: #e5a91a; }
.page-btn.active { background: #e5a91a; color: #0e1525; border-color: #e5a91a; font-weight: 700; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* Sector tags */
.tags-card { margin-top: 24px; }

.tag-form {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.tag-input {
  background: var(--bg-surface, #1e2a3f);
  border: 1px solid var(--border, #243049);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--text, #e8ecf4);
  font-size: 0.85rem;
  font-family: 'Noto Sans TC', system-ui, sans-serif;
  outline: none;
  transition: border-color 0.15s;
}
.tag-input:focus { border-color: #e5a91a; }
.tag-sort { width: 70px; }

.tag-color {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border, #243049);
  border-radius: 6px;
  background: none;
  cursor: pointer;
  padding: 2px;
}

.btn-sm { padding: 8px 16px; font-size: 0.82rem; }

.tag-list { display: flex; flex-direction: column; gap: 6px; }

.tag-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--bg-surface, #1e2a3f);
  border-radius: 6px;
  font-size: 0.85rem;
}

.tag-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tag-name { font-weight: 600; color: var(--text, #e8ecf4); min-width: 80px; }
.tag-kw { color: var(--text-muted, #556178); flex: 1; }
.tag-order { color: var(--text-muted, #556178); font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; }
.tag-empty { text-align: center; color: var(--text-muted, #556178); padding: 20px; }

@media (max-width: 1024px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
