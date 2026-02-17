<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStocks } from '@/api/stocks-api'
import type { Stock } from '@/types/stock'

const router = useRouter()

const query = ref('')
const results = ref<Stock[]>([])
const loading = ref(false)
const isOpen = ref(false)
const selectedIndex = ref(0)
const searchRef = ref<HTMLElement | null>(null)

let debounceTimer: number | null = null

// Debounced search
watch(query, (newQuery) => {
  if (debounceTimer !== null) {
    clearTimeout(debounceTimer)
  }

  if (!newQuery.trim()) {
    results.value = []
    isOpen.value = false
    loading.value = false
    return
  }

  loading.value = true
  debounceTimer = window.setTimeout(async () => {
    try {
      const response = await getStocks({ search: newQuery, limit: 8 })
      results.value = response.items
      isOpen.value = true
      selectedIndex.value = 0
    } catch (error) {
      console.error('Search failed:', error)
      results.value = []
    } finally {
      loading.value = false
    }
  }, 300)
})

// Select stock and navigate
const selectStock = (stock: Stock) => {
  router.push(`/stock/${stock.stock_id}`)
  query.value = ''
  results.value = []
  isOpen.value = false
}

// Keyboard navigation
const handleKeydown = (e: KeyboardEvent) => {
  if (!isOpen.value || results.value.length === 0) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % results.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value - 1 + results.value.length) % results.value.length
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (results.value[selectedIndex.value]) {
      selectStock(results.value[selectedIndex.value])
    }
  } else if (e.key === 'Escape') {
    isOpen.value = false
  }
}

// Close dropdown when clicking outside
const handleClickOutside = (e: MouseEvent) => {
  if (searchRef.value && !searchRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (debounceTimer !== null) {
    clearTimeout(debounceTimer)
  }
})
</script>

<template>
  <div class="stock-search" ref="searchRef">
    <div class="search-input-wrapper">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <input
        v-model="query"
        type="text"
        class="search-input"
        placeholder="搜尋股票代碼或名稱..."
        @keydown="handleKeydown"
        @focus="isOpen = query.trim().length > 0 && results.length > 0"
      />
      <div v-if="loading" class="search-spinner">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" opacity="0.25"></circle>
          <path d="M12 2a10 10 0 0 1 10 10" opacity="0.75"></path>
        </svg>
      </div>
    </div>

    <div v-if="isOpen && results.length > 0" class="search-dropdown">
      <div
        v-for="(stock, idx) in results"
        :key="stock.stock_id"
        :class="['search-item', { active: idx === selectedIndex }]"
        @click="selectStock(stock)"
        @mouseenter="selectedIndex = idx"
      >
        <span class="search-item-id">{{ stock.stock_id }}</span>
        <span class="search-item-name">{{ stock.stock_name }}</span>
        <span v-if="stock.industry" class="search-item-industry">{{ stock.industry }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stock-search {
  position: relative;
  width: 100%;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 36px 0 36px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.search-input:focus {
  border-color: var(--amber);
  box-shadow: 0 0 0 2px rgba(229, 169, 26, 0.1);
}

.search-spinner {
  position: absolute;
  right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--amber);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  max-height: 320px;
  overflow-y: auto;
  z-index: 1000;
}

.search-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--border);
}

.search-item:last-child {
  border-bottom: none;
}

.search-item:hover,
.search-item.active {
  background: var(--bg-card-hover);
}

.search-item-id {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--amber);
  font-size: 0.85rem;
  min-width: 60px;
}

.search-item-name {
  color: var(--text);
  font-weight: 500;
  font-size: 0.88rem;
  flex: 1;
}

.search-item-industry {
  font-size: 0.75rem;
  color: var(--text-muted);
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-card);
  white-space: nowrap;
}
</style>
