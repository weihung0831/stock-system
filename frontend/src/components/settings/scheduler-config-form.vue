<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/api/client'
import { useSettingsStore } from '@/stores/settings-store'

const emit = defineEmits<{ triggerPipeline: [] }>()
const settingsStore = useSettingsStore()

const isEnabled = ref(true)
const scheduledTime = ref('16:30')
const volumeMultiplier = ref(settingsStore.threshold)
const saveLoading = ref(false)

const fetchSettings = async () => {
  try {
    const { data } = await apiClient.get('/scheduler/settings')
    isEnabled.value = data.enabled
    const h = String(data.hour).padStart(2, '0')
    const m = String(data.minute).padStart(2, '0')
    scheduledTime.value = `${h}:${m}`
  } catch {
    // Use defaults
  }
}

const handleToggle = () => {
  isEnabled.value = !isEnabled.value
}

const handleSaveSettings = async () => {
  saveLoading.value = true
  try {
    const [h, m] = scheduledTime.value.split(':').map(Number)
    await apiClient.put('/scheduler/settings', {
      enabled: isEnabled.value,
      hour: h,
      minute: m,
    })
    settingsStore.updateThreshold(volumeMultiplier.value)
    ElMessage.success('排程設定已儲存')
  } catch {
    ElMessage.error('儲存失敗')
  } finally {
    saveLoading.value = false
  }
}

onMounted(fetchSettings)
</script>

<template>
  <div class="scheduler-form">
    <div class="form-row">
      <div class="row-label">
        每日自動執行
        <small>收盤後自動抓取資料與評分</small>
      </div>
      <div class="toggle" :class="{ on: isEnabled }" @click="handleToggle" />
    </div>

    <div class="form-row">
      <div class="row-label">
        Pipeline 啟動時間
        <small>建議 16:30 後確保資料更新</small>
      </div>
      <input
        v-model="scheduledTime"
        type="time"
        class="time-input"
        :disabled="!isEnabled"
      />
    </div>

    <div class="form-row">
      <div class="row-label">
        週量篩選倍數
        <small>週成交量 > 均值 × 此倍數</small>
      </div>
      <input
        v-model.number="volumeMultiplier"
        type="number"
        class="threshold-input"
        step="0.1"
        min="1"
        max="10"
      />
    </div>

    <!-- Actions -->
    <div class="form-actions">
      <button class="btn-secondary" :disabled="saveLoading" @click="handleSaveSettings">
        {{ saveLoading ? '儲存中...' : '儲存設定' }}
      </button>
      <button class="btn-primary" @click="emit('triggerPipeline')">手動執行 Pipeline</button>
    </div>

  </div>
</template>

<style scoped>
.scheduler-form {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--border, #243049);
}

.row-label {
  font-size: 0.88rem;
  color: var(--text-secondary, #8c9ab5);
}

.row-label small {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted, #556178);
  margin-top: 2px;
}

/* Toggle */
.toggle {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background: var(--border, #243049);
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}
.toggle.on { background: #e5a91a; }
.toggle::after {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: white;
  top: 3px;
  left: 3px;
  transition: transform 0.2s;
}
.toggle.on::after { transform: translateX(20px); }

/* Inputs */
.time-input,
.threshold-input {
  background: var(--bg-dark, #0e1525);
  border: 1px solid var(--border, #243049);
  border-radius: 6px;
  padding: 7px 12px;
  color: var(--text, #e8ecf4);
  font-family: 'JetBrains Mono', monospace;
  width: 140px;
  text-align: center;
  font-size: 0.88rem;
  outline: none;
}
.time-input:focus,
.threshold-input:focus { border-color: #e5a91a; }
.time-input:disabled { opacity: 0.5; cursor: not-allowed; }

.select-input {
  background: var(--bg-dark, #0e1525);
  border: 1px solid var(--border, #243049);
  border-radius: 6px;
  padding: 7px 12px;
  color: var(--text, #e8ecf4);
  font-family: 'JetBrains Mono', monospace;
  width: 200px;
  text-align: left;
  font-size: 0.85rem;
  outline: none;
  cursor: pointer;
}
.select-input:focus { border-color: #e5a91a; }

/* Actions */
.form-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 16px;
  margin-top: auto;
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
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 0 20px rgba(240, 185, 41, 0.5); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

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
.btn-secondary:hover { border-color: #e5a91a; color: #e5a91a; }
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }

</style>
