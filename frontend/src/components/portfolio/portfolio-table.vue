<script setup lang="ts">
import { ElMessageBox } from 'element-plus'
import type { RealtimeItem } from '@/types/portfolio'

const props = defineProps<{
  items: RealtimeItem[]
  loading: boolean
  marketOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'delete', portfolioId: number): void
  (e: 'edit', item: RealtimeItem): void
}>()

function profitColor(val: number): string {
  if (val > 0) return 'var(--up, #22c55e)'
  if (val < 0) return 'var(--down, #ef4444)'
  return 'var(--text-secondary)'
}

function momentumIcon(status: string): string {
  if (status === 'green') return '🟢'
  if (status === 'yellow') return '🟡'
  if (status === 'red') return '🔴'
  return ''
}

function momentumLabel(status: string): string {
  if (status === 'green') return '維持'
  if (status === 'yellow') return '降級'
  if (status === 'red') return '衰退'
  return ''
}

function statusLabel(item: RealtimeItem, marketOpen: boolean): string {
  if (item.target_reached) return '🎯 達標'
  if (!item.is_realtime && !marketOpen) return '收盤'
  if (!item.is_realtime && marketOpen) return '延遲'
  return '持有中'
}

function statusClass(item: RealtimeItem, marketOpen: boolean): string {
  if (item.target_reached) return 'status-reached'
  if (!item.is_realtime && marketOpen) return 'status-delayed'
  if (!item.is_realtime && !marketOpen) return 'status-closed'
  return 'status-holding'
}

async function confirmDelete(portfolioId: number) {
  try {
    await ElMessageBox.confirm('確定要刪除此持股？', '刪除確認', {
      confirmButtonText: '刪除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    emit('delete', portfolioId)
  } catch {
    // cancelled
  }
}
</script>

<template>
  <div class="table-container">
    <table class="stock-table">
      <colgroup>
        <col style="width:70px">
        <col style="width:80px">
        <col style="width:80px">
        <col style="width:80px">
        <col style="width:95px">
        <col style="width:65px">
        <col style="width:65px">
        <col style="width:70px">
        <col style="width:80px">
        <col style="width:65px">
        <col style="width:110px">
      </colgroup>
      <thead>
        <tr>
          <th>代號</th>
          <th>名稱</th>
          <th style="text-align:right">現價</th>
          <th style="text-align:right">獲利%</th>
          <th style="text-align:right">獲利金額</th>
          <th style="text-align:center">動能</th>
          <th style="text-align:right">目標%</th>
          <th style="text-align:center">狀態</th>
          <th style="text-align:right">成本價</th>
          <th style="text-align:right">股數</th>
          <th style="text-align:center">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in items"
          :key="row.portfolio_id"
          :class="{ 'target-reached-row': row.target_reached }"
        >
          <td class="mono">{{ row.stock_id }}</td>
          <td>{{ row.stock_name }}</td>
          <td style="text-align:right" class="mono">{{ row.current_price.toFixed(2) }}</td>
          <td style="text-align:right">
            <span class="mono" :style="{ color: profitColor(row.profit_pct) }">
              {{ row.profit_pct >= 0 ? '+' : '' }}{{ row.profit_pct.toFixed(2) }}%
            </span>
          </td>
          <td style="text-align:right">
            <span class="mono" :style="{ color: profitColor(row.profit_amount) }">
              {{ row.profit_amount >= 0 ? '+' : '' }}{{ row.profit_amount.toLocaleString() }}
            </span>
          </td>
          <td style="text-align:center">
            <span v-if="row.momentum_status !== 'unknown'" class="momentum-cell" :title="row.momentum_status">
              {{ momentumIcon(row.momentum_status) }}
              <span class="momentum-text">{{ momentumLabel(row.momentum_status) }}</span>
            </span>
            <span v-else class="text-muted" style="font-size:0.75rem">N/A</span>
          </td>
          <td style="text-align:right" class="mono text-muted">{{ row.target_return_pct.toFixed(1) }}%</td>
          <td style="text-align:center">
            <span :class="['status-tag', statusClass(row, props.marketOpen)]">
              {{ statusLabel(row, props.marketOpen) }}
            </span>
          </td>
          <td style="text-align:right" class="mono text-muted">{{ row.cost_price.toFixed(2) }}</td>
          <td style="text-align:right" class="mono text-muted">{{ row.quantity.toLocaleString() }}</td>
          <td style="text-align:center">
            <button class="edit-btn" @click="emit('edit', row)">編輯</button>
            <button class="delete-btn" @click="confirmDelete(row.portfolio_id)">刪除</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-container {
  overflow-x: auto;
}

.mono {
  font-family: 'JetBrains Mono', monospace;
}

.text-muted {
  color: var(--text-secondary, #8c9ab5);
}

.target-reached-row {
  background: rgba(34, 197, 94, 0.06) !important;
}

.target-reached-row td {
  border-bottom-color: rgba(34, 197, 94, 0.15);
}

.momentum-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.82rem;
}

.momentum-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.status-reached {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.status-holding {
  background: rgba(245, 158, 11, 0.12);
  color: var(--amber, #f59e0b);
}

.status-delayed {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.status-closed {
  background: rgba(140, 154, 181, 0.1);
  color: var(--text-secondary, #8c9ab5);
}

.edit-btn {
  background: transparent;
  border: 1px solid rgba(245, 158, 11, 0.3);
  color: var(--amber, #f59e0b);
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
  margin-right: 6px;
}

.edit-btn:hover {
  background: rgba(245, 158, 11, 0.1);
  border-color: var(--amber, #f59e0b);
}

.delete-btn {
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
}
</style>
