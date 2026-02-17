<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

interface InstitutionalData {
  trade_date: string
  foreign_net: number
  trust_net: number
  dealer_net: number
}

interface Props {
  data: InstitutionalData[]
}

const props = defineProps<Props>()
const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  if (chartInstance) chartInstance.dispose()

  chartInstance = echarts.init(chartRef.value)

  const dates = props.data.map((d) => d.trade_date)
  const foreignNet = props.data.map((d) => d.foreign_net)
  const trustNet = props.data.map((d) => d.trust_net)
  const dealerNet = props.data.map((d) => d.dealer_net)

  // 檢測是否為手機版
  const isMobile = window.innerWidth <= 768
  const legendTop = isMobile ? -5 : 0
  const gridTop = isMobile ? 55 : 35
  const gridBottom = isMobile ? 60 : 40

  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1e2a3f',
      borderColor: '#243049',
      textStyle: { color: '#e8ecf4', fontSize: 12 },
    },
    legend: {
      data: ['外資', '投信', '自營商'],
      textStyle: { color: '#8c9ab5', fontSize: 11 },
      top: legendTop,
    },
    grid: { left: 60, right: 20, top: gridTop, bottom: gridBottom },
    dataZoom: isMobile ? [] : undefined,
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#243049' } },
      axisLabel: { color: '#556178', fontSize: 10, rotate: 45 },
    },
    yAxis: {
      type: 'value',
      name: '買賣超 (張)',
      nameTextStyle: { color: '#556178', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#1e2a3f' } },
      axisLabel: { color: '#8c9ab5', fontFamily: 'JetBrains Mono', fontSize: 10 },
    },
    series: [
      { name: '外資', type: 'bar', stack: 'total', data: foreignNet, itemStyle: { color: '#e5a91a' } },
      { name: '投信', type: 'bar', stack: 'total', data: trustNet, itemStyle: { color: '#22c55e' } },
      { name: '自營商', type: 'bar', stack: 'total', data: dealerNet, itemStyle: { color: '#6366f1' } },
    ],
  })
}

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

watch(() => props.data, initChart, { deep: true })
</script>

<template>
  <div ref="chartRef" class="chart-box"></div>
</template>

<style scoped>
.chart-box {
  width: 100%;
  height: 360px;
}
</style>
