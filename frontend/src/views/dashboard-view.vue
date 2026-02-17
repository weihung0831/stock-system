<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScreeningStore } from '@/stores/screening-store'
import { useSectorTagsStore } from '@/stores/sector-tags-store'
import { getLatestReports } from '@/api/reports-api'
import type { ScoreResult } from '@/types/screening'

const router = useRouter()
const screeningStore = useScreeningStore()
const sectorTagsStore = useSectorTagsStore()
const reportStockIds = ref<Set<string>>(new Set())
const activeSector = ref('all')

/* ========== Sector filtering ========== */
const sectorFiltered = computed(() => {
  if (activeSector.value === 'all') return screeningStore.results
  const tag = sectorTagsStore.tags.find(t => t.name === activeSector.value)
  const keyword = tag?.keywords || activeSector.value
  return screeningStore.results.filter(r => r.industry?.includes(keyword))
})

/* ========== Pagination ========== */
const currentPage = ref(1)
const pageSize = 10
const topN = 30

const top30 = computed(() => {
  const sliced = sectorFiltered.value.slice(0, topN)
  if (!sortKey.value) return sliced
  const arr = [...sliced]
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
const totalPages = computed(() => Math.ceil(top30.value.length / pageSize))

const filteredResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return top30.value.slice(start, start + pageSize)
})

const handlePageChange = (page: number) => {
  currentPage.value = page
}

/* ========== Stat cards ========== */
const statCards = computed(() => {
  const results = top30.value
  const top = results[0]
  const highChip = results.filter(r => r.chip_score >= 60).length
  return [
    {
      label: '分析股票數',
      value: results.length.toLocaleString(),
      change: '全市場覆蓋',
      changeClass: 'up',
    },
    {
      label: '今日最高分',
      value: top ? top.total_score.toFixed(1) : '-',
      change: top ? `${top.stock_id} ${top.stock_name}` : '',
      changeClass: 'up',
      valueStyle: 'color: var(--amber)',
    },
    {
      label: '高籌碼分數',
      value: highChip.toString(),
      change: '籌碼分 ≥ 60',
      changeClass: 'up',
      valueStyle: 'color: var(--up)',
    },
    {
      label: '資料日期',
      value: screeningStore.latestDate || '-',
      change: screeningStore.updatedAt ? `更新於 ${screeningStore.updatedAt}` : '',
      changeClass: '',
      valueStyle: 'font-size: 1.2rem',
    },
  ]
})

/* ========== Category tabs ========== */
const categoryTabs = computed(() => {
  // For "all" tab: show count from top30 (limited by topN)
  const all = { key: 'all', label: '全部', color: '', count: Math.min(screeningStore.results.length, topN) }

  // For sector tabs: show count of stocks in that sector (also limited by topN)
  const tagTabs = sectorTagsStore.tags.map(tag => {
    const keyword = tag.keywords || tag.name
    const sectorCount = screeningStore.results.filter(r => r.industry?.includes(keyword)).length
    return {
      key: tag.name,
      label: tag.name,
      color: tag.color,
      count: Math.min(sectorCount, topN),
    }
  })
  return [all, ...tagTabs]
})

/* ========== Sort ========== */
const sortKey = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('asc')

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'desc'
  }
}

function sortIcon(key: string): string {
  if (sortKey.value !== key) return '⇅'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

/* ========== Score class helpers ========== */
const scoreClass = (v: number) => v >= 80 ? 'score-high' : v >= 65 ? 'score-mid' : 'score-low'
const rankClass = (i: number) => i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : i === 2 ? 'rank-3' : ''

const formatChange = (row: ScoreResult) => {
  const pct = row.change_percent
  const arrow = pct >= 0 ? '▲' : '▼'
  const sign = pct >= 0 ? '+' : ''
  return `${arrow} ${sign}${pct.toFixed(2)}%`
}

/* ========== Navigation ========== */
const openStock = (row: ScoreResult) => {
  router.push(`/stock/${row.stock_id}`)
}

/* ========== Init ========== */
onMounted(async () => {
  const [, reports] = await Promise.all([
    screeningStore.fetchResults(),
    getLatestReports().catch(() => []),
  ])
  reportStockIds.value = new Set(reports.map(r => r.stock_id))
  sectorTagsStore.fetchTags()
})
</script>

<template>
  <div class="dashboard-page" style="animation: fadeIn 0.3s ease">
    <!-- Stat cards -->
    <div class="stat-grid">
      <div v-for="(card, i) in statCards" :key="i" class="stat-card">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value" :style="card.valueStyle">{{ card.value }}</div>
        <div :class="['stat-change', card.changeClass]">{{ card.change }}</div>
      </div>
    </div>

    <!-- Section header: title + category tabs -->
    <div class="section-header">
      <div class="section-title" style="margin-bottom: 0">
        每日精選排行
        <span class="badge">TOP {{ top30.length }}</span>
      </div>

      <!-- Desktop: tabs -->
      <div class="category-tabs desktop-only">
        <div
          v-for="tab in categoryTabs"
          :key="tab.key"
          :class="['cat-tab', { active: activeSector === tab.key }]"
          @click="activeSector = tab.key; currentPage = 1"
        >
          <span v-if="tab.color" class="cat-dot" :style="{ background: tab.color }" />
          {{ tab.label }}
          <span class="cat-count">{{ tab.count }}</span>
        </div>
      </div>

      <!-- Mobile: dropdown -->
      <select
        v-model="activeSector"
        class="category-select mobile-only"
        @change="currentPage = 1"
      >
        <option
          v-for="tab in categoryTabs"
          :key="tab.key"
          :value="tab.key"
        >
          {{ tab.label }} ({{ tab.count }})
        </option>
      </select>
    </div>

    <!-- Stock ranking table -->
    <div class="card" style="margin-bottom: 20px">
      <table class="stock-table">
        <thead>
          <tr>
            <th style="width: 50px">#</th>
            <th class="sortable-th" @click="toggleSort('stock_id')">代號 <span class="sort-icon">{{ sortIcon('stock_id') }}</span></th>
            <th class="sortable-th" @click="toggleSort('stock_name')">名稱 <span class="sort-icon">{{ sortIcon('stock_name') }}</span></th>
            <th class="sortable-th" @click="toggleSort('close_price')">收盤價 <span class="sort-icon">{{ sortIcon('close_price') }}</span></th>
            <th class="sortable-th" @click="toggleSort('change_percent')">漲跌 <span class="sort-icon">{{ sortIcon('change_percent') }}</span></th>
            <th class="sortable-th" @click="toggleSort('chip_score')">籌碼 <span class="sort-icon">{{ sortIcon('chip_score') }}</span></th>
            <th class="sortable-th" @click="toggleSort('fundamental_score')">基本面 <span class="sort-icon">{{ sortIcon('fundamental_score') }}</span></th>
            <th class="sortable-th" @click="toggleSort('technical_score')">技術面 <span class="sort-icon">{{ sortIcon('technical_score') }}</span></th>
            <th class="sortable-th" @click="toggleSort('total_score')">總分 <span class="sort-icon">{{ sortIcon('total_score') }}</span></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in filteredResults"
            :key="row.stock_id"
            @click="openStock(row)"
          >
            <td :class="['rank-num', rankClass((currentPage - 1) * pageSize + idx)]">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
            <td class="stock-code">{{ row.stock_id }}</td>
            <td class="stock-name">
              {{ row.stock_name }}
              <span
                v-if="reportStockIds.has(row.stock_id)"
                class="ai-report-badge"
                @click.stop="router.push(`/reports?stock=${row.stock_id}`)"
              >AI</span>
            </td>
            <td style="font-family: var(--font-mono)">${{ row.close_price?.toFixed(2) ?? '-' }}</td>
            <td :class="['price-change', row.change_percent >= 0 ? 'up' : 'down']" style="font-family: var(--font-mono)">
              {{ formatChange(row) }}
            </td>
            <td><span :class="['score-pill', scoreClass(row.chip_score)]">{{ row.chip_score.toFixed(1) }}</span></td>
            <td><span :class="['score-pill', scoreClass(row.fundamental_score)]">{{ row.fundamental_score.toFixed(1) }}</span></td>
            <td><span :class="['score-pill', scoreClass(row.technical_score)]">{{ row.technical_score.toFixed(1) }}</span></td>
            <td class="total-score">{{ row.total_score.toFixed(1) }}</td>
          </tr>
          <tr v-if="filteredResults.length === 0">
            <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 40px">
              {{ screeningStore.loading ? '載入中...' : '尚無資料' }}
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

  </div>
</template>

<style scoped>
.dashboard-page {
  padding: 24px 28px;
}

/* Desktop/Mobile toggle */
.desktop-only {
  display: flex;
}

.mobile-only {
  display: none;
}

/* Category select dropdown */
.category-select {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 14px;
  font-family: var(--font-sans);
  font-weight: 600;
  cursor: pointer;
  outline: none;
  transition: all 0.2s;
}

.category-select:hover {
  border-color: var(--border-light);
}

.category-select:focus {
  border-color: var(--amber);
  box-shadow: 0 0 0 2px rgba(229, 169, 26, 0.1);
}

@media (max-width: 768px) {
  .dashboard-page {
    padding: 16px 16px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .section-title {
    font-size: 0.95rem;
  }

  /* Hide desktop tabs, show mobile select */
  .desktop-only {
    display: none !important;
  }

  .mobile-only {
    display: block;
  }

  .category-select {
    margin-top: 8px;
  }

  /* Pagination adjustments for mobile */
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

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
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
