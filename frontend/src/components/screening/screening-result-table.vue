<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { ScoreResult } from '@/types/screening'

interface Props {
  results: ScoreResult[]
}

defineProps<Props>()
const router = useRouter()

const scoreClass = (v: number) => v >= 80 ? 'score-high' : v >= 65 ? 'score-mid' : 'score-low'

const formatChange = (row: ScoreResult) => {
  const pct = row.change_percent ?? 0
  const arrow = pct >= 0 ? '▲' : '▼'
  const sign = pct >= 0 ? '+' : ''
  return `${arrow} ${sign}${pct.toFixed(2)}%`
}

function openStock(row: ScoreResult) {
  router.push(`/stock/${row.stock_id}`)
}
</script>

<template>
  <div class="card">
    <table class="stock-table">
      <thead>
        <tr>
          <th style="width: 50px">#</th>
          <th>代號</th>
          <th>名稱</th>
          <th>收盤價</th>
          <th>漲跌</th>
          <th>籌碼</th>
          <th>基本面</th>
          <th>技術面</th>
          <th>總分</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, idx) in results"
          :key="row.stock_id"
          @click="openStock(row)"
        >
          <td class="rank-num">{{ row.rank ?? idx + 1 }}</td>
          <td class="stock-code">{{ row.stock_id }}</td>
          <td class="stock-name">{{ row.stock_name }}</td>
          <td style="font-family: var(--font-mono)">${{ row.close_price?.toFixed(2) ?? '-' }}</td>
          <td :class="['price-change', (row.change_percent ?? 0) >= 0 ? 'up' : 'down']" style="font-family: var(--font-mono)">
            {{ formatChange(row) }}
          </td>
          <td><span :class="['score-pill', scoreClass(row.chip_score)]">{{ row.chip_score.toFixed(1) }}</span></td>
          <td><span :class="['score-pill', scoreClass(row.fundamental_score)]">{{ row.fundamental_score.toFixed(1) }}</span></td>
          <td><span :class="['score-pill', scoreClass(row.technical_score)]">{{ row.technical_score.toFixed(1) }}</span></td>
          <td class="total-score">{{ row.total_score.toFixed(1) }}</td>
        </tr>
        <tr v-if="results.length === 0">
          <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 40px">
            尚無資料
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
