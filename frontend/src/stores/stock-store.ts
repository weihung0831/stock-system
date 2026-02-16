import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getStocks, getStockPrices } from '@/api/stocks-api'
import type { Stock, DailyPrice } from '@/types/stock'

export const useStockStore = defineStore('stock', () => {
  const stocks = ref<Stock[]>([])
  const selectedStock = ref<Stock | null>(null)
  const prices = ref<DailyPrice[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchStocks(page = 1, limit = 50, search = '') {
    loading.value = true
    try {
      const res = await getStocks({ page, limit, search })
      stocks.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchPrices(stockId: string, startDate?: string, endDate?: string) {
    loading.value = true
    try {
      prices.value = await getStockPrices(stockId, startDate, endDate)
    } finally {
      loading.value = false
    }
  }

  function selectStock(stock: Stock) {
    selectedStock.value = stock
  }

  return { stocks, selectedStock, prices, loading, total, fetchStocks, fetchPrices, selectStock }
})
