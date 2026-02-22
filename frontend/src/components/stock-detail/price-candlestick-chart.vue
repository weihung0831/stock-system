<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import type { EChartsOption } from 'echarts'
import type { DailyPrice } from '@/types/stock'

interface Props {
  prices: DailyPrice[]
}

const props = defineProps<Props>()

/** Calculate simple moving average for given period */
function calcMA(closes: number[], period: number): (number | null)[] {
  return closes.map((_, i) => {
    if (i < period - 1) return null
    const slice = closes.slice(i - period + 1, i + 1)
    return slice.reduce((a, b) => a + b, 0) / period
  })
}

const chartData = computed(() => {
  const sorted = [...props.prices].sort((a, b) =>
    new Date(a.trade_date).getTime() - new Date(b.trade_date).getTime()
  )
  const closes = sorted.map(p => Number(p.close))
  return {
    dates: sorted.map(p => p.trade_date),
    ohlc: sorted.map(p => [Number(p.open), Number(p.close), Number(p.low), Number(p.high)]),
    volumes: sorted.map(p => p.volume),
    ma5: calcMA(closes, 5),
    ma10: calcMA(closes, 10),
    ma20: calcMA(closes, 20),
    ma60: calcMA(closes, 60),
  }
})

const option = computed<EChartsOption>(() => ({
  backgroundColor: 'transparent',
  grid: [
    { left: 60, right: 20, top: 30, height: '60%' },
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
  legend: {
    data: ['MA5', 'MA10', 'MA20', 'MA60'],
    top: 0,
    textStyle: { color: '#8c9ab5', fontSize: 11 },
    itemWidth: 14,
    itemHeight: 2,
  },
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
      name: 'MA5',
      type: 'line',
      data: chartData.value.ma5,
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 1, color: '#f59e0b' },
      xAxisIndex: 0,
      yAxisIndex: 0,
    },
    {
      name: 'MA10',
      type: 'line',
      data: chartData.value.ma10,
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 1, color: '#3b82f6' },
      xAxisIndex: 0,
      yAxisIndex: 0,
    },
    {
      name: 'MA20',
      type: 'line',
      data: chartData.value.ma20,
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 1, color: '#a855f7' },
      xAxisIndex: 0,
      yAxisIndex: 0,
    },
    {
      name: 'MA60',
      type: 'line',
      data: chartData.value.ma60,
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 1, color: '#06b6d4' },
      xAxisIndex: 0,
      yAxisIndex: 0,
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
      const [, open, close, low, high] = candle.value
      let html = `<div style="margin-bottom:4px">${candle.axisValue}</div>`
      html += `<div>開盤: <b>${open}</b></div>`
      html += `<div>收盤: <b>${close}</b></div>`
      html += `<div>最低: <b>${low}</b></div>`
      html += `<div>最高: <b>${high}</b></div>`
      if (vol) html += `<div>成交量: <b>${Number(vol.value).toLocaleString()}</b></div>`
      const maColors: Record<string, string> = { MA5: '#f59e0b', MA10: '#3b82f6', MA20: '#a855f7', MA60: '#06b6d4' }
      params.filter((p: any) => p.seriesName?.startsWith('MA')).forEach((p: any) => {
        if (p.value != null) {
          html += `<div><span style="color:${maColors[p.seriesName]}">${p.seriesName}</span>: <b>${Number(p.value).toFixed(2)}</b></div>`
        }
      })
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
