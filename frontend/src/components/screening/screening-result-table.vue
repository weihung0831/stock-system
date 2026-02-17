<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { ScoreResult } from '@/types/screening'

interface Props {
  results: ScoreResult[]
}

const props = defineProps<Props>()
const router = useRouter()

const sortKey = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)
const pageSize = 10

const sortedResults = computed(() => {
  if (!sortKey.value) return props.results
  const arr = [...props.results]
  const key = sortKey.value as keyof ScoreResult
  const dir = sortOrder.value === 'asc' ? 1 : -1
  arr.sort((a, b) => {
    const va = a[key] ?? 0
    const vb = b[key] ?? 0
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir
    return String(va).localeCompare(String(vb)) * dir
  })
  return arr
})

const totalPages = computed(() => Math.ceil(sortedResults.value.length / pageSize))

const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return sortedResults.value.slice(start, start + pageSize)
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

const scoreClass = (v: number) => v >= 80 ? 'score-high' : v >= 65 ? 'score-mid' : 'score-low'

const formatChange = (row: ScoreResult) => {
  const pct = row.change_percent ?? 0
  const arrow = pct >= 0 ? '▲' : '▼'
  const sign = pct >= 0 ? '+' : ''
  return `${arrow} ${sign}${pct.toFixed(2)}%`
}

function openStock(row: ScoreResult) {
  router.push(`/stock/${row.stock_id}`)
}
</script>

<template>
  <div class="card">
    <table class="stock-table">
      <thead>
        <tr>
          <th style="width: 50px">#</th>
          <th class="sortable-th" @click="toggleSort('stock_id')">
            代號 <span class="sort-icon">{{ sortIcon('stock_id') }}</span>
          </th>
          <th class="sortable-th" @click="toggleSort('stock_name')">
            名稱 <span class="sort-icon">{{ sortIcon('stock_name') }}</span>
          </th>
          <th class="sortable-th" @click="toggleSort('close_price')">
            收盤價 <span class="sort-icon">{{ sortIcon('close_price') }}</span>
          </th>
          <th class="sortable-th" @click="toggleSort('change_percent')">
            漲跌 <span class="sort-icon">{{ sortIcon('change_percent') }}</span>
          </th>
          <th class="sortable-th" @click="toggleSort('chip_score')">
            籌碼 <span class="sort-icon">{{ sortIcon('chip_score') }}</span>
          </th>
          <th class="sortable-th" @click="toggleSort('fundamental_score')">
            基本面 <span class="sort-icon">{{ sortIcon('fundamental_score') }}</span>
          </th>
          <th class="sortable-th" @click="toggleSort('technical_score')">
            技術面 <span class="sort-icon">{{ sortIcon('technical_score') }}</span>
          </th>
          <th class="sortable-th" @click="toggleSort('total_score')">
            總分 <span class="sort-icon">{{ sortIcon('total_score') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, idx) in pagedResults"
          :key="row.stock_id"
          @click="openStock(row)"
        >
          <td class="rank-num">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
          <td class="stock-code">{{ row.stock_id }}</td>
          <td class="stock-name">{{ row.stock_name }}</td>
          <td style="font-family: var(--font-mono)">${{ row.close_price?.toFixed(2) ?? '-' }}</td>
          <td :class="['price-change', (row.change_percent ?? 0) >= 0 ? 'up' : 'down']" style="font-family: var(--font-mono)">
            {{ formatChange(row) }}
          </td>
          <td><span :class="['score-pill', scoreClass(row.chip_score)]">{{ row.chip_score.toFixed(1) }}</span></td>
          <td><span :class="['score-pill', scoreClass(row.fundamental_score)]">{{ row.fundamental_score.toFixed(1) }}</span></td>
          <td><span :class="['score-pill', scoreClass(row.technical_score)]">{{ row.technical_score.toFixed(1) }}</span></td>
          <td class="total-score">{{ row.total_score.toFixed(1) }}</td>
        </tr>
        <tr v-if="results.length === 0">
          <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 40px">
            尚無資料
          </td>
        </tr>
      </tbody>
    </table>

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
