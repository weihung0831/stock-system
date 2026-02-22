<script setup lang="ts">
import { ref, watch } from 'vue'
import { getStockSignals } from '@/api/right-side-signals-api'
import type { RightSideSignal, TradePrediction } from '@/types/right-side-signals'

const props = defineProps<{ stockId: string }>()

const signals = ref<RightSideSignal[]>([])
const triggeredCount = ref(0)
const score = ref(0)
const prediction = ref<TradePrediction | null>(null)
const todayBreakout = ref(false)
const weeklyTrendUp = ref(false)
const strongRecommend = ref(false)
const riskLevel = ref<'low' | 'medium' | 'high'>('high')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getStockSignals(props.stockId)
    signals.value = res.signals
    triggeredCount.value = res.triggered_count
    score.value = res.score
    prediction.value = res.prediction
    todayBreakout.value = res.today_breakout ?? false
    weeklyTrendUp.value = res.weekly_trend_up ?? false
    strongRecommend.value = res.strong_recommend ?? false
    riskLevel.value = res.risk_level ?? 'high'
  } catch {
    signals.value = []
    triggeredCount.value = 0
    score.value = 0
    prediction.value = null
    todayBreakout.value = false
    weeklyTrendUp.value = false
    strongRecommend.value = false
    riskLevel.value = 'high'
  } finally {
    loading.value = false
  }
}

const scoreClass = (s: number) => s >= 60 ? 'score-high' : s >= 35 ? 'score-mid' : 'score-low'
const actionClass = (a: string) => a === 'buy' ? 'act-buy' : a === 'hold' ? 'act-hold' : 'act-avoid'

watch(() => props.stockId, load, { immediate: true })
</script>

<template>
  <div class="card signal-card">
    <div class="signal-header">
      <h3>
        右側買法訊號
        <span class="triggered-badge" v-if="!loading">
          {{ triggeredCount }} / {{ signals.length }}
        </span>
        <span v-if="!loading" :class="['score-pill', scoreClass(score)]" style="margin-left: auto">
          {{ score }} 分
        </span>
      </h3>
    </div>

    <div v-if="loading" class="signal-loading">
      <div class="spinner" />
    </div>

    <div v-else>
      <!-- Condition tags -->
      <div class="cond-tags">
        <span v-if="todayBreakout" class="cond-tag breakout">今日突破</span>
        <span v-if="weeklyTrendUp" class="cond-tag trend-up">週趨勢向上</span>
        <span v-if="strongRecommend" class="cond-tag strong-rec">強力推薦</span>
        <span :class="['cond-tag', `risk-${riskLevel}`]">
          {{ riskLevel === 'low' ? '低風險' : riskLevel === 'medium' ? '中風險' : '高風險' }}
        </span>
      </div>

      <div class="signal-grid">
        <div
          v-for="sig in signals"
          :key="sig.id"
          class="signal-chip"
          :class="{ active: sig.triggered }"
          :title="sig.description"
        >
          <span class="chip-dot" />
          <span class="chip-label">{{ sig.label }}</span>
          <span class="chip-desc">{{ sig.description }}</span>
        </div>
      </div>

      <!-- Trade prediction -->
      <div v-if="prediction" class="prediction-bar">
        <span :class="['action-tag', actionClass(prediction.action)]">
          {{ prediction.action_label }}
        </span>
        <div class="pred-item">
          <span class="pred-label">進場</span>
          <span class="pred-value">${{ prediction.entry.toFixed(2) }}</span>
        </div>
        <div class="pred-item">
          <span class="pred-label">停損</span>
          <span class="pred-value down">${{ prediction.stop_loss.toFixed(2) }}</span>
        </div>
        <div class="pred-item">
          <span class="pred-label">目標</span>
          <span class="pred-value up">${{ prediction.target.toFixed(2) }}</span>
        </div>
        <div class="pred-item">
          <span class="pred-label">風報比</span>
          <span class="pred-value">1 : {{ prediction.risk_reward }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.signal-card {
  padding: 20px;
  margin-bottom: 20px;
}

.signal-header {
  margin-bottom: 14px;
}

.signal-header h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 10px;
}

.triggered-badge {
  font-size: 0.78rem;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 12px;
  background: var(--amber, #e5a91a);
  color: var(--bg-dark, #0e1525);
}

.signal-loading {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Condition tags */
.cond-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.cond-tag {
  font-size: 0.75rem;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.cond-tag.breakout {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.cond-tag.trend-up {
  background: rgba(34, 197, 94, 0.1);
  color: var(--up, #22c55e);
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.cond-tag.strong-rec {
  background: rgba(251, 191, 36, 0.15);
  color: var(--amber, #e5a91a);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.cond-tag.risk-low {
  background: rgba(34, 197, 94, 0.1);
  color: var(--up, #22c55e);
  border: 1px solid rgba(34, 197, 94, 0.25);
}

.cond-tag.risk-medium {
  background: rgba(251, 191, 36, 0.1);
  color: var(--amber, #e5a91a);
  border: 1px solid rgba(251, 191, 36, 0.25);
}

.cond-tag.risk-high {
  background: rgba(239, 68, 68, 0.1);
  color: var(--down, #ef4444);
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.signal-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.signal-chip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: var(--radius-sm, 8px);
  background: var(--bg-card, #151d2e);
  border: 1px solid var(--border, #243049);
  transition: all 0.2s;
}

.signal-chip.active {
  border-color: var(--up, #22c55e);
  background: rgba(34, 197, 94, 0.06);
}

.chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted, #556178);
  flex-shrink: 0;
}

.signal-chip.active .chip-dot {
  background: var(--up, #22c55e);
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.4);
}

.chip-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary, #8c9ab5);
}

.signal-chip.active .chip-label {
  color: var(--text, #e8ecf4);
}

.chip-desc {
  width: 100%;
  font-size: 0.75rem;
  color: var(--text-muted, #556178);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Prediction bar */
.prediction-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 14px;
  padding: 12px 16px;
  border-radius: var(--radius-sm, 8px);
  background: var(--bg-card, #151d2e);
  border: 1px solid var(--border, #243049);
  flex-wrap: wrap;
}

.action-tag {
  font-size: 0.78rem;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 12px;
  white-space: nowrap;
}

.act-buy {
  background: rgba(34, 197, 94, 0.15);
  color: var(--up, #22c55e);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.act-hold {
  background: rgba(229, 169, 26, 0.15);
  color: var(--amber, #e5a91a);
  border: 1px solid rgba(229, 169, 26, 0.3);
}

.act-avoid {
  background: rgba(239, 68, 68, 0.15);
  color: var(--down, #ef4444);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.pred-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.pred-label {
  font-size: 0.7rem;
  color: var(--text-muted, #556178);
}

.pred-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text, #e8ecf4);
  font-family: var(--font-mono);
}

.pred-value.up {
  color: var(--up, #22c55e);
}

.pred-value.down {
  color: var(--down, #ef4444);
}

@media (max-width: 768px) {
  .signal-grid {
    grid-template-columns: 1fr;
  }

  .prediction-bar {
    gap: 12px;
    justify-content: space-around;
  }
}
</style>
