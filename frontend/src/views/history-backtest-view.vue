<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import BacktestPerformanceChart from '@/components/backtest/backtest-performance-chart.vue'
import HistoricalResultTable from '@/components/backtest/historical-result-table.vue'
import { getBacktestPerformance, getScoreDates, type ScoreDateInfo } from '@/api/backtest-api'

const loading = ref(false)
const errorMsg = ref('')
const selectedDate = ref('')
const topN = ref(10)
const performanceData = ref<any[]>([])
const availableDates = ref<ScoreDateInfo[]>([])

const selectedDateBacktestable = computed(() => {
  const info = availableDates.value.find(d => d.date === selectedDate.value)
  return info?.backtestable ?? false
})

const topNOptions = [
  { label: '前10名', value: 10 },
  { label: '前20名', value: 20 },
  { label: '前30名', value: 30 },
  { label: '前50名', value: 50 },
]

async function fetchBacktestData() {
  if (!selectedDate.value) {
    errorMsg.value = '請選擇日期'
    return
  }

  loading.value = true
  errorMsg.value = ''
  try {
    const data = await getBacktestPerformance(selectedDate.value, topN.value)
    performanceData.value = data
    if (data.length === 0) {
      errorMsg.value = '該日期無回測數據'
    }
  } catch (error: any) {
    errorMsg.value = error.response?.data?.detail || '載入回測數據失敗'
    performanceData.value = []
  } finally {
    loading.value = false
  }
}

function handleDateChange() {
  if (selectedDate.value) fetchBacktestData()
}

function handleTopNChange() {
  if (selectedDate.value) fetchBacktestData()
}

onMounted(async () => {
  try {
    const dates = await getScoreDates()
    availableDates.value = dates
    if (dates.length > 0) {
      const backtestable = dates.find(d => d.backtestable)
      selectedDate.value = backtestable ? backtestable.date : dates[0]!.date
      fetchBacktestData()
    }
  } catch {
    availableDates.value = []
  }
})
</script>

<template>
  <div class="history-page" style="animation: fadeIn 0.3s ease">
    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">功能說明</div>
        <div class="stat-value" style="font-size: 1.2rem">歷史回測</div>
        <div class="stat-change">評分績效驗證</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">可用日期</div>
        <div class="stat-value" style="color: var(--amber)">{{ availableDates.length }}</div>
        <div class="stat-change up">評分日期</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">查詢結果</div>
        <div class="stat-value" style="color: var(--up)">{{ performanceData.length }}</div>
        <div class="stat-change up">支股票</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">排名範圍</div>
        <div class="stat-value">Top {{ topN }}</div>
        <div class="stat-change">高分股票</div>
      </div>
    </div>

    <!-- Controls -->
    <div class="section-header" style="margin-bottom: 8px">
      <div class="section-title" style="margin-bottom: 0">查詢條件</div>
    </div>

    <div class="card" style="padding: 20px; margin-bottom: 20px">
      <div class="controls-row">
        <div class="control-group">
          <label class="control-label">評分日期</label>
          <select v-model="selectedDate" class="native-select" @change="handleDateChange">
            <option value="" disabled>選擇日期</option>
            <option
              v-for="d in availableDates"
              :key="d.date"
              :value="d.date"
            >{{ d.backtestable ? d.date : `${d.date}（數據不足）` }}</option>
          </select>
        </div>

        <div class="control-group">
          <label class="control-label">排名範圍</label>
          <select v-model="topN" class="native-select" @change="handleTopNChange">
            <option v-for="opt in topNOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <button class="btn-query" :disabled="loading || !selectedDate" @click="fetchBacktestData">
          {{ loading ? '查詢中...' : '查詢回測結果' }}
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="error-bar">{{ errorMsg }}</div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <span>載入中...</span>
    </div>

    <!-- Results -->
    <template v-else-if="performanceData.length > 0">
      <div v-if="selectedDate && !selectedDateBacktestable" class="warning-bar">
        此評分日期後尚無足夠交易數據計算報酬，報酬欄位將顯示 N/A
      </div>

      <div class="card" style="padding: 20px; margin-bottom: 20px">
        <HistoricalResultTable :data="performanceData" :score-date="selectedDate" />
      </div>

      <div class="card" style="padding: 20px">
        <div class="chart-title">績效表現趨勢</div>
        <BacktestPerformanceChart :data="performanceData" />
      </div>
    </template>

    <!-- Empty -->
    <div v-else class="empty-state">
      <span v-if="availableDates.length === 0">目前尚無可回測的評分日期（需至少5天後的交易數據）</span>
      <span v-else>請選擇日期並查詢回測結果</span>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  padding: 24px 28px;
}

.controls-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-label {
  font-size: 0.82rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.native-select {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-surface);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 0.88rem;
  outline: none;
  cursor: pointer;
  min-width: 180px;
  transition: border-color 0.15s;
}
.native-select:focus { border-color: var(--amber); }

.btn-query {
  padding: 8px 20px;
  background: linear-gradient(135deg, var(--amber-dim), var(--amber));
  border: none;
  border-radius: var(--radius-sm);
  color: var(--bg-dark);
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.2s;
  font-family: var(--font-sans);
  align-self: flex-end;
}
.btn-query:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}
.btn-query:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.warning-bar {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
  border-radius: var(--radius-sm);
  color: #eab308;
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

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
}
</style>
