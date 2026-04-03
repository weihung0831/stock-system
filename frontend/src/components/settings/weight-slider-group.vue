<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useSettingsStore } from '@/stores/settings-store'

const settingsStore = useSettingsStore()

const threshold = ref(settingsStore.threshold)

const handleSave = () => {
  settingsStore.updateThreshold(threshold.value)
  ElMessage.success('設定已儲存')
}

const handleReset = () => {
  threshold.value = 2.5
  ElMessage.info('已重設為預設值，請按儲存套用')
}

watch(
  () => settingsStore.threshold,
  (v) => { threshold.value = v },
)
</script>

<template>
  <div class="weight-sliders">
    <div class="slider-group">
      <div class="slider-label">
        <span>篩選門檻值</span>
        <span class="slider-val">{{ threshold }}</span>
      </div>
      <div class="slider-wrap">
        <div class="slider-fill tech" :style="{ width: (threshold / 10 * 100) + '%' }" />
        <input
          type="range"
          class="slider-input"
          v-model.number="threshold"
          min="0"
          max="10"
          step="0.5"
        />
      </div>
    </div>

    <p class="hint-text">
      動能策略已移除三維權重設定，評分由系統自動計算動能分數。
    </p>

    <!-- Actions -->
    <div class="settings-actions">
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

.slider-group { margin-bottom: 22px; }

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

.hint-text {
  font-size: 0.82rem;
  color: var(--text-muted, #6b7280);
  margin: 8px 0 0;
  line-height: 1.5;
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
