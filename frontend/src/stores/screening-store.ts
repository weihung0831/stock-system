import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getResults, runScreening as apiRunScreening } from '@/api/screening-api'
import type { ScoreResult, ScreeningWeights } from '@/types/screening'

export const useScreeningStore = defineStore('screening', () => {
  const results = ref<ScoreResult[]>([])
  const latestDate = ref<string>('')
  const updatedAt = ref<string>('')
  const loading = ref(false)

  async function fetchResults(date?: string) {
    loading.value = true
    try {
      results.value = await getResults(date)
      if (results.value.length > 0) {
        latestDate.value = results.value[0].score_date
        updatedAt.value = new Date().toLocaleTimeString('zh-TW', {
          hour: '2-digit', minute: '2-digit',
        })
      }
    } finally {
      loading.value = false
    }
  }

  async function runScreening(weights: ScreeningWeights, threshold: number) {
    loading.value = true
    try {
      await apiRunScreening({ weights, threshold })
      await fetchResults()
    } finally {
      loading.value = false
    }
  }

  return { results, latestDate, updatedAt, loading, fetchResults, runScreening }
})
