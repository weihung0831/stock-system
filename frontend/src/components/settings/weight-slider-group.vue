<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useSettingsStore } from '@/stores/settings-store'
import { getAutoWeights } from '@/api/screening-api'

const settingsStore = useSettingsStore()

const chipWeight = ref(settingsStore.weights.chip)
const fundamentalWeight = ref(settingsStore.weights.fundamental)
const technicalWeight = ref(settingsStore.weights.technical)
const autoLoading = ref(false)

const total = computed(() => chipWeight.value + fundamentalWeight.value + technicalWeight.value)

const handleChipChange = (val: number) => {
  chipWeight.value = val
}

const handleFundamentalChange = (val: number) => {
  fundamentalWeight.value = val
}

const handleTechnicalChange = (val: number) => {
  technicalWeight.value = val
}

const updateStore = () => {
  settingsStore.updateWeights({
    chip: chipWeight.value,
    fundamental: fundamentalWeight.value,
    technical: technicalWeight.value,
  })
}

const handleReset = () => {
  chipWeight.value = 40
  fundamentalWeight.value = 30
  technicalWeight.value = 30
  ElMessage.info('已重設為預設權重，請按儲存套用')
}

const handleAutoOptimize = async () => {
  autoLoading.value = true
  try {
    const { weights } = await getAutoWeights()
    chipWeight.value = weights.chip
    fundamentalWeight.value = weights.fundamental
    technicalWeight.value = weights.technical
    ElMessage.info('已自動配置最佳權重，請按儲存套用')
  } catch {
    ElMessage.error('自動配置失敗')
  } finally {
    autoLoading.value = false
  }
}

const handleSave = async () => {
  if (total.value !== 100) {
    ElMessage.error('權重總和必須等於 100%')
    return
  }
  updateStore()
  ElMessage.success('權重設定已儲存')
}

watch(
  () => settingsStore.weights,
  (w) => {
    chipWeight.value = w.chip
    fundamentalWeight.value = w.fundamental
    technicalWeight.value = w.technical
  },
  { deep: true },
)
</script>

<template>
  <div class="weight-sliders">
    <!-- Chip slider -->
    <div class="slider-group">
      <div class="slider-label">
        <span>&#9679; 籌碼面權重</span>
        <span class="slider-val">{{ chipWeight }}%</span>
      </div>
      <div class="slider-wrap">
        <div class="slider-fill chip" :style="{ width: chipWeight + '%' }" />
        <input
          type="range"
          class="slider-input"
          :value="chipWeight"
          min="0"
          max="100"
          step="5"
          @input="handleChipChange(Number(($event.target as HTMLInputElement).value))"
        />
      </div>
    </div>

    <!-- Fundamental slider -->
    <div class="slider-group">
      <div class="slider-label">
        <span>&#9679; 基本面權重</span>
        <span class="slider-val">{{ fundamentalWeight }}%</span>
      </div>
      <div class="slider-wrap">
        <div class="slider-fill fund" :style="{ width: fundamentalWeight + '%' }" />
        <input
          type="range"
          class="slider-input"
          :value="fundamentalWeight"
          min="0"
          max="100"
          step="5"
          @input="handleFundamentalChange(Number(($event.target as HTMLInputElement).value))"
        />
      </div>
    </div>

    <!-- Technical slider -->
    <div class="slider-group">
      <div class="slider-label">
        <span>&#9679; 技術面權重</span>
        <span class="slider-val">{{ technicalWeight }}%</span>
      </div>
      <div class="slider-wrap">
        <div class="slider-fill tech" :style="{ width: technicalWeight + '%' }" />
        <input
          type="range"
          class="slider-input"
          :value="technicalWeight"
          min="0"
          max="100"
          step="5"
          @input="handleTechnicalChange(Number(($event.target as HTMLInputElement).value))"
        />
      </div>
    </div>

    <!-- Total -->
    <div class="slider-total">
      <span>權重總和</span>
      <span class="total-val" :class="{ invalid: total !== 100 }">{{ total }}%</span>
    </div>

    <!-- Actions -->
    <div class="settings-actions">
      <button class="btn-secondary" :disabled="autoLoading" @click="handleAutoOptimize">
        {{ autoLoading ? '計算中...' : '自動配置最佳比例' }}
      </button>
      <button class="btn-secondary" @click="handleReset">重設預設</button>
      <button class="btn-primary" @click="handleSave">儲存設定</button>
    </div>
  </div>
</template>

<style scoped>
.weight-sliders {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.slider-group {
  margin-bottom: 22px;
}

.slider-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.slider-label span {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text, #e8ecf4);
}

.slider-val {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #e5a91a;
  font-size: 0.95rem;
}

.slider-wrap {
  position: relative;
  height: 8px;
  background: var(--bg-surface, #1e2a3f);
  border-radius: 4px;
  overflow: visible;
}

.slider-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.1s;
  pointer-events: none;
}

.slider-fill.chip {
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
}

.slider-fill.fund {
  background: linear-gradient(90deg, #06b6d4, #22d3ee);
}

.slider-fill.tech {
  background: linear-gradient(90deg, #d4960a, #e5a91a);
}

.slider-input {
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 20px;
  transform: translateY(-50%);
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  cursor: pointer;
  margin: 0;
  outline: none;
  border: none;
}

.slider-input:focus {
  outline: none;
}

.slider-input::-webkit-slider-runnable-track {
  -webkit-appearance: none;
  height: 8px;
  background: transparent;
  border: none;
}

.slider-input::-moz-range-track {
  height: 8px;
  background: transparent;
  border: none;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  border: 3px solid #e5a91a;
  cursor: grab;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  transition: box-shadow 0.15s;
  margin-top: -6px;
}

.slider-input::-webkit-slider-thumb:hover {
  box-shadow: 0 0 20px rgba(240, 185, 41, 0.5);
}

.slider-input::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  border: 3px solid #e5a91a;
  cursor: grab;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.slider-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--bg-surface, #1e2a3f);
  border-radius: 6px;
  margin-top: 4px;
}

.slider-total span:first-child {
  font-size: 0.85rem;
  color: var(--text-secondary, #8c9ab5);
}

.total-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.1rem;
  font-weight: 700;
  color: #22c55e;
}

.total-val.invalid {
  color: #ef4444;
}

.settings-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  justify-content: center;
}

.btn-primary {
  padding: 10px 24px;
  background: linear-gradient(135deg, #d4960a, #e5a91a);
  border: none;
  border-radius: 6px;
  color: #0e1525;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.2s;
  font-size: 0.88rem;
  font-family: 'Noto Sans TC', system-ui, sans-serif;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 20px rgba(240, 185, 41, 0.5);
}

.btn-secondary {
  padding: 10px 24px;
  background: var(--bg-surface, #1e2a3f);
  border: 1px solid var(--border, #243049);
  border-radius: 6px;
  color: var(--text, #e8ecf4);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.88rem;
  font-family: 'Noto Sans TC', system-ui, sans-serif;
}

.btn-secondary:hover {
  border-color: #e5a91a;
  color: #e5a91a;
}
</style>
