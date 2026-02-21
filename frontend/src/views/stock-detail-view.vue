<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStockStore } from '@/stores/stock-store'
import { getStockScore } from '@/api/screening-api'
import { getStockReport, generateStockReport, getReportQuota, type ReportQuota } from '@/api/reports-api'
import PriceCandlestickChart from '@/components/stock-detail/price-candlestick-chart.vue'
import TechnicalIndicatorChart from '@/components/stock-detail/technical-indicator-chart.vue'
import FactorScoreCard from '@/components/stock-detail/factor-score-card.vue'
import LlmReportPanel from '@/components/stock-detail/llm-report-panel.vue'
import RightSideSignalCard from '@/components/stock-detail/right-side-signal-card.vue'
import SectorTag from '@/components/shared/sector-tag.vue'
import { useSectorTagsStore } from '@/stores/sector-tags-store'
import type { ScoreResult } from '@/types/screening'
import type { LLMReport } from '@/types/report'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const stockStore = useStockStore()
const sectorTagsStore = useSectorTagsStore()
if (sectorTagsStore.tags.length === 0) sectorTagsStore.fetchTags()
const stockId = computed(() => route.params.id as string)

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
  const latest = prices[0]!
  const prev = prices.length >= 2 ? prices[1]! : null
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

// Track whether current stock already has today's report
const generatedThisSession = ref(false)

const loadStockData = async () => {
  loading.value = true
  scoreResult.value = null
  report.value = null
  generatedThisSession.value = false
  reportLimitReached.value = false
  refreshReportQuota()
  const id = stockId.value
  try {
    // Score first — triggers on-demand data fetch for non-pipeline stocks
    const [scoreData] = await Promise.all([
      getStockScore(id),
      getStockReport(id).then(data => { report.value = data }).catch(() => { report.value = null })
    ])
    scoreResult.value = scoreData
    // If report was generated within 24 hours, mark as done
    const rpt = report.value as LLMReport | null
    if (rpt?.created_at) {
      const hoursAgo = (Date.now() - new Date(rpt.created_at).getTime()) / (1000 * 60 * 60)
      if (hoursAgo < 24) generatedThisSession.value = true
    }
    // Fetch prices after on-demand data is populated
    await stockStore.fetchPrices(id, dateRange.value.start, dateRange.value.end)
  } catch (error) {
    console.error('載入股票資料失敗:', error)
  } finally {
    loading.value = false
  }
}

const reportLimitReached = ref(false)
const reportQuota = ref<ReportQuota | null>(null)

function refreshReportQuota() {
  getReportQuota().then(q => {
    reportQuota.value = q
    reportLimitReached.value = q.daily_remaining <= 0
  }).catch(() => {})
}

const handleGenerateReport = async () => {
  generating.value = true
  try {
    const oldId = report.value?.id
    report.value = await generateStockReport(stockId.value)
    generatedThisSession.value = true
    if (report.value?.id === oldId) {
      ElMessage.info('已是最新分析（24 小時內快取）')
    } else {
      ElMessage.success('AI 分析完成')
    }
  } catch (error: any) {
    const status = error.response?.status
    if (status === 429) {
      reportLimitReached.value = true
      ElMessage.warning('已達每日 AI 報告上限')
    } else {
      ElMessage.error('產生 AI 分析失敗')
    }
  } finally {
    generating.value = false
    refreshReportQuota()
  }
}

// Load on mount + reload when route param changes (same component reused)
watch(() => route.params.id, () => {
  loadStockData()
}, { immediate: true })
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

      <!-- Right-side signals -->
      <RightSideSignalCard :stock-id="stockId" />

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
            AI 分析報告
            <span v-if="report?.model_used" class="llm-badge">★ {{ report.model_used }}</span>
          </h3>
          <div style="display: flex; align-items: center; gap: 12px">
            <router-link v-if="reportLimitReached" to="/pricing" class="report-limit-hint">
              升級 Premium &rarr;
            </router-link>
            <button
              class="btn-generate"
              :disabled="generating || reportLimitReached"
              @click="handleGenerateReport"
              :title="reportLimitReached ? '已達每日 AI 報告上限' : ''"
            >
              {{ generating ? '分析中...' : reportLimitReached ? '已達上限' : report ? '更新分析' : '產生 AI 分析' }}
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
.report-quota-text {
  font-size: 0.75rem;
  font-family: var(--font-mono);
  color: var(--text-muted);
}
.report-limit-hint {
  font-size: 0.78rem;
  color: #e5a91a;
  text-decoration: none;
  font-weight: 600;
  white-space: nowrap;
  transition: opacity 0.15s;
}
.report-limit-hint:hover {
  opacity: 0.8;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .detail-page {
    padding: 16px 16px;
  }

  .detail-header {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 16px;
  }

  .detail-header > div:last-child {
    margin-left: 0 !important;
    text-align: left !important;
    width: 100%;
  }

  .stock-title {
    font-size: 1.4rem !important;
  }

  .stock-price {
    font-size: 1.6rem !important;
  }

  .stock-price-change {
    font-size: 0.9rem !important;
  }

  .detail-grid {
    grid-template-columns: 1fr !important;
  }

  .llm-panel {
    padding: 16px !important;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 12px;
  }

  .panel-header h3 {
    font-size: 0.95rem;
  }

  .btn-generate {
    width: 100%;
    padding: 10px 18px;
    font-size: 0.9rem;
  }
}
</style>
