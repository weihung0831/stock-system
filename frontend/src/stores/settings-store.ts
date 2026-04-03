import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import apiClient from '@/api/client'

const STORAGE_KEY = 'tw-stock-settings'

function loadFromStorage(): { threshold: number } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* use defaults */ }
  return { threshold: 2.5 }
}

export const useSettingsStore = defineStore('settings', () => {
  const saved = loadFromStorage()
  const threshold = ref(saved.threshold)

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      threshold: threshold.value,
    }))
  }

  watch(threshold, persist)

  /** Sync current settings to backend DB for pipeline use */
  async function syncToBackend() {
    try {
      await apiClient.put('/screening/settings', {
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
      threshold.value = data.threshold
      persist()
    } catch {
      // Backend not available, keep localStorage values
    }
  }

  function updateThreshold(val: number) {
    threshold.value = val
    syncToBackend()
  }

  return { threshold, updateThreshold, loadFromBackend }
})
