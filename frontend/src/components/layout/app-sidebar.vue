<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth-store'
import HeaderStockSearch from './header-stock-search.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const currentPath = computed(() => route.path)

const emit = defineEmits<{
  (e: 'navigate'): void
}>()

const navSections = computed(() => {
  const sections = [
    {
      label: '總覽',
      items: [
        { path: '/', label: 'Dashboard', icon: 'grid' },
      ],
    },
    {
      label: '分析',
      items: [
        { path: '/screening', label: '自訂篩選', icon: 'filter' },
        { path: '/chip-stats', label: '籌碼統計', icon: 'trend' },
        { path: '/reports', label: 'AI 報告', icon: 'doc' },
        { path: '/history', label: '歷史回測', icon: 'chart' },
        { path: '/right-side', label: '右側買法', icon: 'signal' },
      ],
    },
    {
      label: '系統',
      items: [
        { path: '/settings', label: '設定', icon: 'gear' },
      ],
    },
  ]
  return sections
})

function isActive(path: string) {
  if (path === '/') {
    return currentPath.value === '/' || currentPath.value.startsWith('/stock/')
  }
  return currentPath.value.startsWith(path)
}

function navigate(path: string) {
  router.push(path)
  emit('navigate')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
  emit('navigate')
}

const userInitial = computed(() => {
  const name = authStore.user?.username
  return name ? name.charAt(0).toUpperCase() : 'U'
})

const showUserMenu = ref(false)

function handleMenuAction(action: string) {
  showUserMenu.value = false
  if (action === 'profile') navigate('/profile')
  else if (action === 'admin') navigate('/admin/users')
  else if (action === 'logout') handleLogout()
}
</script>

<template>
  <aside class="sidebar">
    <!-- Brand -->
    <div class="sidebar-brand" @click="navigate('/')">
      <div class="brand-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
          <polyline points="16 7 22 7 22 13" />
        </svg>
      </div>
      <span class="brand-text">Stock Screener</span>
    </div>

    <!-- Mobile search -->
    <div class="sidebar-search">
      <HeaderStockSearch @navigate="emit('navigate')" />
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <template v-for="section in navSections" :key="section.label">
        <div class="nav-section">{{ section.label }}</div>
        <div
          v-for="item in section.items"
          :key="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          @click="navigate(item.path)"
        >
          <!-- Dashboard icon -->
          <svg v-if="item.icon === 'grid'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="9" rx="2" />
            <rect x="14" y="3" width="7" height="5" rx="2" />
            <rect x="14" y="12" width="7" height="9" rx="2" />
            <rect x="3" y="16" width="7" height="5" rx="2" />
          </svg>
          <!-- Filter / Screening icon -->
          <svg v-else-if="item.icon === 'filter'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h16" /><path d="M6 8h12" /><path d="M8 12h8" /><path d="M10 16h4" /><path d="M11 20h2" />
          </svg>
          <!-- Chip / Trend icon -->
          <svg v-else-if="item.icon === 'trend'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
            <polyline points="16 7 22 7 22 13" />
          </svg>
          <!-- AI Report icon -->
          <svg v-else-if="item.icon === 'doc'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4a2 2 0 012-2h8l6 6v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
            <polyline points="14 2 14 8 20 8" />
            <path d="M9 15l2-2 2 2" /><line x1="11" y1="13" x2="11" y2="18" />
          </svg>
          <!-- Backtest / Bar chart icon -->
          <svg v-else-if="item.icon === 'chart'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="13" width="4" height="7" rx="1" />
            <rect x="10" y="8" width="4" height="12" rx="1" />
            <rect x="16" y="3" width="4" height="17" rx="1" />
          </svg>
          <!-- Right-side signal icon -->
          <svg v-else-if="item.icon === 'signal'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 20h.01" /><path d="M7 20v-4" /><path d="M12 20v-8" /><path d="M17 20v-12" /><path d="M22 4v16" />
          </svg>
          <!-- Settings icon -->
          <svg v-else-if="item.icon === 'gear'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12.22 2h-.44a2 2 0 00-2 2v.18a2 2 0 01-1 1.73l-.43.25a2 2 0 01-2 0l-.15-.08a2 2 0 00-2.73.73l-.22.38a2 2 0 00.73 2.73l.15.1a2 2 0 011 1.72v.51a2 2 0 01-1 1.74l-.15.09a2 2 0 00-.73 2.73l.22.38a2 2 0 002.73.73l.15-.08a2 2 0 012 0l.43.25a2 2 0 011 1.73V20a2 2 0 002 2h.44a2 2 0 002-2v-.18a2 2 0 011-1.73l.43-.25a2 2 0 012 0l.15.08a2 2 0 002.73-.73l.22-.39a2 2 0 00-.73-2.73l-.15-.08a2 2 0 01-1-1.74v-.5a2 2 0 011-1.74l.15-.09a2 2 0 00.73-2.73l-.22-.38a2 2 0 00-2.73-.73l-.15.08a2 2 0 01-2 0l-.43-.25a2 2 0 01-1-1.73V4a2 2 0 00-2-2z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          <span>{{ item.label }}</span>
        </div>
      </template>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div class="avatar-wrapper">
        <div class="avatar" @click="showUserMenu = !showUserMenu">{{ userInitial }}</div>
        <!-- Popover menu -->
        <Transition name="menu-fade">
          <div v-if="showUserMenu" class="user-menu">
            <div class="menu-item" @click="handleMenuAction('profile')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" />
              </svg>
              個人資料
            </div>
            <div v-if="authStore.user?.is_admin" class="menu-item" @click="handleMenuAction('admin')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" />
              </svg>
              會員管理
            </div>
            <div class="menu-divider" />
            <div class="menu-item menu-item-danger" @click="handleMenuAction('logout')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              登出
            </div>
          </div>
        </Transition>
      </div>
      <div class="user-info">
        <div class="user-name">{{ authStore.user?.username ?? '使用者' }}</div>
        <div class="user-role">
          <span class="tier-badge" :class="authStore.user?.membership_tier ?? 'free'">
            {{ authStore.user?.is_admin ? '管理員' : authStore.user?.membership_tier === 'premium' ? '進階會員' : '免費會員' }}
          </span>
        </div>
      </div>
    </div>
    <!-- Click outside to close menu -->
    <div v-if="showUserMenu" class="menu-overlay" @click="showUserMenu = false" />
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background: var(--bg-dark, #0e1525);
  border-right: 1px solid var(--border, #243049);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* Brand */
.sidebar-brand {
  padding: 18px 20px;
  border-bottom: 1px solid var(--border, #243049);
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.brand-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #d4960a, #e5a91a);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  color: var(--bg-dark, #0e1525);
  font-size: 0.9rem;
  flex-shrink: 0;
}
.brand-text {
  font-weight: 700;
  font-size: 0.95rem;
  letter-spacing: -0.01em;
  color: var(--text, #e8ecf4);
}

/* Mobile search — only visible on small screens */
.sidebar-search {
  display: none;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border, #243049);
}

@media (max-width: 768px) {
  .sidebar-search {
    display: block;
  }
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}
.nav-section {
  padding: 6px 20px;
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-muted, #556178);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 12px;
}
.nav-section:first-child {
  margin-top: 0;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  cursor: pointer;
  color: var(--text-secondary, #8c9ab5);
  transition: all 0.15s;
  border-left: 3px solid transparent;
  font-size: 0.9rem;
}
.nav-item:hover {
  background: var(--bg-card, #151d2e);
  color: var(--text, #e8ecf4);
}
.nav-item.active {
  color: #e5a91a;
  border-left-color: #e5a91a;
  background: rgba(229, 169, 26, 0.03);
}
.nav-item svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  opacity: 0.7;
}
.nav-item.active svg {
  opacity: 1;
}

/* Footer */
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border, #243049);
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}
.user-info {
  flex: 1;
  min-width: 0;
}
.user-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text, #e8ecf4);
}
.user-role {
  font-size: 0.72rem;
  color: var(--text-muted, #556178);
}
/* Avatar & popover menu */
.avatar-wrapper {
  position: relative;
}
.avatar {
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.avatar:hover {
  box-shadow: 0 0 0 2px rgba(229, 169, 26, 0.4);
}
.user-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  min-width: 160px;
  background: var(--bg-card, #151d2e);
  border: 1px solid var(--border, #243049);
  border-radius: 8px;
  padding: 6px 0;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 100;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  font-size: 0.82rem;
  color: var(--text-secondary, #8c9ab5);
  cursor: pointer;
  transition: all 0.12s;
}
.menu-item:hover {
  background: rgba(229, 169, 26, 0.06);
  color: var(--text, #e8ecf4);
}
.menu-item-danger:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}
.menu-divider {
  height: 1px;
  background: var(--border, #243049);
  margin: 4px 0;
}
.menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 99;
}
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
.tier-badge {
  font-size: 0.65rem;
  padding: 1px 8px;
  border-radius: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.tier-badge.premium {
  background: rgba(229, 169, 26, 0.15);
  color: #e5a91a;
}
.tier-badge.free {
  background: rgba(140, 154, 181, 0.15);
  color: #8c9ab5;
}
</style>
