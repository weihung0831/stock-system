<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getLatestReports } from '@/api/reports-api'
import type { LLMReport } from '@/types/report'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const errorMsg = ref('')
const reports = ref<LLMReport[]>([])
const searchKeyword = ref('')
const confidenceFilter = ref('')
const expandedIds = ref<Set<number>>(new Set())
const currentPage = ref(1)
const pageSize = 5

const filteredReports = computed(() => {
  return reports.value.filter((report) => {
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      if (
        !report.stock_id.toLowerCase().includes(keyword) &&
        !(report.stock_name || '').toLowerCase().includes(keyword)
      ) return false
    }
    if (confidenceFilter.value && report.confidence !== confidenceFilter.value) return false
    return true
  })
})

const totalPages = computed(() => Math.ceil(filteredReports.value.length / pageSize))

const pagedReports = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredReports.value.slice(start, start + pageSize)
})

watch([searchKeyword, confidenceFilter], () => { currentPage.value = 1 })

function handlePageChange(page: number) {
  currentPage.value = page
  expandedIds.value.clear()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function toggleExpand(reportId: number) {
  if (expandedIds.value.has(reportId)) {
    expandedIds.value.delete(reportId)
  } else {
    expandedIds.value.add(reportId)
  }
}

function isExpanded(reportId: number): boolean {
  return expandedIds.value.has(reportId)
}

function confidenceClass(c: string) {
  if (c === '高' || c === 'high') return 'buy'
  if (c === '低' || c === 'low') return 'sell'
  return 'hold'
}

function navigateToStock(stockId: string) {
  router.push(`/stock/${stockId}`)
}

async function fetchReports() {
  loading.value = true
  errorMsg.value = ''
  try {
    reports.value = await getLatestReports()
  } catch (error: any) {
    errorMsg.value = error.response?.data?.detail || '載入報告失敗'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchReports()
})
</script>

<template>
  <div class="reports-page" style="animation: fadeIn 0.3s ease">
    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">報告總數</div>
        <div class="stat-value">{{ reports.length }}</div>
        <div class="stat-change up">AI 分析報告</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">篩選結果</div>
        <div class="stat-value" style="color: var(--amber)">{{ filteredReports.length }}</div>
        <div class="stat-change">符合條件</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">高信心度</div>
        <div class="stat-value" style="color: var(--up)">
          {{ reports.filter(r => r.confidence === '高' || r.confidence === 'high').length }}
        </div>
        <div class="stat-change up">信心度 = 高</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">功能說明</div>
        <div class="stat-value" style="font-size: 1.2rem">AI 報告</div>
        <div class="stat-change">Gemini 生成</div>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="section-header" style="margin-bottom: 8px">
      <div class="section-title" style="margin-bottom: 0">搜尋與篩選</div>
    </div>

    <div class="card" style="padding: 20px; margin-bottom: 20px">
      <div class="filter-row">
        <input
          v-model="searchKeyword"
          type="text"
          class="search-input"
          placeholder="搜尋股票代碼或名稱..."
          style="width: 300px"
        />
        <div class="category-tabs">
          <div
            :class="['cat-tab', { active: confidenceFilter === '' }]"
            @click="confidenceFilter = ''"
          >全部</div>
          <div
            :class="['cat-tab conf-high', { active: confidenceFilter === '高' }]"
            @click="confidenceFilter = '高'"
          >高</div>
          <div
            :class="['cat-tab conf-mid', { active: confidenceFilter === '中' }]"
            @click="confidenceFilter = '中'"
          >中</div>
          <div
            :class="['cat-tab conf-low', { active: confidenceFilter === '低' }]"
            @click="confidenceFilter = '低'"
          >低</div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="error-bar">{{ errorMsg }}</div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <span>載入中...</span>
    </div>

    <!-- Empty -->
    <div v-else-if="filteredReports.length === 0" class="empty-state">
      {{ searchKeyword ? '未找到相關報告' : '暫無分析報告' }}
    </div>

    <!-- Report list -->
    <div v-else class="reports-list">
      <div v-for="report in pagedReports" :key="report.id" class="report-card card">
        <div class="report-header" @click="toggleExpand(report.id)">
          <div class="report-info">
            <span class="stock-code clickable" @click.stop="navigateToStock(report.stock_id)">
              {{ report.stock_id }}
            </span>
            <span class="report-stock-name">{{ report.stock_name }}</span>
            <span :class="['llm-tag', confidenceClass(report.confidence)]">
              信心度: {{ report.confidence }}
            </span>
          </div>
          <div class="report-meta">
            <span class="panel-date">{{ report.report_date }}</span>
            <span :class="['expand-arrow', { expanded: isExpanded(report.id) }]">▼</span>
          </div>
        </div>

        <div class="report-preview">
          <div class="rec-label">建議:</div>
          <ul class="rec-list">
            <li v-for="(line, idx) in report.recommendation.split(/[。；\n]/).filter(l => l.trim())" :key="idx">
              {{ line.trim() }}
            </li>
          </ul>
        </div>

        <div v-if="isExpanded(report.id)" class="report-details">
          <div class="detail-section">
            <h4>💰 籌碼分析</h4>
            <ul class="detail-list">
              <li v-for="(line, idx) in report.chip_analysis.split(/[。；\n]/).filter(l => l.trim())" :key="idx">
                {{ line.trim() }}
              </li>
            </ul>
          </div>
          <div class="detail-section">
            <h4>📊 基本面分析</h4>
            <ul class="detail-list">
              <li v-for="(line, idx) in report.fundamental_analysis.split(/[。；\n]/).filter(l => l.trim())" :key="idx">
                {{ line.trim() }}
              </li>
            </ul>
          </div>
          <div class="detail-section">
            <h4>📈 技術面分析</h4>
            <ul class="detail-list">
              <li v-for="(line, idx) in report.technical_analysis.split(/[。；\n]/).filter(l => l.trim())" :key="idx">
                {{ line.trim() }}
              </li>
            </ul>
          </div>
          <div class="detail-section">
            <h4>📰 新聞情緒</h4>
            <ul class="detail-list">
              <li v-for="(line, idx) in report.news_sentiment.split(/[。；\n]/).filter(l => l.trim())" :key="idx">
                {{ line.trim() }}
              </li>
            </ul>
          </div>
          <div class="detail-section" v-if="report.news_summary">
            <h4>📰 新聞摘要</h4>
            <ul class="detail-list">
              <li v-for="(line, idx) in report.news_summary.split(/[。；\n]/).filter(l => l.trim())" :key="idx">
                {{ line.trim() }}
              </li>
            </ul>
          </div>
          <div class="detail-section" v-if="report.risk_alerts && report.risk_alerts.length > 0">
            <h4 style="color: var(--down)">⚠️ 風險警示</h4>
            <ul class="risk-list">
              <li v-for="(alert, idx) in report.risk_alerts" :key="idx">{{ alert }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button class="page-btn" :disabled="currentPage === 1" @click="handlePageChange(currentPage - 1)">‹</button>
        <button
          v-for="p in totalPages"
          :key="p"
          :class="['page-btn', { active: p === currentPage }]"
          @click="handlePageChange(p)"
        >{{ p }}</button>
        <button class="page-btn" :disabled="currentPage === totalPages" @click="handlePageChange(currentPage + 1)">›</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reports-page {
  padding: 24px 28px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.search-input {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-surface);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.15s;
}
.search-input:focus { border-color: var(--amber); }
.search-input::placeholder { color: var(--text-muted); }

/* Confidence tab color overrides */
.cat-tab.conf-high.active { background: var(--up); border-color: var(--up); }
.cat-tab.conf-mid.active { background: #eab308; border-color: #eab308; }
.cat-tab.conf-low.active { background: var(--text-muted); border-color: var(--text-muted); }

.error-bar {
  margin-bottom: 16px;
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
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
}

.reports-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.report-card {
  padding: 20px;
  transition: border-color 0.2s;
}
.report-card:hover {
  border-color: var(--border-light);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  margin-bottom: 12px;
}

.report-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.clickable {
  cursor: pointer;
}
.clickable:hover {
  text-decoration: underline;
}

.report-stock-name {
  font-size: 0.92rem;
  color: var(--text);
  font-weight: 500;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.expand-arrow {
  font-size: 0.75rem;
  color: var(--text-muted);
  transition: transform 0.3s;
}
.expand-arrow.expanded {
  transform: rotate(180deg);
}

.report-preview {
  padding: 10px 14px;
  background: rgba(229, 169, 26, 0.05);
  border-left: 3px solid var(--amber);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.rec-label {
  font-weight: 600;
  color: var(--amber);
  margin-bottom: 8px;
}

.rec-list {
  margin: 0;
  padding-left: 20px;
  color: var(--text-secondary);
  font-size: 0.88rem;
  line-height: 1.6;
}

.rec-list li {
  margin-bottom: 4px;
}

.rec-list li:last-child {
  margin-bottom: 0;
}

.report-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.detail-section {
  margin-bottom: 16px;
}
.detail-section:last-child {
  margin-bottom: 0;
}
.detail-section h4 {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 8px 0;
}

.detail-list {
  margin: 0;
  padding-left: 20px;
  color: var(--text-secondary);
  font-size: 0.88rem;
  line-height: 1.75;
}

.detail-list li {
  margin-bottom: 4px;
}

.detail-list li:last-child {
  margin-bottom: 0;
}

.risk-list {
  margin: 0;
  padding-left: 20px;
  color: #fca5a5;
  font-size: 0.88rem;
  line-height: 1.75;
}

/* Pagination - reuse dashboard style */
.pagination {
  display: flex;
  justify-content: center;
  gap: 4px;
  padding: 20px 0 4px;
}
.page-btn {
  min-width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { border-color: var(--amber); color: var(--amber); }
.page-btn.active { background: var(--amber); color: var(--bg-dark); border-color: var(--amber); font-weight: 700; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
</style>
