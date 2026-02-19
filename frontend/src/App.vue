<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth-store'
import { useSettingsStore } from '@/stores/settings-store'
import AppSidebar from '@/components/layout/app-sidebar.vue'
import AppHeader from '@/components/layout/app-header.vue'
import ScrollToTop from '@/components/shared/scroll-to-top.vue'
import AiAssistantWidget from '@/components/ai-assistant/ai-assistant-widget.vue'

const route = useRoute()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const isLoginPage = computed(() => route.path === '/login')
const sidebarVisible = ref(false)

onMounted(async () => {
  if (authStore.token) {
    await authStore.fetchUser()
    // Load screening settings from backend DB
    await settingsStore.loadFromBackend()
  }
})

// Toggle sidebar on mobile
const toggleSidebar = () => {
  sidebarVisible.value = !sidebarVisible.value
}

// Close sidebar when clicking outside on mobile
const closeSidebar = () => {
  if (window.innerWidth <= 768) {
    sidebarVisible.value = false
  }
}
</script>

<template>
  <!-- Login page: no layout -->
  <router-view v-if="isLoginPage" />

  <!-- App layout with sidebar + header -->
  <el-container v-else class="app-layout">
    <!-- Overlay for mobile -->
    <div v-if="sidebarVisible" class="sidebar-overlay" @click="closeSidebar"></div>

    <!-- Sidebar -->
    <el-aside :class="['app-aside', { 'mobile-visible': sidebarVisible }]" width="240px">
      <AppSidebar @navigate="closeSidebar" />
    </el-aside>

    <el-container>
      <el-header class="app-header-wrapper" height="56px">
        <AppHeader :sidebar-visible="sidebarVisible" @toggle-sidebar="toggleSidebar" />
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <ScrollToTop />
    <AiAssistantWidget />
  </el-container>
</template>

<style>
/* ========== CSS Variables (from prototype) ========== */
:root {
  --bg-deepest: #080c14;
  --bg-dark: #0e1525;
  --bg-card: #151d2e;
  --bg-card-hover: #1a2338;
  --bg-surface: #1e2a3f;
  --border: #243049;
  --border-light: #2e3d5a;
  --amber: #e5a91a;
  --amber-glow: #f0b92980;
  --amber-dim: #d4960a;
  --up: #22c55e;
  --up-bg: #22c55e18;
  --down: #ef4444;
  --down-bg: #ef444418;
  --text: #e8ecf4;
  --text-secondary: #8c9ab5;
  --text-muted: #556178;
  --sidebar-w: 240px;
  --header-h: 56px;
  --radius: 10px;
  --radius-sm: 6px;
  --radius-lg: 14px;
  --font-sans: 'Noto Sans TC', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --shadow-card: 0 2px 12px #0004, 0 0 0 1px var(--border);
  --shadow-glow: 0 0 20px var(--amber-glow);
}

/* ========== RESET & BASE ========== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 14px; -webkit-font-smoothing: antialiased; }
body {
  font-family: var(--font-sans);
  background: var(--bg-deepest);
  color: var(--text);
  overflow-x: hidden;
}
a { color: var(--amber); text-decoration: none; }
input, select, button { font-family: inherit; font-size: inherit; }

.app-layout { min-height: 100vh; }

.app-aside {
  transition: width 0.3s;
  overflow: hidden;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
}

.app-header-wrapper { padding: 0 !important; }

.app-main {
  background: var(--bg-deepest);
  min-height: calc(100vh - var(--header-h));
  overflow-y: auto;
  padding: 0 !important;
}

/* Element Plus dark overrides */
.el-menu { border-right: none !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-light); }

/* ========== Shared utility classes ========== */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.section-title {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title .badge {
  font-size: 0.7rem;
  background: var(--amber);
  color: var(--bg-dark);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 700;
}

/* ========== Shared table styles (prototype) ========== */
.stock-table { width: 100%; border-collapse: collapse; }
.stock-table thead { background: var(--bg-surface); }
.stock-table th {
  padding: 10px 14px;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
  transition: color 0.15s;
}
.stock-table th:hover { color: var(--text-secondary); }
.stock-table td {
  padding: 11px 14px;
  border-bottom: 1px solid var(--border);
  font-size: 0.88rem;
  white-space: nowrap;
}
.stock-table tbody tr { transition: background 0.15s; cursor: pointer; }
.stock-table tbody tr:hover { background: var(--bg-card-hover); }
.stock-table tbody tr:last-child td { border-bottom: none; }
.stock-code { font-family: var(--font-mono); font-weight: 600; color: var(--amber); }
.stock-name { color: var(--text); font-weight: 500; }
.score-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 48px;
  text-align: center;
}
.score-high { background: var(--up-bg); color: var(--up); }
.score-mid { background: #eab30818; color: #eab308; }
.score-low { background: var(--down-bg); color: var(--down); }
.rank-num { font-family: var(--font-mono); font-weight: 700; color: var(--text-muted); width: 30px; text-align: center; }
.rank-1 { color: var(--amber); font-size: 1.05rem; }
.rank-2 { color: #c0c0c0; }
.rank-3 { color: #cd7f32; }
.price-change.up { color: var(--up); }
.price-change.down { color: var(--down); }
.total-score { font-weight: 700; font-family: var(--font-mono); font-size: 1rem; color: var(--amber); }

/* ========== Stat cards ========== */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  transition: border-color 0.2s, transform 0.2s;
}
.stat-card:hover { border-color: var(--border-light); transform: translateY(-2px); }
.stat-card .stat-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 500; letter-spacing: 0.03em; margin-bottom: 8px; }
.stat-card .stat-value { font-size: 1.6rem; font-weight: 700; font-family: var(--font-mono); letter-spacing: -0.03em; }
.stat-card .stat-change { font-size: 0.78rem; margin-top: 4px; font-family: var(--font-mono); }
.stat-card .stat-change.up { color: var(--up); }
.stat-card .stat-change.down { color: var(--down); }

/* ========== Category tabs ========== */
.category-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.cat-tab {
  padding: 7px 16px;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  transition: all 0.2s;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}
.cat-tab:hover { border-color: var(--border-light); color: var(--text); }
.cat-tab.active { background: var(--amber); border-color: var(--amber); color: var(--bg-dark); }
.cat-tab .cat-count {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  padding: 1px 6px;
  border-radius: 10px;
  background: #0002;
  min-width: 20px;
  text-align: center;
}
.cat-tab.active .cat-count { background: #0003; }
.cat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* ========== Dashboard grid ========== */
.dash-grid { display: grid; grid-template-columns: 1fr 380px; gap: 20px; margin-top: 20px; }
.dash-grid .card { padding: 20px; }

/* ========== Alert list ========== */
.alert-item { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.alert-item:last-child { border-bottom: none; }
.alert-badge {
  font-size: 0.7rem;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-family: var(--font-mono);
  background: var(--up-bg);
  color: var(--up);
  white-space: nowrap;
}
.alert-text { font-size: 0.85rem; color: var(--text-secondary); flex: 1; }
.alert-text strong { color: var(--text); font-weight: 600; }

/* ========== Back button ========== */
.btn-back { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: var(--bg-surface);
  border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text-secondary);
  cursor: pointer; font-size: 0.82rem; transition: all 0.15s; margin-bottom: 16px; font-family: var(--font-sans); }
.btn-back:hover { border-color: var(--amber); color: var(--amber); }

/* ========== Stock detail ========== */
.detail-header { display: flex; align-items: flex-end; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.detail-header .stock-title { font-size: 1.8rem; font-weight: 900; letter-spacing: -0.03em; }
.detail-header .stock-code-lg { font-family: var(--font-mono); font-size: 1rem; color: var(--amber); font-weight: 600; }
.detail-header .stock-price { font-family: var(--font-mono); font-size: 2rem; font-weight: 700; }
.detail-header .stock-price-change { font-family: var(--font-mono); font-size: 1rem; padding: 4px 12px;
  border-radius: 6px; font-weight: 600; }
.detail-header .stock-price-change.up { background: var(--up-bg); color: var(--up); }
.detail-header .stock-price-change.down { background: var(--down-bg); color: var(--down); }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.detail-grid .card { padding: 20px; }
.chart-title { font-size: 0.85rem; font-weight: 600; margin-bottom: 12px; color: var(--text-secondary); }

/* ========== Factor score rings ========== */
.factor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.factor-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 20px; text-align: center; transition: transform 0.2s, border-color 0.2s; }
.factor-card:hover { transform: translateY(-2px); border-color: var(--border-light); }
.factor-card .factor-label { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 12px; font-weight: 500; }
.factor-ring { position: relative; width: 100px; height: 100px; margin: 0 auto 12px; }
.factor-ring svg { transform: rotate(-90deg); width: 100%; height: 100%; }
.factor-ring .ring-bg { fill: none; stroke: var(--border); stroke-width: 6; }
.factor-ring .ring-fill { fill: none; stroke-width: 6; stroke-linecap: round; transition: stroke-dashoffset 0.8s ease; }
.factor-ring .ring-value { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-size: 1.4rem; font-weight: 700; }

/* ========== LLM report panel ========== */
.llm-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; }
.llm-panel .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.llm-panel .panel-header h3 { font-size: 1rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.llm-panel .panel-date { font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono); }
.llm-content { font-size: 0.9rem; line-height: 1.75; color: var(--text-secondary); }
.llm-content h4 { color: var(--text); font-size: 0.95rem; margin: 16px 0 8px; font-weight: 700; }
.llm-content h4:first-child { margin-top: 0; }
.llm-content strong { color: var(--text); font-weight: 600; }
.llm-content .highlight { color: var(--amber); font-weight: 600; }
.llm-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; margin-right: 4px; }
.llm-tag.buy { background: var(--up-bg); color: var(--up); }
.llm-tag.hold { background: #eab30815; color: #eab308; }
.llm-tag.sell { background: var(--down-bg); color: var(--down); }
.llm-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px;
  font-size: 0.75rem; font-weight: 600; background: rgba(229, 169, 26, 0.07); color: var(--amber); border: 1px solid rgba(229, 169, 26, 0.19); }

/* ========== Sector tag ========== */
.sector-tag { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 12px;
  font-size: 0.75rem; font-weight: 600; border: 1px solid var(--border); background: var(--bg-surface); color: var(--text-secondary); }
.sector-tag .cat-dot { width: 8px; height: 8px; border-radius: 50%; }

/* ========== Page animation ========== */
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

/* Sidebar overlay for mobile */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  backdrop-filter: blur(2px);
}

/* ========== Responsive ========== */
@media (max-width: 1024px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-grid { grid-template-columns: 1fr; }
  .detail-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  /* Hide sidebar by default on mobile */
  .app-aside {
    position: fixed;
    left: -240px;
    top: 0;
    z-index: 1000;
    transition: left 0.3s ease;
    height: 100vh;
  }

  /* Show sidebar when mobile-visible */
  .app-aside.mobile-visible {
    left: 0;
  }

  /* Show overlay when sidebar is visible */
  .mobile-visible ~ .sidebar-overlay,
  .sidebar-overlay {
    display: block;
  }

  .stat-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
  .stat-card { padding: 14px; }
  .stat-card .stat-value { font-size: 1.3rem; }
  .category-tabs { gap: 6px; flex-wrap: nowrap; overflow-x: auto; -webkit-overflow-scrolling: touch; padding-bottom: 6px; }
  .card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .stock-table { min-width: 700px; }
  .dash-grid { gap: 16px; }
  .detail-header { gap: 12px; }
  .detail-header .stock-title { font-size: 1.4rem; }
  .detail-header .stock-price { font-size: 1.5rem; }
  .factor-grid { grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .factor-card { padding: 14px; }
  .factor-ring { width: 80px; height: 80px; }
  .factor-ring .ring-value { font-size: 1.1rem; }
  .llm-panel { padding: 16px; }
  .llm-content { font-size: 0.85rem; }
}
</style>
