import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { ScreeningWeights } from '@/types/screening'
import apiClient from '@/api/client'

const STORAGE_KEY = 'tw-stock-settings'

function loadFromStorage(): { weights: ScreeningWeights; threshold: number } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* use defaults */ }
  return { weights: { chip: 40, fundamental: 35, technical: 25 }, threshold: 2.5 }
}

export const useSettingsStore = defineStore('settings', () => {
  const saved = loadFromStorage()
  const weights = ref<ScreeningWeights>(saved.weights)
  const threshold = ref(saved.threshold)

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      weights: weights.value,
      threshold: threshold.value,
    }))
  }

  watch([weights, threshold], persist, { deep: true })

  /** Sync current settings to backend DB for pipeline use */
  async function syncToBackend() {
    try {
      await apiClient.put('/screening/settings', {
        weights: weights.value,
        threshold: threshold.value,
      })
    } catch (e) {
      console.warn('Failed to sync settings to backend:', e)
    }
  }

  /** Load settings from backend DB (on app init) */
  async function loadFromBackend() {
    try {
      const { data } = await apiClient.get('/screening/settings')
      weights.value = data.weights
      threshold.value = data.threshold
      persist()
    } catch {
      // Backend not available, keep localStorage values
    }
  }

  function updateWeights(newWeights: ScreeningWeights) {
    weights.value = newWeights
    syncToBackend()
  }

  function updateThreshold(val: number) {
    threshold.value = val
    syncToBackend()
  }

  return { weights, threshold, updateWeights, updateThreshold, loadFromBackend }
})
