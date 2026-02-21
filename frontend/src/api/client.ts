import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect to login on 401/403 (skip auth endpoints for 401)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url ?? ''
    const status = error.response?.status
    if (status === 401 && !url.startsWith('/auth/')) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    // 403 = account deactivated or no permission (skip login/register only)
    const isAuthMutation = url.startsWith('/auth/login') || url.startsWith('/auth/register')
    if (status === 403 && !isAuthMutation) {
      const detail = error.response?.data?.detail ?? ''
      if (detail === 'Inactive user account') {
        localStorage.removeItem('access_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default apiClient
