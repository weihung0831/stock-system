<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScreeningStore } from '@/stores/screening-store'
import { getLatestReports } from '@/api/reports-api'
import type { ScoreResult } from '@/types/screening'

const router = useRouter()
const screeningStore = useScreeningStore()
const reportStockIds = ref<Set<string>>(new Set())
const activeClassification = ref('all')
const activeSector = ref('all')

/* ========== Market status ========== */
const marketStatus = computed(() => screeningStore.marketStatus || null)
const topSectors = computed(() => screeningStore.topSectors)

const isDowntrend = computed(() => marketStatus.value === 'DOWNTREND')

/* ========== Classification filter ========== */
const classificationTabs = computed(() => {
  // 從族群精選中收集所有不重複股票來計算 tabs 數量
  const seen = new Set<string>()
  const results: ScoreResult[] = []
  for (const g of sectorGroups.value) {
    for (const s of g.stocks) {
      if (!seen.has(s.stock_id)) {
        seen.add(s.stock_id)
        results.push(s)
      }
    }
  }
  const all = results.length
  const buy = results.filter(r => r.classification === 'BUY').length
  const watch = results.filter(r => r.classification === 'WATCH').length
  const early = results.filter(r => r.classification === 'EARLY').length
  return [
    { key: 'all', label: '全部', count: all },
    { key: 'BUY', label: '買進', count: buy },
    { key: 'WATCH', label: '觀察', count: watch },
    { key: 'EARLY', label: '初期', count: early },
  ]
})

const sectorList = computed(() => {
  const set = new Set<string>()
  for (const r of screeningStore.results) {
    if (r.sector_name) set.add(r.sector_name)
  }
  return Array.from(set).sort()
})

const classFiltered = computed(() => {
  if (isDowntrend.value) return []
  let list = screeningStore.results
  if (activeClassification.value !== 'all') {
    list = list.filter(r => r.classification === activeClassification.value)
  }
  if (activeSector.value !== 'all') {
    list = list.filter(r => r.sector_name === activeSector.value)
  }
  return list.sort((a, b) => b.momentum_score - a.momentum_score)
})

/* ========== Sector grouping (ordered by backend top_sectors) ========== */
const sectorGroups = computed(() => {
  const map = new Map<string, ScoreResult[]>()
  for (const r of classFiltered.value) {
    const sector = r.sector_name || '其他'
    if (!map.has(sector)) map.set(sector, [])
    map.get(sector)!.push(r)
  }
  // Sort each group by momentum_score desc, take top 6
  for (const stocks of map.values()) {
    stocks.sort((a, b) => b.momentum_score - a.momentum_score)
  }

  const groups: { name: string; returnPct: number; stocks: ScoreResult[] }[] = []

  // Try backend top_sectors order first (ranked by 20d sector return)
  const sectorOrder = topSectors.value.map(s => s.name)
  if (sectorOrder.length > 0) {
    for (const sectorName of sectorOrder) {
      const stocks = map.get(sectorName)
      if (stocks && stocks.length > 0) {
        const ts = topSectors.value.find(s => s.name === sectorName)
        groups.push({ name: sectorName, returnPct: ts?.return_pct ?? 0, stocks: stocks.slice(0, 6) })
      }
    }
  }

  // Fallback: sort by average momentum_score when top_sectors unavailable
  if (groups.length === 0 && map.size > 0) {
    for (const [name, stocks] of map) {
      groups.push({ name, returnPct: 0, stocks: stocks.slice(0, 6) })
    }
    groups.sort((a, b) => {
      const avgA = a.stocks.reduce((s, x) => s + x.momentum_score, 0) / a.stocks.length
      const avgB = b.stocks.reduce((s, x) => s + x.momentum_score, 0) / b.stocks.length
      return avgB - avgA
    })
  }

  return groups.slice(0, 5)
})

/* ========== Overall ranking = stocks from sector groups, mixed sort ========== */
const overallRanking = computed(() => {
  const all: ScoreResult[] = []
  for (const g of sectorGroups.value) {
    all.push(...g.stocks)
  }
  // Deduplicate (a stock may appear in multiple custom sectors)
  const seen = new Set<string>()
  const unique: ScoreResult[] = []
  for (const s of all) {
    if (!seen.has(s.stock_id)) {
      seen.add(s.stock_id)
      unique.push(s)
    }
  }
  let list = unique.sort((a, b) => b.momentum_score - a.momentum_score)
  if (activeClassification.value !== 'all') {
    list = list.filter(r => r.classification === activeClassification.value)
  }
  if (activeSector.value !== 'all') {
    list = list.filter(r => r.sector_name === activeSector.value)
  }
  return list
})

/* ========== Pagination (overall ranking) ========== */
const currentPage = ref(1)
const pageSize = 10
const LOW_RESULT_THRESHOLD = 10

const totalPages = computed(() => Math.ceil(overallRanking.value.length / pageSize))


const handlePageChange = (page: number) => {
  currentPage.value = page
}

/* ========== Stat cards ========== */
const statCards = computed(() => {
  const results = overallRanking.value
  const top = results[0]
  const buyCount = results.filter(r => r.classification === 'BUY').length
  return [
    {
      label: '分析股票數',
      value: results.length.toLocaleString(),
      change: '全市場覆蓋',
      changeClass: 'up',
    },
    {
      label: '最高動能分數',
      value: top ? top.momentum_score.toFixed(1) : '-',
      change: top ? `${top.stock_id} ${top.stock_name}` : '',
      changeClass: 'up',
      valueStyle: 'color: var(--amber)',
    },
    {
      label: 'BUY 訊號',
      value: buyCount.toString(),
      change: '可進場標的數',
      changeClass: 'up',
      valueStyle: 'color: var(--up)',
    },
    {
      label: '資料日期',
      value: screeningStore.latestDate || '-',
      change: '',
      changeClass: '',
      valueStyle: 'font-size: 1.2rem',
    },
  ]
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

const sortedOverall = computed(() => {
  if (!sortKey.value) return overallRanking.value
  const arr = [...overallRanking.value]
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

const sortedPaged = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return sortedOverall.value.slice(start, start + pageSize)
})

/* ========== Helpers ========== */
import { scoreClass, classificationBadge, signalLabel, formatPrice } from '@/utils/format'
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
})
</script>

<template>
  <div class="dashboard-page" style="animation: fadeIn 0.3s ease">

    <!-- Market trend signal -->

    <!-- Stat cards -->
    <div class="stat-grid">
      <div v-for="(card, i) in statCards" :key="i" class="stat-card">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value" :style="card.valueStyle">{{ card.value }}</div>
        <div :class="['stat-change', card.changeClass]">{{ card.change }}</div>
      </div>
    </div>

    <!-- Low results hint (post-holiday) -->
    <div
      v-if="!screeningStore.loading && screeningStore.results.length > 0 && screeningStore.results.length < LOW_RESULT_THRESHOLD"
      class="low-results-hint"
    >
      連假後交易資料尚在累積中，篩選結果較少屬正常現象，待數個交易日後將恢復正常數量。
    </div>

    <!-- Downtrend empty state -->
    <div v-if="isDowntrend" class="empty-state">
      <p>市場處於空頭趨勢，目前不顯示推薦標的</p>
    </div>

    <template v-else>
      <!-- Sector groups -->
      <div class="section-header">
        <div class="section-title" style="margin-bottom: 0; display: flex; align-items: center; gap: 8px">
          族群分組精選
          <span :class="['trend-tag', isDowntrend ? 'trend-down' : 'trend-up']">
            <span class="trend-dot" />{{ isDowntrend ? '空頭' : '多頭' }}
          </span>
        </div>
      </div>

      <div class="sector-scroll">
        <div v-for="group in sectorGroups" :key="group.name" class="sector-chip card">
          <div class="sector-chip-header">
            <span class="sector-chip-name">{{ group.name }}</span>
            <span class="sector-chip-meta">
              <span :class="group.returnPct >= 0 ? 'text-up' : 'text-down'">{{ group.returnPct >= 0 ? '+' : '' }}{{ group.returnPct.toFixed(1) }}%</span>
              <span class="sector-chip-count">{{ group.stocks.length }}檔</span>
            </span>
          </div>
          <div class="sector-chip-stocks">
            <div
              v-for="s in group.stocks"
              :key="s.stock_id"
              class="sector-chip-row"
              @click.stop="openStock(s)"
            >
              <span class="stock-code">{{ s.stock_id }}</span>
              <span class="stock-name-short">{{ s.stock_name }}</span>
              <span :class="['score-pill-sm', scoreClass(s.momentum_score)]">{{ s.momentum_score.toFixed(0) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Overall ranking -->
      <div class="section-header">
        <div class="section-title" style="margin-bottom: 0; display: flex; align-items: center; gap: 10px; flex-wrap: wrap">
          綜合動能排行
          <span class="badge">共 {{ overallRanking.length }} 檔</span>
        </div>

        <!-- Classification filter tabs + sector select (desktop) -->
        <div class="category-tabs desktop-only">
          <div
            v-for="tab in classificationTabs"
            :key="tab.key"
            :class="['cat-tab', { active: activeClassification === tab.key }]"
            @click="activeClassification = tab.key; currentPage = 1"
          >
            {{ tab.label }}
            <span class="cat-count">{{ tab.count }}</span>
          </div>
          <select
            v-model="activeSector"
            class="sector-select"
            @change="currentPage = 1"
          >
            <option value="all">全部族群</option>
            <option v-for="s in sectorList" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <div class="filter-row mobile-only">
          <select
            v-model="activeClassification"
            class="category-select"
            @change="currentPage = 1"
          >
            <option v-for="tab in classificationTabs" :key="tab.key" :value="tab.key">
              {{ tab.label }} ({{ tab.count }})
            </option>
          </select>
          <select
            v-model="activeSector"
            class="sector-select"
            @change="currentPage = 1"
          >
            <option value="all">全部族群</option>
            <option v-for="s in sectorList" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

      </div>

      <div class="card" style="margin-bottom: 20px">
        <table class="stock-table">
          <thead>
            <tr>
              <th style="width: 50px">#</th>
              <th class="sortable-th" @click="toggleSort('stock_id')">代號 <span class="sort-icon">{{ sortIcon('stock_id') }}</span></th>
              <th class="sortable-th" @click="toggleSort('stock_name')">名稱 <span class="sort-icon">{{ sortIcon('stock_name') }}</span></th>
              <th>族群</th>
              <th>信號</th>
              <th class="sortable-th" @click="toggleSort('momentum_score')">動能 <span class="sort-icon">{{ sortIcon('momentum_score') }}</span></th>
              <th class="sortable-th" @click="toggleSort('close_price')">收盤價 <span class="sort-icon">{{ sortIcon('close_price') }}</span></th>
              <th class="sortable-th" @click="toggleSort('change_percent')">漲跌 <span class="sort-icon">{{ sortIcon('change_percent') }}</span></th>
              <th>進場</th>
              <th>停損</th>
              <th>目標</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, idx) in sortedPaged"
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
              <td class="sector-label">{{ row.sector_name || '—' }}</td>
              <td><span :class="['cls-badge', classificationBadge(row.classification)]">{{ signalLabel(row.classification) }}</span></td>
              <td><span :class="['score-pill', scoreClass(row.momentum_score)]">{{ row.momentum_score.toFixed(1) }}</span></td>
              <td style="font-family: var(--font-mono)">${{ row.close_price?.toFixed(2) ?? '-' }}</td>
              <td :class="['price-change', row.change_percent >= 0 ? 'up' : 'down']" style="font-family: var(--font-mono)">
                {{ formatChange(row) }}
              </td>
              <td style="font-family: var(--font-mono)">{{ formatPrice(row.buy_price) }}</td>
              <td style="font-family: var(--font-mono)">{{ formatPrice(row.stop_price) }}</td>
              <td style="font-family: var(--font-mono)">{{ formatPrice(row.target_price) }}</td>
            </tr>
            <tr v-if="sortedPaged.length === 0">
              <td colspan="11" style="text-align: center; color: var(--text-muted); padding: 40px">
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
    </template>

  </div>
</template>

<style scoped>
.dashboard-page {
  padding: 24px 28px;
}

/* Market signal */
.market-signal {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-radius: 10px;
  margin-bottom: 18px;
  font-weight: 600;
  font-size: 0.92rem;
}
.signal-up {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
}
.signal-down {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}
.signal-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}
.signal-up .signal-dot { background: #22c55e; box-shadow: 0 0 8px rgba(34, 197, 94, 0.5); }
.signal-down .signal-dot { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.5); }

/* Classification badges */
.cls-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-mono);
  letter-spacing: 0.03em;
}
.cls-buy { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.cls-watch { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.cls-early { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.cls-ignore { background: rgba(107, 114, 128, 0.15); color: #6b7280; }
.sector-label { font-size: 0.78rem; color: var(--text-secondary); white-space: nowrap; }
.trend-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 0.7rem; font-weight: 600; padding: 2px 8px;
  border-radius: 10px;
}
.trend-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.trend-up { background: rgba(34,197,94,0.15); color: #22c55e; }
.trend-up .trend-dot { background: #22c55e; }
.trend-down { background: rgba(239,68,68,0.15); color: #ef4444; }
.trend-down .trend-dot { background: #ef4444; }
.sector-select {
  background: var(--bg-card);
  color: var(--text);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.82rem;
  cursor: pointer;
  margin-left: 8px;
}
.filter-row {
  display: flex;
  gap: 8px;
  width: 100%;
}
.filter-row select {
  flex: 1;
  margin-left: 0;
  background: var(--bg-card) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%239ca3af'/%3E%3C/svg%3E") no-repeat right 10px center;
  color: var(--text);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 6px;
  padding: 8px 28px 8px 10px;
  font-size: 0.82rem;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}

/* Sector horizontal scroll */
.sector-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 20px;
  scrollbar-width: thin;
}
.sector-scroll::-webkit-scrollbar { height: 4px; }
.sector-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }
.sector-chip {
  min-width: 200px;
  max-width: 220px;
  flex-shrink: 0;
  padding: 10px 12px;
}
.sector-chip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.sector-chip-name {
  font-weight: 700;
  font-size: 0.82rem;
  color: var(--text);
}
.sector-chip-meta {
  display: flex;
  gap: 6px;
  align-items: center;
}
.sector-chip-count {
  font-size: 0.7rem;
  color: var(--text-secondary);
}
.text-up { color: #22c55e; font-size: 0.72rem; font-weight: 600; }
.text-down { color: #ef4444; font-size: 0.72rem; font-weight: 600; }
.sector-chip-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 2px;
  cursor: pointer;
  font-size: 0.78rem;
  border-radius: 3px;
}
.sector-chip-row:hover {
  background: rgba(229, 169, 26, 0.06);
}
.score-pill-sm {
  margin-left: auto;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
}
.stock-name-short {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
  font-size: 0.92rem;
}

/* Desktop/Mobile toggle */
.desktop-only { display: flex; }
.mobile-only { display: none; }

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
.category-select:hover { border-color: var(--border-light); }
.category-select:focus { border-color: var(--amber); box-shadow: 0 0 0 2px rgba(229, 169, 26, 0.1); }

@media (max-width: 768px) {
  .dashboard-page { padding: 16px 16px; }
  .section-header { flex-direction: column; align-items: flex-start; }
  .section-title { font-size: 0.95rem; }
  .desktop-only { display: none !important; }
  .mobile-only { display: block; }
  .filter-row.mobile-only { display: flex !important; }
  .category-select { margin-top: 0; }
  .sector-chip { min-width: 170px; max-width: 180px; }
  .pagination { gap: 6px; padding: 12px 0 6px; }
  .page-btn { min-width: 40px; height: 40px; font-size: 15px; }
  .page-btn.active { font-size: 16px; font-weight: 900; color: #0e1525 !important; }
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
.sortable-th:hover { color: var(--amber); }
.sort-icon { font-size: 0.7rem; color: var(--text-muted); margin-left: 2px; }
.sortable-th:hover .sort-icon { color: var(--amber); }

.low-results-hint {
  padding: 12px 16px;
  margin-bottom: 14px;
  background: rgba(229, 169, 26, 0.08);
  border: 1px solid rgba(229, 169, 26, 0.25);
  border-radius: 8px;
  color: var(--amber);
  font-size: 13px;
  line-height: 1.5;
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
.ai-report-badge:hover { box-shadow: 0 0 8px rgba(139, 92, 246, 0.6); }
</style>
