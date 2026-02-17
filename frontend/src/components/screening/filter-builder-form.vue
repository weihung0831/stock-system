<script setup lang="ts">
import { reactive, computed, onMounted } from 'vue'
import { useSectorTagsStore } from '@/stores/sector-tags-store'

interface FilterForm {
  industry: string
  min_total_score: number
  min_chip_score: number
  min_fundamental_score: number
  min_technical_score: number
  min_close_price: number | undefined
  max_close_price: number | undefined
}

const emit = defineEmits<{
  (e: 'filter-change', filters: FilterForm): void
}>()

const sectorTagsStore = useSectorTagsStore()

const form = reactive<FilterForm>({
  industry: '全部',
  min_total_score: 0,
  min_chip_score: 0,
  min_fundamental_score: 0,
  min_technical_score: 0,
  min_close_price: undefined,
  max_close_price: undefined,
})

onMounted(() => {
  if (sectorTagsStore.tags.length === 0) {
    sectorTagsStore.fetchTags()
  }
})

const industries = computed(() => [
  { label: '全部', value: '全部' },
  ...sectorTagsStore.tags.map((t) => ({ label: t.name, value: t.name })),
])

function handleSubmit() {
  const filters = { ...form }
  if (filters.industry === '全部') {
    delete (filters as any).industry
  }
  emit('filter-change', filters)
}

function handleReset() {
  form.industry = '全部'
  form.min_total_score = 0
  form.min_chip_score = 0
  form.min_fundamental_score = 0
  form.min_technical_score = 0
  form.min_close_price = undefined
  form.max_close_price = undefined
}
</script>

<template>
  <div class="filter-form card">
    <div class="filter-grid">
      <!-- Industry select -->
      <div class="filter-item">
        <label class="filter-label">產業類別</label>
        <select v-model="form.industry" class="filter-select">
          <option v-for="item in industries" :key="item.value" :value="item.value">
            {{ item.label }}
          </option>
        </select>
      </div>

      <!-- Score sliders -->
      <div class="filter-item">
        <label class="filter-label">總分最低值</label>
        <div class="range-group">
          <input type="range" v-model.number="form.min_total_score" min="0" max="100" step="5" class="filter-range" />
          <span class="range-value">{{ form.min_total_score }}</span>
        </div>
      </div>

      <div class="filter-item">
        <label class="filter-label">籌碼分數最低值</label>
        <div class="range-group">
          <input type="range" v-model.number="form.min_chip_score" min="0" max="100" step="5" class="filter-range" />
          <span class="range-value">{{ form.min_chip_score }}</span>
        </div>
      </div>

      <div class="filter-item">
        <label class="filter-label">基本面分數最低值</label>
        <div class="range-group">
          <input type="range" v-model.number="form.min_fundamental_score" min="0" max="100" step="5" class="filter-range" />
          <span class="range-value">{{ form.min_fundamental_score }}</span>
        </div>
      </div>

      <div class="filter-item">
        <label class="filter-label">技術面分數最低值</label>
        <div class="range-group">
          <input type="range" v-model.number="form.min_technical_score" min="0" max="100" step="5" class="filter-range" />
          <span class="range-value">{{ form.min_technical_score }}</span>
        </div>
      </div>

      <!-- Price range -->
      <div class="filter-item">
        <label class="filter-label">股價區間</label>
        <div class="price-range">
          <input
            type="number"
            v-model.number="form.min_close_price"
            min="0"
            step="10"
            placeholder="最低價"
            class="filter-input"
          />
          <span class="range-sep">~</span>
          <input
            type="number"
            v-model.number="form.max_close_price"
            min="0"
            step="10"
            placeholder="最高價"
            class="filter-input"
          />
        </div>
      </div>
    </div>

    <!-- Buttons -->
    <div class="filter-actions">
      <button class="btn btn-primary" @click="handleSubmit">執行篩選</button>
      <button class="btn btn-ghost" @click="handleReset">重設</button>
    </div>
  </div>
</template>

<style scoped>
.filter-form {
  padding: 20px 24px;
  margin-bottom: 20px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px 28px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.03em;
}

.filter-select,
.filter-input {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--bg-surface);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 0.88rem;
  outline: none;
  transition: border-color 0.15s;
}
.filter-select:focus,
.filter-input:focus {
  border-color: var(--amber);
}
.filter-select option {
  background: var(--bg-card);
  color: var(--text);
}

/* Range slider */
.range-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-range {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}
.filter-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--amber);
  border: 2px solid var(--bg-card);
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.filter-range::-webkit-slider-thumb:hover {
  box-shadow: 0 0 8px var(--amber-glow);
}
.filter-range::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--amber);
  border: 2px solid var(--bg-card);
  cursor: pointer;
}

.range-value {
  min-width: 32px;
  text-align: right;
  font-family: var(--font-mono);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--amber);
}

/* Price range */
.price-range {
  display: flex;
  align-items: center;
  gap: 10px;
}
.price-range .filter-input {
  width: 120px;
}
.range-sep {
  color: var(--text-muted);
  font-weight: 500;
}

/* Buttons */
.filter-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.btn {
  padding: 8px 24px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s;
  font-family: var(--font-sans);
}
.btn-primary {
  background: var(--amber);
  color: var(--bg-dark);
  border-color: var(--amber);
}
.btn-primary:hover {
  background: var(--amber-dim);
  box-shadow: 0 0 12px var(--amber-glow);
}
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--border);
}
.btn-ghost:hover {
  border-color: var(--border-light);
  color: var(--text);
}

/* Number input hide spinners */
.filter-input[type='number']::-webkit-inner-spin-button,
.filter-input[type='number']::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.filter-input[type='number'] {
  -moz-appearance: textfield;
}

@media (max-width: 768px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
