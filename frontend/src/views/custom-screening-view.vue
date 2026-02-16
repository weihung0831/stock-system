<script setup lang="ts">
import { ref } from 'vue'
import FilterBuilderForm from '@/components/screening/filter-builder-form.vue'
import ScreeningResultTable from '@/components/screening/screening-result-table.vue'
import { runCustomScreening } from '@/api/custom-screening-api'
import type { ScoreResult } from '@/types/screening'

const loading = ref(false)
const results = ref<ScoreResult[]>([])
const errorMsg = ref('')

async function handleFilterChange(filters: any) {
  loading.value = true
  errorMsg.value = ''
  try {
    const data = await runCustomScreening(filters)
    results.value = data.map((item, index) => ({
      ...item,
      rank: index + 1,
    }))
  } catch (error: any) {
    errorMsg.value = error.response?.data?.detail || '篩選失敗，請稍後再試'
    results.value = []
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="screening-page" style="animation: fadeIn 0.3s ease">
    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">篩選結果</div>
        <div class="stat-value">{{ results.length }}</div>
        <div class="stat-change up">符合條件股票數</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">最高總分</div>
        <div class="stat-value" style="color: var(--amber)">
          {{ results.length ? results[0]!.total_score.toFixed(1) : '-' }}
        </div>
        <div class="stat-change up">
          {{ results.length ? `${results[0]!.stock_id} ${results[0]!.stock_name}` : '' }}
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">高籌碼分數</div>
        <div class="stat-value" style="color: var(--up)">
          {{ results.filter(r => r.chip_score >= 60).length }}
        </div>
        <div class="stat-change up">籌碼分 ≥ 60</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">功能說明</div>
        <div class="stat-value" style="font-size: 1.2rem">自訂篩選</div>
        <div class="stat-change">依條件篩選全市場</div>
      </div>
    </div>

    <!-- Section header -->
    <div class="section-header">
      <div class="section-title" style="margin-bottom: 0">
        篩選條件設定
      </div>
    </div>

    <!-- Filter form -->
    <FilterBuilderForm @filter-change="handleFilterChange" />

    <!-- Error message -->
    <div v-if="errorMsg" class="error-bar">{{ errorMsg }}</div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <span>篩選中...</span>
    </div>

    <!-- Results -->
    <template v-else-if="results.length > 0">
      <div class="section-header">
        <div class="section-title" style="margin-bottom: 0">
          篩選結果
          <span class="badge">共 {{ results.length }} 檔</span>
        </div>
      </div>
      <ScreeningResultTable :results="results" />
    </template>

    <!-- Empty state -->
    <div v-else-if="!loading && !errorMsg" class="empty-state">
      <p>請設定篩選條件並執行篩選</p>
    </div>
  </div>
</template>

<style scoped>
.screening-page {
  padding: 24px 28px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
}

.error-bar {
  margin: 16px 0;
  padding: 12px 16px;
  background: var(--down-bg);
  border: 1px solid var(--down);
  border-radius: var(--radius-sm);
  color: var(--down);
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

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
  font-size: 0.92rem;
}
</style>
