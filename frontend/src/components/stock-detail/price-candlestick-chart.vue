<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import type { EChartsOption } from 'echarts'
import type { DailyPrice } from '@/types/stock'

interface Props {
  prices: DailyPrice[]
}

const props = defineProps<Props>()

const chartData = computed(() => {
  const sorted = [...props.prices].sort((a, b) =>
    new Date(a.trade_date).getTime() - new Date(b.trade_date).getTime()
  )
  return {
    dates: sorted.map(p => p.trade_date),
    ohlc: sorted.map(p => [Number(p.open), Number(p.close), Number(p.low), Number(p.high)]),
    volumes: sorted.map(p => p.volume)
  }
})

const option = computed<EChartsOption>(() => ({
  backgroundColor: 'transparent',
  grid: [
    { left: 60, right: 20, top: 20, height: '62%' },
    { left: 60, right: 20, top: '78%', height: '16%' }
  ],
  xAxis: [
    {
      type: 'category',
      data: chartData.value.dates,
      gridIndex: 0,
      axisLine: { lineStyle: { color: '#243049' } },
      axisLabel: { color: '#556178', fontSize: 11 }
    },
    {
      type: 'category',
      data: chartData.value.dates,
      gridIndex: 1,
      show: false
    }
  ],
  yAxis: [
    {
      scale: true,
      gridIndex: 0,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#1e2a3f' } },
      axisLabel: { color: '#8c9ab5', fontFamily: 'JetBrains Mono', fontSize: 11 }
    },
    {
      scale: true,
      gridIndex: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false }
    }
  ],
  dataZoom: [
    { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 }
  ],
  series: [
    {
      type: 'candlestick',
      data: chartData.value.ohlc,
      xAxisIndex: 0,
      yAxisIndex: 0,
      itemStyle: {
        color: '#22c55e',
        color0: '#ef4444',
        borderColor: '#22c55e',
        borderColor0: '#ef4444'
      }
    },
    {
      type: 'bar',
      data: chartData.value.volumes.map((v, i) => ({
        value: v,
        itemStyle: {
          color: (chartData.value.ohlc[i]?.[1] ?? 0) >= (chartData.value.ohlc[i]?.[0] ?? 0)
            ? '#22c55e40' : '#ef444440'
        }
      })),
      xAxisIndex: 1,
      yAxisIndex: 1
    }
  ],
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
    backgroundColor: '#1e2a3f',
    borderColor: '#243049',
    textStyle: { color: '#e8ecf4', fontFamily: 'JetBrains Mono', fontSize: 12 },
    formatter: (params: any) => {
      const candle = params.find((p: any) => p.seriesType === 'candlestick')
      const vol = params.find((p: any) => p.seriesType === 'bar')
      if (!candle) return ''
      const [open, close, low, high] = candle.data
      let html = `<div style="margin-bottom:4px">${candle.axisValue}</div>`
      html += `<div>開盤: <b>${open}</b></div>`
      html += `<div>收盤: <b>${close}</b></div>`
      html += `<div>最低: <b>${low}</b></div>`
      html += `<div>最高: <b>${high}</b></div>`
      if (vol) html += `<div>成交量: <b>${Number(vol.value).toLocaleString()}</b></div>`
      return html
    }
  }
}))
</script>

<template>
  <div class="kline-chart">
    <VChart :option="option" autoresize />
  </div>
</template>

<style scoped>
.kline-chart {
  width: 100%;
  height: 340px;
}
</style>
