<script setup lang="ts">
import { ref, onMounted } from 'vue'
import InstitutionalTrendChart from '@/components/chip-stats/institutional-trend-chart.vue'
import MarginTrendChart from '@/components/chip-stats/margin-trend-chart.vue'
import { getInstitutionalTrend, getMarginTrend } from '@/api/chip-stats-api'

const activePeriod = ref(30)
const stockId = ref('')
const loading = ref(false)
const errorMsg = ref('')
const institutionalData = ref<any[]>([])
const marginData = ref<any[]>([])

const periods = [
  { label: '7天', value: 7 },
  { label: '14天', value: 14 },
  { label: '30天', value: 30 },
  { label: '60天', value: 60 },
]

function buildParams() {
  const params: { days: number; stock_id?: string } = { days: activePeriod.value }
  const trimmed = stockId.value.trim()
  if (trimmed) params.stock_id = trimmed
  return params
}

async function fetchData() {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = buildParams()
    const [institutional, margin] = await Promise.all([
      getInstitutionalTrend(params),
      getMarginTrend(params),
    ])
    institutionalData.value = institutional
    marginData.value = margin
  } catch (error: any) {
    errorMsg.value = error.response?.data?.detail || '載入籌碼統計失敗'
  } finally {
    loading.value = false
  }
}

async function handlePeriodChange(days: number) {
  activePeriod.value = days
  await fetchData()
}

function handleStockSearch() {
  fetchData()
}

function clearStock() {
  stockId.value = ''
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="chip-page" style="animation: fadeIn 0.3s ease">
    <!-- Stat cards as page header info -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">功能說明</div>
        <div class="stat-value" style="font-size: 1.2rem">籌碼統計</div>
        <div class="stat-change">三大法人 · 融資融券</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">查詢天數</div>
        <div class="stat-value" style="color: var(--amber)">{{ activePeriod }}</div>
        <div class="stat-change up">交易日</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">法人資料筆數</div>
        <div class="stat-value" style="color: var(--up)">{{ institutionalData.length }}</div>
        <div class="stat-change up">日數據</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">融資券資料筆數</div>
        <div class="stat-value">{{ marginData.length }}</div>
        <div class="stat-change">日數據</div>
      </div>
    </div>

    <!-- Controls -->
    <div class="section-header" style="margin-bottom: 8px">
      <div class="section-title" style="margin-bottom: 0">查詢條件</div>
    </div>

    <div class="controls-card card" style="padding: 20px; margin-bottom: 20px">
      <div class="controls-row">
        <!-- Stock search -->
        <div class="search-group">
          <input
            v-model="stockId"
            type="text"
            class="search-input"
            placeholder="輸入股票代號 (如 2330)"
            @keyup.enter="handleStockSearch"
          />
          <button class="btn-search" @click="handleStockSearch">查詢</button>
          <button v-if="stockId.trim()" class="btn-clear" @click="clearStock">清除</button>
        </div>

        <!-- Period tabs -->
        <div class="category-tabs">
          <div
            v-for="p in periods"
            :key="p.value"
            :class="['cat-tab', { active: activePeriod === p.value }]"
            @click="handlePeriodChange(p.value)"
          >
            {{ p.label }}
          </div>
        </div>
      </div>

      <div v-if="stockId.trim()" class="stock-badge">
        查詢個股：<strong>{{ stockId.trim() }}</strong>
      </div>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="error-bar">{{ errorMsg }}</div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <span>載入中...</span>
    </div>

    <!-- Charts -->
    <div v-else class="charts-stack">
      <div class="card" style="padding: 20px">
        <div class="chart-title">三大法人買賣超趨勢</div>
        <InstitutionalTrendChart :data="institutionalData" />
      </div>

      <div class="card" style="padding: 20px">
        <div class="chart-title">融資融券餘額趨勢</div>
        <MarginTrendChart :data="marginData" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chip-page {
  padding: 24px 28px;
}

.controls-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.search-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-surface);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 0.88rem;
  width: 220px;
  outline: none;
  transition: border-color 0.15s;
}
.search-input:focus {
  border-color: var(--amber);
}
.search-input::placeholder {
  color: var(--text-muted);
}

.btn-search {
  padding: 8px 16px;
  background: linear-gradient(135deg, var(--amber-dim), var(--amber));
  border: none;
  border-radius: var(--radius-sm);
  color: var(--bg-dark);
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.2s;
  font-family: var(--font-sans);
}
.btn-search:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.btn-clear {
  padding: 8px 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.15s;
  font-family: var(--font-sans);
}
.btn-clear:hover {
  border-color: var(--down);
  color: var(--down);
}

.stock-badge {
  display: inline-block;
  margin-top: 12px;
  padding: 4px 12px;
  background: rgba(229, 169, 26, 0.1);
  border: 1px solid rgba(229, 169, 26, 0.2);
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  color: var(--amber);
}
.stock-badge strong {
  font-family: var(--font-mono);
}

.error-bar {
  margin-bottom: 16px;
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
@keyframes spin { to { transform: rotate(360deg); } }

.charts-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
