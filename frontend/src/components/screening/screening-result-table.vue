<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { ScoreResult } from '@/types/screening'

interface Props {
  results: ScoreResult[]
  reportStockIds?: Set<string>
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

// Show first, last, and nearby pages with ellipsis for compact pagination
const visiblePages = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages: (number | '...')[] = [1]
  const start = Math.max(2, cur - 1)
  const end = Math.min(total - 1, cur + 1)

  if (start > 2) pages.push('...')
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < total - 1) pages.push('...')
  pages.push(total)

  return pages
})

const scoreClass = (v: number) => v >= 69.95 ? 'score-high' : v >= 49.95 ? 'score-mid' : 'score-low'

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
          <th class="sortable-th" @click="toggleSort('total_score')">
            總分 <span class="sort-icon">{{ sortIcon('total_score') }}</span>
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
          <td class="stock-name">
            {{ row.stock_name }}
            <span
              v-if="reportStockIds?.has(row.stock_id)"
              class="ai-report-badge"
              @click.stop="router.push(`/reports?stock=${row.stock_id}`)"
            >AI</span>
          </td>
          <td><span :class="['score-pill', scoreClass(row.total_score)]">{{ row.total_score.toFixed(1) }}</span></td>
          <td style="font-family: var(--font-mono)">${{ row.close_price?.toFixed(2) ?? '-' }}</td>
          <td :class="['price-change', (row.change_percent ?? 0) >= 0 ? 'up' : 'down']" style="font-family: var(--font-mono)">
            {{ formatChange(row) }}
          </td>
          <td><span :class="['score-pill', scoreClass(row.chip_score)]">{{ row.chip_score.toFixed(1) }}</span></td>
          <td><span :class="['score-pill', scoreClass(row.fundamental_score)]">{{ row.fundamental_score.toFixed(1) }}</span></td>
          <td><span :class="['score-pill', scoreClass(row.technical_score)]">{{ row.technical_score.toFixed(1) }}</span></td>
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
      <template v-for="(p, i) in visiblePages" :key="i">
        <span v-if="p === '...'" class="page-ellipsis">…</span>
        <button
          v-else
          :class="['page-btn', { active: p === currentPage }]"
          @click="handlePageChange(p as number)"
        >{{ p }}</button>
      </template>
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
.page-ellipsis { color: var(--text-muted); font-size: 13px; padding: 0 4px; user-select: none; }

.ai-report-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 5px;
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--bg-dark);
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border-radius: 3px;
  cursor: pointer;
  vertical-align: middle;
  transition: box-shadow 0.15s;
}
.ai-report-badge:hover {
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.6);
}
</style>
