<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

interface PerformanceData {
  stock_id: string
  stock_name: string
  total_score: number
  return_5d: number
  return_10d: number
  return_20d: number
}

interface Props {
  data: PerformanceData[]
  scoreDate: string
}

const props = defineProps<Props>()
const router = useRouter()

const sortKey = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)
const pageSize = 10

const hasPartialNA = computed(() => {
  if (props.data.length === 0) return false
  const all5d = props.data.every(r => r.return_5d == null)
  const all10d = props.data.every(r => r.return_10d == null)
  const all20d = props.data.every(r => r.return_20d == null)
  return (all5d || all10d || all20d) && !(all5d && all10d && all20d)
})

const sortedData = computed(() => {
  if (!sortKey.value) return props.data
  const arr = [...props.data]
  const key = sortKey.value as keyof PerformanceData
  const dir = sortOrder.value === 'asc' ? 1 : -1
  arr.sort((a, b) => {
    const va = a[key] ?? -Infinity
    const vb = b[key] ?? -Infinity
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir
    return String(va).localeCompare(String(vb)) * dir
  })
  return arr
})

const totalPages = computed(() => Math.ceil(sortedData.value.length / pageSize))

const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return sortedData.value.slice(start, start + pageSize)
})

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

function handlePageChange(page: number) {
  currentPage.value = page
}

function formatReturn(val: number): string {
  const sign = val >= 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}

function returnClass(val: number | null): string {
  if (val == null) return 'na'
  return val >= 0 ? 'up' : 'down'
}

function navigateToStock(stockId: string) {
  router.push(`/stock/${stockId}`)
}
</script>

<template>
  <div class="result-table-wrap">
    <div class="table-badge">
      評分日期: <strong>{{ scoreDate }}</strong>
    </div>

    <div v-if="hasPartialNA" class="partial-na-notice">
      部分報酬欄位尚無足夠交易數據，待更多交易日累積後將自動顯示
    </div>

    <div class="table-scroll">
      <table class="stock-table">
        <thead>
          <tr>
            <th>排名</th>
            <th class="sortable-th" @click="toggleSort('stock_id')">
              代碼 <span class="sort-icon">{{ sortIcon('stock_id') }}</span>
            </th>
            <th>股票名稱</th>
            <th class="num sortable-th" @click="toggleSort('total_score')">
              總分 <span class="sort-icon">{{ sortIcon('total_score') }}</span>
            </th>
            <th class="num sortable-th" @click="toggleSort('return_5d')">
              5日報酬 <span class="sort-icon">{{ sortIcon('return_5d') }}</span>
            </th>
            <th class="num sortable-th" @click="toggleSort('return_10d')">
              10日報酬 <span class="sort-icon">{{ sortIcon('return_10d') }}</span>
            </th>
            <th class="num sortable-th" @click="toggleSort('return_20d')">
              20日報酬 <span class="sort-icon">{{ sortIcon('return_20d') }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in pagedData" :key="row.stock_id">
            <td class="rank">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
            <td>
              <span class="stock-code clickable" @click="navigateToStock(row.stock_id)">
                {{ row.stock_id }}
              </span>
            </td>
            <td>{{ row.stock_name }}</td>
            <td class="num">
              <span class="total-score">{{ row.total_score.toFixed(2) }}</span>
            </td>
            <td class="num">
              <span v-if="row.return_5d != null" :class="['return-val', returnClass(row.return_5d)]">
                {{ formatReturn(row.return_5d) }}
              </span>
              <span v-else class="return-val na">N/A</span>
            </td>
            <td class="num">
              <span v-if="row.return_10d != null" :class="['return-val', returnClass(row.return_10d)]">
                {{ formatReturn(row.return_10d) }}
              </span>
              <span v-else class="return-val na">N/A</span>
            </td>
            <td class="num">
              <span v-if="row.return_20d != null" :class="['return-val', returnClass(row.return_20d)]">
                {{ formatReturn(row.return_20d) }}
              </span>
              <span v-else class="return-val na">N/A</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button class="page-btn" :disabled="currentPage === 1" @click="handlePageChange(currentPage - 1)">‹</button>
      <button
        v-for="p in totalPages"
        :key="p"
        :class="['page-btn', { active: p === currentPage }]"
        @click="handlePageChange(p)"
      >{{ p }}</button>
      <button class="page-btn" :disabled="currentPage === totalPages" @click="handlePageChange(currentPage + 1)">›</button>
    </div>
  </div>
</template>

<style scoped>
.table-badge {
  display: inline-block;
  margin-bottom: 14px;
  padding: 6px 14px;
  background: rgba(229, 169, 26, 0.08);
  border: 1px solid rgba(229, 169, 26, 0.2);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  color: var(--amber);
}
.table-badge strong {
  font-family: var(--font-mono);
}

.partial-na-notice {
  margin-bottom: 12px;
  padding: 10px 16px;
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
  border-radius: var(--radius-sm);
  color: #eab308;
  font-size: 0.82rem;
}

.table-scroll {
  overflow-x: auto;
}

.rank {
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-size: 0.82rem;
}

.clickable {
  cursor: pointer;
}
.clickable:hover {
  text-decoration: underline;
}

.return-val {
  font-family: var(--font-mono);
  font-weight: 600;
  font-size: 0.85rem;
}
.return-val.up { color: var(--up); }
.return-val.down { color: var(--down); }
.return-val.na { color: var(--text-muted); }

.sortable-th {
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  transition: color 0.15s;
}
.sortable-th:hover {
  color: var(--amber);
}
.sort-icon {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-left: 2px;
}
.sortable-th:hover .sort-icon {
  color: var(--amber);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  gap: 4px;
  padding: 16px 0 8px;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { border-color: var(--amber); color: var(--amber); }
.page-btn.active { background: var(--amber); color: var(--bg-dark); border-color: var(--amber); font-weight: 700; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
</style>
