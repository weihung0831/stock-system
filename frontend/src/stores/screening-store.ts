import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getResults, runScreening as apiRunScreening } from '@/api/screening-api'
import type { ScoreResult, SectorRankItem } from '@/types/screening'

export const useScreeningStore = defineStore('screening', () => {
  const results = ref<ScoreResult[]>([])
  const topSectors = ref<SectorRankItem[]>([])
  const marketStatus = ref<string>('')
  const latestDate = ref<string>('')
  const updatedAt = ref<string>('')
  const loading = ref(false)

  async function fetchResults(date?: string) {
    loading.value = true
    try {
      const resp = await getResults(date)
      results.value = resp.items ?? []
      topSectors.value = resp.top_sectors ?? []
      marketStatus.value = resp.market_status ?? ''
      if (results.value.length > 0) {
        latestDate.value = results.value[0]?.score_date ?? ''
        updatedAt.value = new Date().toLocaleTimeString('zh-TW', {
          hour: '2-digit', minute: '2-digit',
        })
      }
    } finally {
      loading.value = false
    }
  }

  async function runScreening(threshold: number) {
    loading.value = true
    try {
      await apiRunScreening({ threshold })
      await fetchResults()
    } finally {
      loading.value = false
    }
  }

  return { results, topSectors, marketStatus, latestDate, updatedAt, loading, fetchResults, runScreening }
})
