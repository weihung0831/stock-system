<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

interface PerformanceData {
  stock_id: string
  stock_name: string
  total_score: number
  return_5d: number
  return_10d: number
  return_20d: number
}

interface Props {
  data: PerformanceData[]
  scoreDate: string
}

const props = defineProps<Props>()
const router = useRouter()

const hasPartialNA = computed(() => {
  if (props.data.length === 0) return false
  const all5d = props.data.every(r => r.return_5d == null)
  const all10d = props.data.every(r => r.return_10d == null)
  const all20d = props.data.every(r => r.return_20d == null)
  return (all5d || all10d || all20d) && !(all5d && all10d && all20d)
})

function formatReturn(val: number): string {
  const sign = val >= 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}

function returnClass(val: number | null): string {
  if (val == null) return 'na'
  return val >= 0 ? 'up' : 'down'
}

function navigateToStock(stockId: string) {
  router.push(`/stock/${stockId}`)
}
</script>

<template>
  <div class="result-table-wrap">
    <div class="table-badge">
      評分日期: <strong>{{ scoreDate }}</strong>
    </div>

    <div v-if="hasPartialNA" class="partial-na-notice">
      部分報酬欄位尚無足夠交易數據，待更多交易日累積後將自動顯示
    </div>

    <div class="table-scroll">
      <table class="stock-table">
        <thead>
          <tr>
            <th>排名</th>
            <th>代碼</th>
            <th>股票名稱</th>
            <th class="num">總分</th>
            <th class="num">5日報酬</th>
            <th class="num">10日報酬</th>
            <th class="num">20日報酬</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in data" :key="row.stock_id">
            <td class="rank">{{ idx + 1 }}</td>
            <td>
              <span class="stock-code clickable" @click="navigateToStock(row.stock_id)">
                {{ row.stock_id }}
              </span>
            </td>
            <td>{{ row.stock_name }}</td>
            <td class="num">
              <span class="total-score">{{ row.total_score.toFixed(2) }}</span>
            </td>
            <td class="num">
              <span v-if="row.return_5d != null" :class="['return-val', returnClass(row.return_5d)]">
                {{ formatReturn(row.return_5d) }}
              </span>
              <span v-else class="return-val na">N/A</span>
            </td>
            <td class="num">
              <span v-if="row.return_10d != null" :class="['return-val', returnClass(row.return_10d)]">
                {{ formatReturn(row.return_10d) }}
              </span>
              <span v-else class="return-val na">N/A</span>
            </td>
            <td class="num">
              <span v-if="row.return_20d != null" :class="['return-val', returnClass(row.return_20d)]">
                {{ formatReturn(row.return_20d) }}
              </span>
              <span v-else class="return-val na">N/A</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-badge {
  display: inline-block;
  margin-bottom: 14px;
  padding: 6px 14px;
  background: rgba(229, 169, 26, 0.08);
  border: 1px solid rgba(229, 169, 26, 0.2);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  color: var(--amber);
}
.table-badge strong {
  font-family: var(--font-mono);
}

.partial-na-notice {
  margin-bottom: 12px;
  padding: 10px 16px;
  background: rgba(234, 179, 8, 0.08);
  border: 1px solid rgba(234, 179, 8, 0.2);
  border-radius: var(--radius-sm);
  color: #eab308;
  font-size: 0.82rem;
}

.table-scroll {
  overflow-x: auto;
}

.rank {
  font-family: var(--font-mono);
  color: var(--text-muted);
  font-size: 0.82rem;
}

.clickable {
  cursor: pointer;
}
.clickable:hover {
  text-decoration: underline;
}

.return-val {
  font-family: var(--font-mono);
  font-weight: 600;
  font-size: 0.85rem;
}
.return-val.up { color: var(--up); }
.return-val.down { color: var(--down); }
.return-val.na { color: var(--text-muted); }
</style>
