<script setup lang="ts">
import { computed } from 'vue'
import type { ScoreResult } from '@/types/screening'

interface Props {
  scoreResult: ScoreResult | null
}

const props = defineProps<Props>()

const classificationLabel = computed(() => {
  switch (props.scoreResult?.classification) {
    case 'BUY': return { text: '買進', cls: 'cls-buy' }
    case 'WATCH': return { text: '觀察', cls: 'cls-watch' }
    case 'EARLY': return { text: '初期', cls: 'cls-early' }
    default: return { text: '忽略', cls: 'cls-ignore' }
  }
})

const tradePlan = computed(() => {
  const s = props.scoreResult
  if (!s) return []
  return [
    { label: '進場價', value: s.buy_price },
    { label: '停損價', value: s.stop_price },
    { label: '加碼價', value: s.add_price },
    { label: '目標價', value: s.target_price },
  ]
})

/* SVG ring: circumference = 2 * PI * 42 ~ 263.9 */
const CIRC = 263.9
const ringOffset = (score: number) => CIRC - (CIRC * Math.min(score, 100) / 100)

const momentumColor = computed(() => {
  const s = props.scoreResult?.momentum_score ?? 0
  if (s >= 70) return '#22c55e'
  if (s >= 50) return 'var(--amber)'
  return '#ef4444'
})

const formatPrice = (v: number | null) => v != null ? v.toFixed(2) : '-'
</script>

<template>
  <div class="factor-grid">
    <!-- Momentum score ring -->
    <div class="factor-card">
      <div class="factor-label">動能評分</div>
      <div class="factor-ring">
        <svg viewBox="0 0 100 100">
          <circle class="ring-bg" cx="50" cy="50" r="42" />
          <circle
            class="ring-fill"
            cx="50" cy="50" r="42"
            :stroke="momentumColor"
            :stroke-dasharray="CIRC"
            :stroke-dashoffset="ringOffset(scoreResult?.momentum_score ?? 0)"
          />
        </svg>
        <div class="ring-value">{{ scoreResult?.momentum_score?.toFixed(1) ?? '-' }}</div>
      </div>
    </div>

    <!-- Classification -->
    <div class="factor-card">
      <div class="factor-label">分類訊號</div>
      <div class="classification-display">
        <span :class="['cls-badge-lg', classificationLabel.cls]">{{ classificationLabel.text }}</span>
      </div>
    </div>

    <!-- Trade plan -->
    <div class="factor-card trade-plan-card">
      <div class="factor-label">交易計畫</div>
      <div class="trade-plan-grid">
        <div v-for="item in tradePlan" :key="item.label" class="trade-item">
          <span class="trade-label">{{ item.label }}</span>
          <span class="trade-value">{{ formatPrice(item.value) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cls-badge-lg {
  display: inline-block;
  padding: 6px 18px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 700;
  font-family: var(--font-mono);
  letter-spacing: 0.05em;
}
.cls-buy { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.cls-watch { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.cls-early { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.cls-ignore { background: rgba(107, 114, 128, 0.15); color: #6b7280; }

.classification-display {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px 0;
}

.trade-plan-card {
  grid-column: span 2;
}

.trade-plan-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 8px;
}

.trade-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.trade-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 8px;
}

.trade-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trade-value {
  font-family: var(--font-mono);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text);
}

.trade-item:first-child .trade-value { color: var(--amber); }
.trade-item:nth-child(2) .trade-value { color: #ef4444; }
.trade-item:last-child .trade-value { color: #22c55e; }

@media (max-width: 768px) {
  .trade-plan-card {
    grid-column: span 1;
  }
  .trade-plan-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
