<script setup lang="ts">
import { computed } from 'vue'
import type { LLMReport } from '@/types/report'

interface Props {
  report: LLMReport | null
}

const props = defineProps<Props>()

const confidenceClass = computed(() => {
  const c = props.report?.confidence
  if (c === '高' || c === 'high') return 'buy'
  if (c === '低' || c === 'low') return 'sell'
  return 'hold'
})

const confidenceLabel = computed(() => {
  const c = props.report?.confidence
  if (!c) return ''
  const map: Record<string, string> = { high: '高', medium: '中', low: '低' }
  return map[c] || c
})

function splitToBullets(text: string | undefined | null): string[] {
  if (!text) return []
  return text
    .split('。')
    .map(s => s.trim())
    .filter(s => s.length > 0)
    .map(s => s + '。')
}

const chipBullets = computed(() => splitToBullets(props.report?.chip_analysis))
const fundamentalBullets = computed(() => splitToBullets(props.report?.fundamental_analysis))
const technicalBullets = computed(() => splitToBullets(props.report?.technical_analysis))
const rightSideBullets = computed(() => splitToBullets(props.report?.right_side_analysis))
const newsSummaryBullets = computed(() => splitToBullets(props.report?.news_summary))
const recommendationItems = computed(() => splitToBullets(props.report?.recommendation))
</script>

<template>
  <div class="llm-content" v-if="!report">
    <p style="text-align: center; color: var(--text-muted); padding: 24px 0">
      目前無 AI 分析報告，請點擊上方按鈕產生
    </p>
  </div>

  <div class="llm-content" v-else>
    <!-- Meta -->
    <div class="report-meta-row">
      <span class="panel-date">{{ report.report_date }}</span>
      <span :class="['llm-tag', confidenceClass]">信心度: {{ confidenceLabel }}</span>
    </div>

    <!-- Sections -->
    <h4>💰 籌碼分析</h4>
    <ul class="llm-bullets">
      <li v-for="(item, idx) in chipBullets" :key="'c'+idx">{{ item }}</li>
    </ul>

    <h4>📊 基本面分析</h4>
    <ul class="llm-bullets">
      <li v-for="(item, idx) in fundamentalBullets" :key="'f'+idx">{{ item }}</li>
    </ul>

    <h4>📈 技術面分析</h4>
    <ul class="llm-bullets">
      <li v-for="(item, idx) in technicalBullets" :key="'t'+idx">{{ item }}</li>
    </ul>

    <template v-if="rightSideBullets.length > 0">
      <h4>🎯 右側買法信號</h4>
      <ul class="llm-bullets right-side">
        <li v-for="(item, idx) in rightSideBullets" :key="'rs'+idx">{{ item }}</li>
      </ul>
    </template>

    <h4>📰 新聞情緒</h4>
    <p v-if="report.news_sentiment"><strong>情緒:</strong> {{ report.news_sentiment }}</p>
    <ul class="llm-bullets">
      <li v-for="(item, idx) in newsSummaryBullets" :key="'n'+idx">{{ item }}</li>
    </ul>

    <template v-if="report.risk_alerts && report.risk_alerts.length > 0">
      <h4 style="color: var(--down)">⚠️ 風險警示</h4>
      <ul class="llm-bullets risk">
        <li v-for="(alert, idx) in report.risk_alerts" :key="'r'+idx">{{ alert }}</li>
      </ul>
    </template>

    <h4 style="color: var(--amber)">💡 投資建議</h4>
    <ul class="llm-bullets recommend">
      <li v-for="(item, idx) in recommendationItems" :key="'rec'+idx">{{ item }}</li>
    </ul>
  </div>
</template>

<style scoped>
.report-meta-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.llm-bullets {
  margin: 0 0 8px 0;
  padding-left: 20px;
  line-height: 1.8;
}
.llm-bullets li {
  margin-bottom: 4px;
}
.llm-bullets.right-side li {
  color: var(--text-secondary);
}
.llm-bullets.risk li {
  color: #fca5a5;
}
.llm-bullets.recommend li {
  color: var(--amber);
  font-weight: 500;
}
</style>
