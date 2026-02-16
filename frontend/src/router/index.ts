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
  ],
})

// Auth guard: redirect to /login if no token
router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (!to.meta.public && !token) {
    return { name: 'login' }
  }
})

export default router
