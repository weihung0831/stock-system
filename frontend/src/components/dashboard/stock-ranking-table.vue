<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { ScoreResult } from '@/types/screening'

interface Props {
  results: ScoreResult[]
  reportStockIds?: Set<string>
}

const props = withDefaults(defineProps<Props>(), {
  reportStockIds: () => new Set<string>(),
})
const emit = defineEmits<{
  'stock-hover': [stock: ScoreResult]
}>()
const router = useRouter()

/* Sort state */
const sortKey = ref<string>('rank')
const sortOrder = ref<'asc' | 'desc'>('asc')

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = key === 'rank' ? 'asc' : 'desc'
  }
}

function sortIcon(key: string): string {
  if (sortKey.value !== key) return '⇅'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

const sortedResults = computed(() => {
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

const handleRowClick = (row: ScoreResult) => {
  router.push(`/stock/${row.stock_id}`)
}

const formatPercent = (val: number) => {
  const sign = val >= 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}
</script>

<template>
  <div class="table-scroll">
    <table class="stock-table">
      <thead>
        <tr>
          <th class="sortable" @click="toggleSort('rank')"># <span class="sort-icon">{{ sortIcon('rank') }}</span></th>
          <th class="sortable" @click="toggleSort('stock_id')">代號 <span class="sort-icon">{{ sortIcon('stock_id') }}</span></th>
          <th class="sortable" @click="toggleSort('stock_name')">名稱 <span class="sort-icon">{{ sortIcon('stock_name') }}</span></th>
          <th class="num sortable" @click="toggleSort('close_price')">收盤價 <span class="sort-icon">{{ sortIcon('close_price') }}</span></th>
          <th class="num sortable" @click="toggleSort('change_percent')">漲跌 <span class="sort-icon">{{ sortIcon('change_percent') }}</span></th>
          <th class="num sortable" @click="toggleSort('chip_score')">籌碼 <span class="sort-icon">{{ sortIcon('chip_score') }}</span></th>
          <th class="num sortable" @click="toggleSort('fundamental_score')">基本面 <span class="sort-icon">{{ sortIcon('fundamental_score') }}</span></th>
          <th class="num sortable" @click="toggleSort('technical_score')">技術面 <span class="sort-icon">{{ sortIcon('technical_score') }}</span></th>
          <th class="num sortable" @click="toggleSort('total_score')">總分 <span class="sort-icon">{{ sortIcon('total_score') }}</span></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in sortedResults"
          :key="row.stock_id"
          class="clickable-row"
          @click="handleRowClick(row)"
          @mouseenter="emit('stock-hover', row)"
        >
          <td class="rank-cell">{{ row.rank }}</td>
          <td>
            <span class="stock-code">{{ row.stock_id }}</span>
          </td>
          <td>
            <span>{{ row.stock_name }}</span>
            <span
              v-if="reportStockIds.has(row.stock_id)"
              class="ai-badge"
              title="已有 AI 分析報告"
              @click.stop="router.push(`/reports?stock=${row.stock_id}`)"
            >AI</span>
          </td>
          <td class="num">${{ row.close_price.toFixed(2) }}</td>
          <td class="num">
            <span :class="['price-change', row.change_percent >= 0 ? 'up' : 'down']">
              {{ row.change_percent >= 0 ? '▲' : '▼' }} {{ formatPercent(row.change_percent) }}
            </span>
          </td>
          <td class="num"><span class="score-pill chip">{{ row.chip_score.toFixed(1) }}</span></td>
          <td class="num"><span class="score-pill fundamental">{{ row.fundamental_score.toFixed(1) }}</span></td>
          <td class="num"><span class="score-pill technical">{{ row.technical_score.toFixed(1) }}</span></td>
          <td class="num"><span class="total-score">{{ row.total_score.toFixed(1) }}</span></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-scroll {
  overflow-x: auto;
}

.sortable {
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}
.sortable:hover {
  color: var(--amber);
}

.sort-icon {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-left: 2px;
}
.sortable:hover .sort-icon {
  color: var(--amber);
}

.clickable-row {
  cursor: pointer;
}
.clickable-row:hover td {
  background: rgba(229, 169, 26, 0.06);
}

.rank-cell {
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-size: 0.82rem;
}

.ai-badge {
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
  line-height: 1.4;
  transition: box-shadow 0.15s;
}
.ai-badge:hover {
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.6);
}
</style>
