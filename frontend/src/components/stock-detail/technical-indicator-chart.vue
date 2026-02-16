<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import type { EChartsOption } from 'echarts'
import type { DailyPrice } from '@/types/stock'

interface Props {
  prices: DailyPrice[]
}

const props = defineProps<Props>()

const calculateKD = (prices: DailyPrice[]) => {
  const k: number[] = []
  const d: number[] = []
  let prevK = 50
  let prevD = 50

  prices.forEach((_, i) => {
    if (i < 8) {
      k.push(50)
      d.push(50)
      return
    }
    const period = prices.slice(i - 8, i + 1)
    const close = Number(period[period.length - 1].close)
    const lowest = Math.min(...period.map(p => Number(p.low)))
    const highest = Math.max(...period.map(p => Number(p.high)))
    const rsv = ((close - lowest) / (highest - lowest)) * 100
    const kVal = (2 / 3) * prevK + (1 / 3) * rsv
    const dVal = (2 / 3) * prevD + (1 / 3) * kVal
    k.push(kVal)
    d.push(dVal)
    prevK = kVal
    prevD = dVal
  })
  return { k, d }
}

const calculateRSI = (prices: DailyPrice[], period = 14) => {
  const rsi: (number | null)[] = []
  for (let i = 0; i < prices.length; i++) {
    if (i < period) { rsi.push(null); continue }
    let gains = 0
    let losses = 0
    for (let j = i - period + 1; j <= i; j++) {
      const change = Number(prices[j].close) - Number(prices[j - 1].close)
      if (change > 0) gains += change
      else losses += Math.abs(change)
    }
    const avgGain = gains / period
    const avgLoss = losses / period
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
    rsi.push(100 - (100 / (1 + rs)))
  }
  return rsi
}

const chartData = computed(() => {
  const sorted = [...props.prices].sort((a, b) =>
    new Date(a.trade_date).getTime() - new Date(b.trade_date).getTime()
  )
  const kd = calculateKD(sorted)
  const rsi = calculateRSI(sorted)
  return {
    dates: sorted.map(p => p.trade_date),
    k: kd.k,
    d: kd.d,
    rsi
  }
})

const option = computed<EChartsOption>(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#1e2a3f',
    borderColor: '#243049',
    textStyle: { color: '#e8ecf4', fontSize: 11 }
  },
  legend: {
    data: ['K', 'D', 'RSI'],
    textStyle: { color: '#8c9ab5', fontSize: 11 },
    top: 0,
    right: 0
  },
  grid: { left: 60, right: 20, top: 30, bottom: 30 },
  xAxis: {
    type: 'category',
    data: chartData.value.dates,
    axisLine: { lineStyle: { color: '#243049' } },
    axisLabel: { color: '#556178', fontSize: 10 }
  },
  yAxis: {
    min: 0,
    max: 100,
    axisLine: { show: false },
    splitLine: { lineStyle: { color: '#1e2a3f' } },
    axisLabel: { color: '#8c9ab5', fontFamily: 'JetBrains Mono', fontSize: 10 }
  },
  dataZoom: [
    { type: 'inside', start: 60, end: 100 }
  ],
  series: [
    {
      name: 'K',
      type: 'line',
      data: chartData.value.k,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1.5, color: '#f0b429' }
    },
    {
      name: 'D',
      type: 'line',
      data: chartData.value.d,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1.5, color: '#8b5cf6' }
    },
    {
      name: 'RSI',
      type: 'line',
      data: chartData.value.rsi,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1.5, color: '#22d3ee' },
      markLine: {
        silent: true,
        data: [
          { yAxis: 70, lineStyle: { color: '#ef4444', type: 'dashed' } },
          { yAxis: 30, lineStyle: { color: '#22c55e', type: 'dashed' } }
        ]
      }
    }
  ]
}))
</script>

<template>
  <div class="indicator-chart">
    <VChart :option="option" autoresize />
  </div>
</template>

<style scoped>
.indicator-chart {
  width: 100%;
  height: 220px;
}
</style>
