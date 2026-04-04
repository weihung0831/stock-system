<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import { usePortfolioStore } from '@/stores/portfolio-store'
import PortfolioTable from '@/components/portfolio/portfolio-table.vue'
import PortfolioForm from '@/components/portfolio/portfolio-form.vue'
import type { AlertItem, RealtimeItem } from '@/types/portfolio'

const store = usePortfolioStore()
const showForm = ref(false)
const editItem = ref<RealtimeItem | null>(null)

const alertedIds = new Set<number>()

function showAlerts(alerts: AlertItem[]) {
  for (const alert of alerts) {
    if (alertedIds.has(alert.portfolio_id)) continue
    alertedIds.add(alert.portfolio_id)
    ElNotification({
      title: `${alert.stock_name} 達標`,
      message: `獲利 ${alert.profit_pct.toFixed(2)}% 已達目標 ${alert.target_return_pct.toFixed(1)}%`,
      type: 'success',
      duration: 6000,
    })
  }
}

watch(
  () => store.realtimeData?.new_alerts,
  (alerts) => {
    if (alerts && alerts.length > 0) showAlerts(alerts)
  },
)

function handleDelete(portfolioId: number) {
  store.removePortfolio(portfolioId)
}

function handleEdit(item: RealtimeItem) {
  editItem.value = item
  showForm.value = true
}

function handleCreated() {
  showForm.value = false
  editItem.value = null
}

function handleUpdated() {
  showForm.value = false
  editItem.value = null
}

function profitColor(val: number): string {
  if (val > 0) return 'var(--up, #22c55e)'
  if (val < 0) return 'var(--down, #ef4444)'
  return 'var(--text-secondary)'
}

onMounted(() => {
  store.fetchPortfolios()
  store.startPolling()
})

onUnmounted(() => {
  store.stopPolling()
})
</script>

<template>
  <div class="portfolio-monitor">
    <div
      v-if="store.realtimeData && !store.isMarketOpen"
      class="banner banner-info"
    >
      目前非開盤時間，顯示收盤價
    </div>

    <div
      v-if="store.realtimeData && store.isMarketOpen && !store.realtimeData.is_realtime"
      class="banner banner-warning"
    >
      即時報價取得異常，目前顯示延遲數據
    </div>

    <div class="page-header">
      <h1 class="page-title">持股監控</h1>
      <button class="amber-btn" @click="editItem = null; showForm = true">＋ 新增持股</button>
    </div>

    <div v-if="store.realtimeData && store.realtimeData.items.length > 0" class="stat-grid" style="grid-template-columns: repeat(2, 1fr)">
      <div class="stat-card">
        <div class="stat-label">總獲利金額</div>
        <div class="stat-value" :style="{ color: profitColor(store.totalProfit) }">
          {{ store.totalProfit >= 0 ? '+' : '' }}{{ store.totalProfit.toLocaleString() }}
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">總報酬率</div>
        <div class="stat-value" :style="{ color: profitColor(store.totalProfitPct) }">
          {{ store.totalProfitPct >= 0 ? '+' : '' }}{{ store.totalProfitPct.toFixed(2) }}%
        </div>
      </div>
    </div>

    <div v-if="store.realtimeData && store.realtimeData.items.length > 0" class="table-wrap">
      <PortfolioTable
        :items="store.realtimeData.items"
        :loading="store.loading"
        :market-open="store.isMarketOpen"
        @delete="handleDelete"
        @edit="handleEdit"
      />
    </div>

    <div
      v-else-if="!store.loading && store.realtimeData"
      class="empty-state"
    >
      <div class="empty-icon">📊</div>
      <div class="empty-text">尚無持股資料</div>
      <button class="amber-btn" @click="showForm = true">新增您的第一檔持股</button>
    </div>

    <PortfolioForm
      v-model:visible="showForm"
      :edit-item="editItem"
      @created="handleCreated"
      @updated="handleUpdated"
    />
  </div>
</template>

<style scoped>
.portfolio-monitor {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.banner {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
}

.banner-info {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  color: var(--amber, #f59e0b);
}

.banner-warning {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text, #fff);
  margin: 0;
}

.table-wrap {
  background: var(--bg-card, #1a1f2e);
  border: 1px solid var(--border, #243049);
  border-radius: var(--radius, 10px);
  overflow: hidden;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: var(--bg-card, #1e1e2e);
  border: 1px solid var(--border, #333);
  border-radius: 10px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.amber-btn {
  background: var(--amber, #f59e0b);
  color: #000;
  border: none;
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.amber-btn:hover {
  background: #d97706;
  transform: translateY(-1px);
}

.empty-text {
  font-size: 15px;
  color: var(--text-secondary, #888);
  margin-bottom: 20px;
}
</style>
