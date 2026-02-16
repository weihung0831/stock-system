<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStockStore } from '@/stores/stock-store'
import { getStockScore } from '@/api/screening-api'
import { getStockReport, generateStockReport } from '@/api/reports-api'
import PriceCandlestickChart from '@/components/stock-detail/price-candlestick-chart.vue'
import TechnicalIndicatorChart from '@/components/stock-detail/technical-indicator-chart.vue'
import FactorScoreCard from '@/components/stock-detail/factor-score-card.vue'
import LlmReportPanel from '@/components/stock-detail/llm-report-panel.vue'
import SectorTag from '@/components/shared/sector-tag.vue'
import type { ScoreResult } from '@/types/screening'
import type { LLMReport } from '@/types/report'

const route = useRoute()
const router = useRouter()
const stockStore = useStockStore()
const stockId = route.params.id as string

const loading = ref(true)
const generating = ref(false)
const scoreResult = ref<ScoreResult | null>(null)
const report = ref<LLMReport | null>(null)

const dateRange = computed(() => {
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - 6)
  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0]
  }
})

const currentPrice = computed(() => {
  const prices = stockStore.prices
  if (prices.length === 0) return null
  const latest = prices[prices.length - 1]
  const prev = prices.length >= 2 ? prices[prices.length - 2] : null
  const close = Number(latest.close) || 0
  const prevClose = prev ? Number(prev.close) || 0 : 0
  const change = prevClose > 0 ? close - prevClose : 0
  const changePct = prevClose > 0 ? ((close - prevClose) / prevClose) * 100 : 0
  return { close, change, change_percent: changePct }
})

const priceClass = computed(() => {
  if (!currentPrice.value) return ''
  return currentPrice.value.change_percent >= 0 ? 'up' : 'down'
})

const loadStockData = async () => {
  loading.value = true
  try {
    await Promise.all([
      stockStore.fetchPrices(stockId, dateRange.value.start, dateRange.value.end),
      getStockScore(stockId).then(data => { scoreResult.value = data }),
      getStockReport(stockId).then(data => { report.value = data }).catch(() => { report.value = null })
    ])
  } catch (error) {
    console.error('載入股票資料失敗:', error)
  } finally {
    loading.value = false
  }
}

const handleGenerateReport = async () => {
  generating.value = true
  try {
    report.value = await generateStockReport(stockId)
  } catch (error) {
    console.error('產生 AI 分析失敗:', error)
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  loadStockData()
})
</script>

<template>
  <div class="detail-page" style="animation: fadeIn 0.3s ease">
    <!-- Back button -->
    <button class="btn-back" @click="router.push('/')">← 返回 Dashboard</button>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <span>載入中...</span>
    </div>

    <template v-else>
      <!-- Detail header -->
      <div class="detail-header">
        <div>
          <div style="display: flex; align-items: center; gap: 10px">
            <div class="stock-code-lg">{{ stockId }}</div>
            <SectorTag v-if="scoreResult?.industry" :industry="scoreResult.industry" />
          </div>
          <div class="stock-title">{{ scoreResult?.stock_name || stockId }}</div>
        </div>
        <div style="margin-left: auto; text-align: right">
          <div class="stock-price" v-if="currentPrice">${{ currentPrice.close.toFixed(2) }}</div>
          <span v-if="currentPrice" :class="['stock-price-change', priceClass]">
            {{ currentPrice.change >= 0 ? '▲' : '▼' }}
            {{ currentPrice.change >= 0 ? '+' : '' }}{{ currentPrice.change.toFixed(2) }}
            ({{ currentPrice.change_percent >= 0 ? '+' : '' }}{{ currentPrice.change_percent.toFixed(2) }}%)
          </span>
        </div>
      </div>

      <!-- Factor score cards -->
      <FactorScoreCard v-if="scoreResult" :score-result="scoreResult" />

      <!-- Charts grid -->
      <div class="detail-grid">
        <div class="card" style="padding: 20px">
          <div class="chart-title">日K線圖</div>
          <PriceCandlestickChart
            v-if="stockStore.prices.length > 0"
            :prices="stockStore.prices"
          />
          <div v-else class="no-data">無價格資料</div>
        </div>
        <div class="card" style="padding: 20px">
          <div class="chart-title">技術指標 — KD / RSI</div>
          <TechnicalIndicatorChart
            v-if="stockStore.prices.length > 0"
            :prices="stockStore.prices"
          />
        </div>
      </div>

      <!-- LLM Report -->
      <div class="llm-panel">
        <div class="panel-header">
          <h3>
            Gemini AI 分析報告
            <span class="llm-badge">★ Gemini 2.0 Flash</span>
          </h3>
          <div style="display: flex; align-items: center; gap: 12px">
            <button
              class="btn-generate"
              :disabled="generating"
              @click="handleGenerateReport"
            >
              {{ generating ? '分析中...' : report ? '重新產生' : '產生 AI 分析' }}
            </button>
          </div>
        </div>
        <LlmReportPanel :report="report" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.detail-page {
  padding: 24px 28px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px 0;
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

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 340px;
  color: var(--text-muted);
}

.btn-generate {
  padding: 7px 18px;
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
.btn-generate:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}
.btn-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
