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

const totalTriggered = computed(() => items.value.length)
const maxCount = computed(() =>
  items.value.length ? Math.max(...items.value.map(i => i.triggered_count)) : 0,
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
  if (!sortKey.value) return items.value
  const arr = [...items.value]
  const key = sortKey.value as keyof RightSideScreenItem
  const dir = sortOrder.value === 'asc' ? 1 : -1
  arr.sort((a, b) => {
    const va = a[key] ?? ''
    const vb = b[key] ?? ''
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
        <div class="stat-label">功能說明</div>
        <div class="stat-value" style="font-size: 1.2rem">右側買法</div>
        <div class="stat-change">趨勢確認進場訊號</div>
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
        <table class="stock-table">
          <thead>
            <tr>
              <th style="width: 50px">#</th>
              <th class="sortable-th" @click="toggleSort('stock_id')">代號 <span class="sort-icon">{{ sortIcon('stock_id') }}</span></th>
              <th class="sortable-th" @click="toggleSort('stock_name')">名稱 <span class="sort-icon">{{ sortIcon('stock_name') }}</span></th>
              <th class="sortable-th" @click="toggleSort('score')">評分 <span class="sort-icon">{{ sortIcon('score') }}</span></th>
              <th class="sortable-th" @click="toggleSort('triggered_count')">觸發數 <span class="sort-icon">{{ sortIcon('triggered_count') }}</span></th>
              <th>訊號明細</th>
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
              <td class="signal-chips">
                <span
                  v-for="sig in item.signals"
                  :key="sig.id"
                  class="mini-chip"
                  :class="{ on: sig.triggered }"
                  :title="sig.description"
                >
                  {{ sig.label }}
                </span>
              </td>
            </tr>
            <tr v-if="pagedItems.length === 0">
              <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 40px">
                尚無資料
              </td>
            </tr>
          </tbody>
        </table>

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

/* Signal chips (page-specific) */
.signal-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.mini-chip {
  font-size: 0.72rem;
  padding: 2px 8px;
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
}
</style>
