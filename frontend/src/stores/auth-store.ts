import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, getCurrentUser } from '@/api/auth-api'
import type { User } from '@/types/auth'

/** Check account status every 10 seconds */
const STATUS_CHECK_INTERVAL = 10_000

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => !!token.value)
  const isPremium = computed(() =>
    user.value?.membership_tier === 'premium' || user.value?.is_admin === true
  )

  let statusTimer: ReturnType<typeof setInterval> | null = null

  async function login(username: string, password: string) {
    const response = await apiLogin(username, password)
    token.value = response.access_token
    localStorage.setItem('access_token', response.access_token)
    await fetchUser()
    startStatusCheck()
  }

  async function register(username: string, email: string, password: string) {
    await apiRegister({ username, email, password })
  }

  async function fetchUser() {
    try {
      user.value = await getCurrentUser()
    } catch {
      logout()
    }
  }

  function logout() {
    stopStatusCheck()
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
  }

  /** Periodically verify account is still active */
  function startStatusCheck() {
    stopStatusCheck()
    statusTimer = setInterval(async () => {
      if (!token.value) return stopStatusCheck()
      try {
        const u = await getCurrentUser()
        user.value = u
      } catch (err: any) {
        const status = err.response?.status
        if (status === 401 || status === 403) {
          logout()
          window.location.href = '/login'
        }
      }
    }, STATUS_CHECK_INTERVAL)
  }

  function stopStatusCheck() {
    if (statusTimer) {
      clearInterval(statusTimer)
      statusTimer = null
    }
  }

  // Auto-start check if already logged in
  if (token.value) startStatusCheck()

  return { token, user, isAuthenticated, isPremium, login, register, fetchUser, logout }
})
