<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

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
}

const props = defineProps<Props>()
const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value || !props.data.length) return
  if (chartInstance) chartInstance.dispose()

  chartInstance = echarts.init(chartRef.value)

  const stockNames = props.data.map((d) => `${d.stock_id} ${d.stock_name}`)
  const return5d = props.data.map((d) => d.return_5d)
  const return10d = props.data.map((d) => d.return_10d)
  const return20d = props.data.map((d) => d.return_20d)

  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e2a3f',
      borderColor: '#243049',
      textStyle: { color: '#e8ecf4', fontSize: 12 },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((param: any) => {
          const sign = param.value >= 0 ? '+' : ''
          result += `${param.marker} ${param.seriesName}: ${sign}${param.value.toFixed(2)}%<br/>`
        })
        return result
      },
    },
    legend: {
      data: ['5日報酬', '10日報酬', '20日報酬'],
      textStyle: { color: '#8c9ab5', fontSize: 11 },
      top: 4,
    },
    grid: { left: 60, right: 40, top: 40, bottom: 100 },
    xAxis: {
      type: 'category',
      data: stockNames,
      axisLine: { lineStyle: { color: '#243049' } },
      axisLabel: { color: '#556178', fontSize: 10, rotate: 45 },
    },
    yAxis: {
      type: 'value',
      name: '報酬率 (%)',
      nameTextStyle: { color: '#556178', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#1e2a3f' } },
      axisLabel: { color: '#8c9ab5', fontFamily: 'JetBrains Mono', fontSize: 10 },
    },
    series: [
      {
        name: '5日報酬',
        type: 'line',
        data: return5d,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#e5a91a', width: 2 },
        itemStyle: { color: '#e5a91a' },
      },
      {
        name: '10日報酬',
        type: 'line',
        data: return10d,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#22c55e', width: 2 },
        itemStyle: { color: '#22c55e' },
      },
      {
        name: '20日報酬',
        type: 'line',
        data: return20d,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#6366f1', width: 2 },
        itemStyle: { color: '#6366f1' },
      },
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
