import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getPortfolios,
  createPortfolio,
  deletePortfolio,
  updatePortfolio as apiUpdatePortfolio,
  getRealtimeData,
} from '@/api/portfolio-api'
import type { Portfolio, PortfolioCreate, PortfolioUpdate, RealtimeResponse } from '@/types/portfolio'

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolios = ref<Portfolio[]>([])
  const realtimeData = ref<RealtimeResponse | null>(null)
  const loading = ref(false)

  let pollingTimer: ReturnType<typeof setInterval> | null = null

  const totalProfit = computed(() => realtimeData.value?.total_profit_amount ?? 0)
  const totalProfitPct = computed(() => realtimeData.value?.total_profit_pct ?? 0)
  const isMarketOpen = computed(() => realtimeData.value?.is_market_open ?? false)

  async function fetchPortfolios() {
    loading.value = true
    try {
      portfolios.value = await getPortfolios()
    } finally {
      loading.value = false
    }
  }

  async function fetchRealtime() {
    try {
      realtimeData.value = await getRealtimeData()
    } catch {
      // keep previous data on error
    }
  }

  async function addPortfolio(data: PortfolioCreate) {
    loading.value = true
    try {
      const created = await createPortfolio(data)
      portfolios.value.push(created)
      await fetchRealtime()
    } finally {
      loading.value = false
    }
  }

  async function removePortfolio(id: number) {
    loading.value = true
    try {
      await deletePortfolio(id)
      portfolios.value = portfolios.value.filter(p => p.id !== id)
      await fetchRealtime()
    } finally {
      loading.value = false
    }
  }

  async function updatePortfolio(id: number, data: PortfolioUpdate) {
    loading.value = true
    try {
      const updated = await apiUpdatePortfolio(id, data)
      const idx = portfolios.value.findIndex(p => p.id === id)
      if (idx !== -1) portfolios.value[idx] = updated
      await fetchRealtime()
    } finally {
      loading.value = false
    }
  }

  function startPolling() {
    stopPolling()
    fetchRealtime()
    pollingTimer = setInterval(async () => {
      await fetchRealtime()
      if (realtimeData.value && !realtimeData.value.is_market_open && !realtimeData.value.is_realtime) {
        stopPolling()
      }
    }, 5000)
  }

  function stopPolling() {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  return {
    portfolios,
    realtimeData,
    loading,
    totalProfit,
    totalProfitPct,
    isMarketOpen,
    fetchPortfolios,
    fetchRealtime,
    addPortfolio,
    removePortfolio,
    updatePortfolio,
    startPolling,
    stopPolling,
  }
})
