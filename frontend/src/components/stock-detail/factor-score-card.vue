<script setup lang="ts">
import { computed } from 'vue'
import type { ScoreResult } from '@/types/screening'

interface Props {
  scoreResult: ScoreResult | null
}

const props = defineProps<Props>()

const factors = computed(() => {
  const s = props.scoreResult
  if (!s) return []
  return [
    { label: '籌碼面評分', score: s.chip_score, color: '#8b5cf6' },
    { label: '基本面評分', score: s.fundamental_score, color: '#22d3ee' },
    { label: '技術面評分', score: s.technical_score, color: 'var(--amber)' },
  ]
})

/* SVG ring: circumference = 2 * PI * 42 ≈ 263.9 */
const CIRC = 263.9
const ringOffset = (score: number) => CIRC - (CIRC * Math.min(score, 100) / 100)
</script>

<template>
  <div class="factor-grid">
    <div v-for="f in factors" :key="f.label" class="factor-card">
      <div class="factor-label">{{ f.label }}</div>
      <div class="factor-ring">
        <svg viewBox="0 0 100 100">
          <circle class="ring-bg" cx="50" cy="50" r="42" />
          <circle
            class="ring-fill"
            cx="50" cy="50" r="42"
            :stroke="f.color"
            :stroke-dasharray="CIRC"
            :stroke-dashoffset="ringOffset(f.score)"
          />
        </svg>
        <div class="ring-value">{{ f.score.toFixed(1) }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Uses global .factor-grid, .factor-card, .factor-ring styles from App.vue prototype */
</style>
