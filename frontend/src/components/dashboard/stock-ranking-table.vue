<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElTooltip } from 'element-plus'
import SectorTag from '@/components/shared/sector-tag.vue'
import type { ScoreResult } from '@/types/screening'

interface Props {
  results: ScoreResult[]
  reportStockIds?: Set<string>
}

const props = withDefaults(defineProps<Props>(), {
  reportStockIds: () => new Set<string>(),
})
const emit = defineEmits<{
  'stock-hover': [stock: ScoreResult]
}>()
const router = useRouter()

const handleRowClick = (row: ScoreResult) => {
  router.push(`/stock/${row.stock_id}`)
}

const handleRowHover = (row: ScoreResult) => {
  emit('stock-hover', row)
}

const formatPercent = (val: number) => {
  const sign = val >= 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}
</script>

<template>
  <div class="stock-ranking-table">
    <el-table
      :data="results"
      stripe
      :row-style="{ cursor: 'pointer' }"
      @row-click="handleRowClick"
      @cell-mouse-enter="handleRowHover"
      :default-sort="{ prop: 'rank', order: 'ascending' }"
    >
      <el-table-column prop="rank" label="排名" width="80" sortable />

      <el-table-column label="產業" width="120">
        <template #default="{ row }">
          <SectorTag :industry="row.industry" />
        </template>
      </el-table-column>

      <el-table-column prop="stock_id" label="代碼" width="100" />
      <el-table-column prop="stock_name" label="股票名稱" width="160">
        <template #default="{ row }">
          <span>{{ row.stock_name }}</span>
          <el-tooltip v-if="reportStockIds.has(row.stock_id)" content="已有 AI 分析報告" placement="top">
            <span class="ai-badge" @click.stop="router.push(`/reports?stock=${row.stock_id}`)">AI</span>
          </el-tooltip>
        </template>
      </el-table-column>

      <el-table-column prop="close_price" label="收盤價" width="100" sortable>
        <template #default="{ row }">
          <span class="price-value">{{ row.close_price.toFixed(2) }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="change_percent" label="漲跌幅" width="100" sortable>
        <template #default="{ row }">
          <span :class="['change-percent', row.change_percent >= 0 ? 'rise' : 'fall']">
            {{ formatPercent(row.change_percent) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="chip_score" label="籌碼分數" width="110" sortable>
        <template #default="{ row }">
          <span class="score-value">{{ row.chip_score.toFixed(2) }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="fundamental_score" label="基本面分數" width="120" sortable>
        <template #default="{ row }">
          <span class="score-value">{{ row.fundamental_score.toFixed(2) }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="technical_score" label="技術面分數" width="120" sortable>
        <template #default="{ row }">
          <span class="score-value">{{ row.technical_score.toFixed(2) }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="total_score" label="總分" width="100" sortable>
        <template #default="{ row }">
          <span class="total-score">{{ row.total_score.toFixed(2) }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.stock-ranking-table {
  margin-top: 16px;
}

.price-value,
.score-value,
.total-score {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}

.change-percent {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

.change-percent.rise {
  color: #22c55e;
}

.change-percent.fall {
  color: #ef4444;
}

.total-score {
  color: #e5a91a;
  font-weight: 600;
}

.ai-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 5px;
  font-size: 10px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: #0e1525;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border-radius: 3px;
  cursor: pointer;
  vertical-align: middle;
  line-height: 1.4;
  transition: box-shadow 0.15s;
}
.ai-badge:hover {
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.6);
}

:deep(.el-table) {
  background-color: transparent;
  color: #d1d5db;
}

:deep(.el-table tr) {
  background-color: rgba(255, 255, 255, 0.02);
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: rgba(255, 255, 255, 0.04);
}

:deep(.el-table th) {
  background-color: rgba(255, 255, 255, 0.05);
  color: #9ca3af;
  font-family: 'Noto Sans TC', sans-serif;
}

:deep(.el-table td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

:deep(.el-table__body tr:hover > td) {
  background-color: rgba(229, 169, 26, 0.1) !important;
}
</style>
