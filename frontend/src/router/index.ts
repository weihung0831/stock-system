import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/login-view.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/register-view.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/dashboard-view.vue'),
    },
    {
      path: '/stock/:id',
      name: 'stock-detail',
      component: () => import('@/views/stock-detail-view.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/settings-view.vue'),
    },
    {
      path: '/screening',
      name: 'custom-screening',
      component: () => import('@/views/custom-screening-view.vue'),
    },
    {
      path: '/chip-stats',
      name: 'chip-stats',
      component: () => import('@/views/chip-stats-view.vue'),
    },
    {
      path: '/reports',
      name: 'reports',
      component: () => import('@/views/reports-list-view.vue'),
    },
    {
      path: '/history',
      name: 'history-backtest',
      component: () => import('@/views/history-backtest-view.vue'),
    },
    {
      path: '/portfolio',
      name: 'portfolio-monitor',
      component: () => import('@/views/portfolio-monitor-view.vue'),
    },
    {
      path: '/right-side',
      name: 'right-side-screening',
      component: () => import('@/views/right-side-screening-view.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/profile-view.vue'),
    },
    {
      path: '/pricing',
      name: 'pricing',
      component: () => import('@/views/pricing-view.vue'),
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('@/views/admin-users-view.vue'),
    },
  ],
})

// Auth guard: redirect to /login if no token; re-verify account on navigation
router.beforeEach(async (to) => {
  const token = localStorage.getItem('access_token')
  if (!to.meta.public && !token) {
    return { name: 'login' }
  }
  // Re-verify account status on every navigation (non-public pages)
  if (!to.meta.public && token) {
    try {
      const { useAuthStore } = await import('@/stores/auth-store')
      const auth = useAuthStore()
      await auth.fetchUser()
    } catch {
      localStorage.removeItem('access_token')
      return { name: 'login' }
    }
  }
})

export default router
