<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

interface MarginData {
  trade_date: string
  margin_balance: number
  short_balance: number
}

interface Props {
  data: MarginData[]
}

const props = defineProps<Props>()
const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  if (chartInstance) chartInstance.dispose()

  chartInstance = echarts.init(chartRef.value)

  const dates = props.data.map((d) => d.trade_date)
  const marginBalance = props.data.map((d) => d.margin_balance)
  const shortBalance = props.data.map((d) => d.short_balance)

  // 檢測是否為手機版
  const isMobile = window.innerWidth <= 768
  const legendTop = isMobile ? -5 : 0
  const gridTop = isMobile ? 55 : 35

  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e2a3f',
      borderColor: '#243049',
      textStyle: { color: '#e8ecf4', fontSize: 12 },
    },
    legend: {
      data: ['融資餘額', '融券餘額'],
      textStyle: { color: '#8c9ab5', fontSize: 11 },
      top: legendTop,
    },
    grid: { left: 60, right: 60, top: gridTop, bottom: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#243049' } },
      axisLabel: { color: '#556178', fontSize: 10, rotate: 45 },
    },
    yAxis: [
      {
        type: 'value',
        name: '融資餘額',
        nameTextStyle: { color: '#ef4444', fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#1e2a3f' } },
        axisLabel: { color: '#8c9ab5', fontFamily: 'JetBrains Mono', fontSize: 10 },
      },
      {
        type: 'value',
        name: '融券餘額',
        nameTextStyle: { color: '#22c55e', fontSize: 11 },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { color: '#8c9ab5', fontFamily: 'JetBrains Mono', fontSize: 10 },
      },
    ],
    series: [
      {
        name: '融資餘額',
        type: 'line',
        yAxisIndex: 0,
        data: marginBalance,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#ef4444', width: 2 },
        itemStyle: { color: '#ef4444' },
      },
      {
        name: '融券餘額',
        type: 'line',
        yAxisIndex: 1,
        data: shortBalance,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#22c55e', width: 2 },
        itemStyle: { color: '#22c55e' },
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
