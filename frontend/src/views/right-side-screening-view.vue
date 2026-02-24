<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { screenRightSideSignals } from '@/api/right-side-signals-api'
import type { RightSideScreenItem } from '@/types/right-side-signals'

const router = useRouter()
const loading = ref(false)
const items = ref<RightSideScreenItem[]>([])
const minSignals = ref(2)
const errorMsg = ref('')

/* Extra filter toggles */
const filterBreakout = ref(false)
const filterWeeklyUp = ref(false)
const filterStrongRec = ref(false)
const filterRisk = ref<'' | 'low' | 'medium' | 'high'>('')
const filterAction = ref<'' | 'buy' | 'hold' | 'avoid'>('')

const filteredItems = computed(() => {
  let list = items.value
  if (filterBreakout.value) list = list.filter(i => i.today_breakout)
  if (filterWeeklyUp.value) list = list.filter(i => i.weekly_trend_up)
  if (filterStrongRec.value) list = list.filter(i => i.strong_recommend)
  if (filterRisk.value) list = list.filter(i => i.risk_level === filterRisk.value)
  if (filterAction.value) list = list.filter(i => i.prediction?.action === filterAction.value)
  return list
})

const totalTriggered = computed(() => filteredItems.value.length)
const maxCount = computed(() =>
  filteredItems.value.length ? Math.max(...filteredItems.value.map(i => i.triggered_count)) : 0,
)

/* Sort */
const sortKey = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('asc')

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'desc'
  }
  currentPage.value = 1
}

function sortIcon(key: string): string {
  if (sortKey.value !== key) return '⇅'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

const sortedItems = computed(() => {
  if (!sortKey.value) return filteredItems.value
  const arr = [...filteredItems.value]
  const dir = sortOrder.value === 'asc' ? 1 : -1
  arr.sort((a, b) => {
    let va: any, vb: any
    if (sortKey.value === 'prediction.risk_reward') {
      va = a.prediction?.risk_reward ?? -1
      vb = b.prediction?.risk_reward ?? -1
    } else {
      const key = sortKey.value as keyof RightSideScreenItem
      va = a[key] ?? ''
      vb = b[key] ?? ''
    }
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir
    return String(va).localeCompare(String(vb)) * dir
  })
  return arr
})

/* Pagination */
const currentPage = ref(1)
const pageSize = 10
const totalPages = computed(() => Math.ceil(sortedItems.value.length / pageSize))
const pagedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return sortedItems.value.slice(start, start + pageSize)
})

async function doScreen() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await screenRightSideSignals(minSignals.value)
    items.value = res.items
    currentPage.value = 1
  } catch (e: any) {
    errorMsg.value = e.response?.data?.detail || '篩選失敗'
    items.value = []
  } finally {
    loading.value = false
  }
}

const scoreClass = (s: number) => s >= 60 ? 'score-high' : s >= 35 ? 'score-mid' : 'score-low'

// Load on mount
doScreen()
</script>

<template>
  <div class="page" style="animation: fadeIn 0.3s ease">
    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">符合條件</div>
        <div class="stat-value">{{ totalTriggered }}</div>
        <div class="stat-change up">檔股票</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最高觸發數</div>
        <div class="stat-value" style="color: var(--amber)">{{ maxCount }}</div>
        <div class="stat-change up">/ 6 個訊號</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最低門檻</div>
        <div class="stat-value" style="color: var(--up)">{{ minSignals }}</div>
        <div class="stat-change">個訊號以上</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">強力推薦</div>
        <div class="stat-value" style="color: var(--up)">{{ filteredItems.filter(i => i.strong_recommend).length }}</div>
        <div class="stat-change up">檔股票</div>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <label class="filter-label">
        最少觸發訊號數：
        <select v-model.number="minSignals" class="filter-select" @change="doScreen">
          <option :value="1">1</option>
          <option :value="2">2</option>
          <option :value="3">3</option>
          <option :value="4">4</option>
          <option :value="5">5</option>
          <option :value="6">6</option>
        </select>
      </label>
      <button class="btn-screen" :disabled="loading" @click="doScreen">
        {{ loading ? '篩選中...' : '重新篩選' }}
      </button>
    </div>

    <!-- Condition filters -->
    <div class="filter-groups">
      <div class="filter-group">
        <span class="filter-group-label">條件</span>
        <button :class="['tag-toggle', { active: filterBreakout }]" @click="filterBreakout = !filterBreakout; currentPage = 1">今日突破</button>
        <button :class="['tag-toggle', { active: filterWeeklyUp }]" @click="filterWeeklyUp = !filterWeeklyUp; currentPage = 1">週趨勢向上</button>
        <button :class="['tag-toggle strong', { active: filterStrongRec }]" @click="filterStrongRec = !filterStrongRec; currentPage = 1">強力推薦</button>
      </div>
      <div class="filter-group">
        <span class="filter-group-label">風險</span>
        <button :class="['tag-toggle risk-low', { active: filterRisk === 'low' }]" @click="filterRisk = filterRisk === 'low' ? '' : 'low'; currentPage = 1">低</button>
        <button :class="['tag-toggle risk-med', { active: filterRisk === 'medium' }]" @click="filterRisk = filterRisk === 'medium' ? '' : 'medium'; currentPage = 1">中</button>
        <button :class="['tag-toggle risk-high', { active: filterRisk === 'high' }]" @click="filterRisk = filterRisk === 'high' ? '' : 'high'; currentPage = 1">高</button>
      </div>
      <div class="filter-group">
        <span class="filter-group-label">操作</span>
        <button :class="['tag-toggle buy', { active: filterAction === 'buy' }]" @click="filterAction = filterAction === 'buy' ? '' : 'buy'; currentPage = 1">買入</button>
        <button :class="['tag-toggle hold', { active: filterAction === 'hold' }]" @click="filterAction = filterAction === 'hold' ? '' : 'hold'; currentPage = 1">觀望</button>
        <button :class="['tag-toggle avoid', { active: filterAction === 'avoid' }]" @click="filterAction = filterAction === 'avoid' ? '' : 'avoid'; currentPage = 1">不建議</button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="error-bar">{{ errorMsg }}</div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <span>篩選中...</span>
    </div>

    <!-- Results table -->
    <template v-else-if="items.length > 0">
      <div class="section-header">
        <div class="section-title">
          篩選結果
          <span class="badge">共 {{ items.length }} 檔</span>
        </div>
      </div>

      <div class="card" style="margin-bottom: 20px">
        <div class="table-scroll-wrapper">
        <table class="stock-table right-side-table">
          <thead>
            <tr>
              <th class="col-rank">#</th>
              <th class="col-code sortable-th" @click="toggleSort('stock_id')">代號 <span class="sort-icon">{{ sortIcon('stock_id') }}</span></th>
              <th class="col-name sortable-th" @click="toggleSort('stock_name')">名稱 <span class="sort-icon">{{ sortIcon('stock_name') }}</span></th>
              <th class="col-score sortable-th" @click="toggleSort('score')">評分 <span class="sort-icon">{{ sortIcon('score') }}</span></th>
              <th class="col-count sortable-th" @click="toggleSort('triggered_count')">觸發數 <span class="sort-icon">{{ sortIcon('triggered_count') }}</span></th>
              <th class="col-tags">條件標籤</th>
              <th class="col-action">操作</th>
              <th class="col-rr sortable-th" @click="toggleSort('prediction.risk_reward')">報酬比 <span class="sort-icon">{{ sortIcon('prediction.risk_reward') }}</span></th>
              <th class="col-signals">訊號明細</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, idx) in pagedItems"
              :key="item.stock_id"
              @click="router.push(`/stock/${item.stock_id}`)"
            >
              <td class="rank-num">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
              <td class="stock-code">{{ item.stock_id }}</td>
              <td class="stock-name">{{ item.stock_name }}</td>
              <td>
                <span :class="['score-pill', scoreClass(item.score)]">{{ item.score }}</span>
              </td>
              <td>{{ item.triggered_count }} / 6</td>
              <td>
                <div class="tag-chips-cell">
                  <span v-if="item.today_breakout" class="cond-tag breakout">突破</span>
                  <span v-if="item.weekly_trend_up" class="cond-tag trend-up">週漲</span>
                  <span v-if="item.strong_recommend" class="cond-tag strong-rec">強推</span>
                  <span :class="['cond-tag', `risk-${item.risk_level}`]">
                    {{ item.risk_level === 'low' ? '低風險' : item.risk_level === 'medium' ? '中風險' : '高風險' }}
                  </span>
                </div>
              </td>
              <td>
                <span v-if="item.prediction" :class="['action-pill', `action-${item.prediction.action}`]">
                  {{ item.prediction.action_label }}
                </span>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <span v-if="item.prediction" class="rr-value">{{ item.prediction.risk_reward.toFixed(1) }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <div class="signal-chips">
                  <span
                    v-for="sig in item.signals"
                    :key="sig.id"
                    class="mini-chip"
                    :class="{ on: sig.triggered }"
                    :title="sig.description"
                  >
                    {{ sig.label }}
                  </span>
                </div>
              </td>
            </tr>
            <tr v-if="pagedItems.length === 0">
              <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 40px">
                尚無資料
              </td>
            </tr>
          </tbody>
        </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination">
          <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">‹</button>
          <button
            v-for="p in totalPages"
            :key="p"
            :class="['page-btn', { active: p === currentPage }]"
            @click="currentPage = p"
          >{{ p }}</button>
          <button class="page-btn" :disabled="currentPage === totalPages" @click="currentPage++">›</button>
        </div>
      </div>
    </template>

    <!-- Empty -->
    <div v-else-if="!loading && !errorMsg" class="empty-state">
      <p>目前無符合條件的股票</p>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 24px 28px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 0.88rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-select {
  padding: 6px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-size: 0.88rem;
}

.btn-screen {
  padding: 7px 18px;
  background: linear-gradient(135deg, var(--amber-dim), var(--amber));
  border: none;
  border-radius: var(--radius-sm);
  color: var(--bg-dark);
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: transform 0.15s, box-shadow 0.2s;
}

.btn-screen:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.btn-screen:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-bar {
  margin: 16px 0;
  padding: 12px 16px;
  background: var(--down-bg);
  border: 1px solid var(--down);
  border-radius: var(--radius-sm);
  color: var(--down);
  font-size: 0.88rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--text-muted);
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Pagination (matches dashboard) */
.pagination {
  display: flex;
  justify-content: center;
  gap: 4px;
  padding: 16px 0 8px;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  border: 1px solid var(--border, #243049);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary, #8c9ab5);
  font-family: var(--font-mono);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { border-color: var(--amber, #e5a91a); color: var(--amber, #e5a91a); }
.page-btn.active { background: var(--amber, #e5a91a); color: var(--bg-dark, #0e1525); border-color: var(--amber, #e5a91a); font-weight: 700; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* Horizontal scroll on small screens */
.table-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* Right-side table: fixed layout, full width */
.right-side-table {
  table-layout: fixed;
  width: 100%;
}

.col-rank { width: 3%; }
.col-code { width: 6%; }
.col-name { width: 9%; }
.col-score { width: 5%; }
.col-count { width: 5%; }
.col-tags { width: 16%; }
.col-action { width: 6%; }
.col-rr { width: 6%; }
.col-signals { width: 44%; }

/* Action pill */
.action-pill {
  font-size: 0.75rem;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
  white-space: nowrap;
}
.action-buy { background: rgba(34, 197, 94, 0.12); color: var(--up); border: 1px solid rgba(34, 197, 94, 0.25); }
.action-hold { background: rgba(251, 191, 36, 0.12); color: var(--amber); border: 1px solid rgba(251, 191, 36, 0.25); }
.action-avoid { background: rgba(239, 68, 68, 0.12); color: var(--down); border: 1px solid rgba(239, 68, 68, 0.25); }

.rr-value {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--text);
}

.text-muted {
  color: var(--text-muted);
  font-size: 0.82rem;
}

/* Signal chips (page-specific) */
.signal-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.signal-chips .mini-chip {
  flex: 1 1 auto;
  text-align: center;
}

.mini-chip {
  font-size: 0.72rem;
  padding: 2px 6px;
  border-radius: 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-muted);
  white-space: nowrap;
}

.mini-chip.on {
  border-color: var(--up);
  color: var(--up);
  background: rgba(34, 197, 94, 0.08);
}


.filter-groups {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
  margin-bottom: 20px;
  align-items: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 600;
  min-width: 28px;
}

.tag-toggle {
  padding: 5px 14px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: all 0.15s;
}

.tag-toggle:hover {
  border-color: var(--amber);
  color: var(--amber);
}

.tag-toggle.active {
  background: rgba(229, 169, 26, 0.15);
  border-color: var(--amber);
  color: var(--amber);
  font-weight: 700;
}

.tag-toggle.strong.active {
  background: rgba(34, 197, 94, 0.15);
  border-color: var(--up);
  color: var(--up);
}

.tag-toggle.risk-low.active {
  background: rgba(34, 197, 94, 0.15);
  border-color: var(--up);
  color: var(--up);
}

.tag-toggle.risk-med.active {
  background: rgba(251, 191, 36, 0.15);
  border-color: var(--amber);
  color: var(--amber);
}

.tag-toggle.risk-high.active {
  background: rgba(239, 68, 68, 0.15);
  border-color: var(--down);
  color: var(--down);
}

.tag-toggle.buy.active {
  background: rgba(34, 197, 94, 0.15);
  border-color: var(--up);
  color: var(--up);
}

.tag-toggle.hold.active {
  background: rgba(251, 191, 36, 0.15);
  border-color: var(--amber);
  color: var(--amber);
}

.tag-toggle.avoid.active {
  background: rgba(239, 68, 68, 0.15);
  border-color: var(--down);
  color: var(--down);
}

/* Tag chips cell */
.tag-chips-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  white-space: normal;
}

.cond-tag {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
  white-space: nowrap;
}

.cond-tag.breakout {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.cond-tag.trend-up {
  background: rgba(34, 197, 94, 0.1);
  color: var(--up);
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.cond-tag.strong-rec {
  background: rgba(251, 191, 36, 0.15);
  color: var(--amber);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.cond-tag.risk-low {
  background: rgba(34, 197, 94, 0.1);
  color: var(--up);
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.cond-tag.risk-medium {
  background: rgba(251, 191, 36, 0.1);
  color: var(--amber);
  border: 1px solid rgba(251, 191, 36, 0.25);
}

.cond-tag.risk-high {
  background: rgba(239, 68, 68, 0.1);
  color: var(--down);
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
  font-size: 0.92rem;
}

@media (max-width: 768px) {
  .page {
    padding: 16px;
  }

  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-screen {
    width: 100%;
    padding: 10px;
  }

  .pagination {
    gap: 6px;
    padding: 12px 0 6px;
  }

  .page-btn {
    min-width: 40px;
    height: 40px;
    font-size: 15px;
  }

  .page-btn.active {
    font-size: 16px;
    font-weight: 900;
    color: #0e1525 !important;
  }

  .right-side-table {
    table-layout: auto;
    width: auto;
    min-width: 0;
  }

  .col-rank,
  .col-code,
  .col-name,
  .col-score,
  .col-count,
  .col-tags,
  .col-action,
  .col-rr,
  .col-signals {
    width: auto;
  }

  .signal-chips {
    flex-wrap: nowrap;
  }

  .tag-chips-cell {
    flex-wrap: nowrap;
  }
}
</style>
