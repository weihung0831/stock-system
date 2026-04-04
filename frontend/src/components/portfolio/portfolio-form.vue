<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { usePortfolioStore } from '@/stores/portfolio-store'
import type { PortfolioCreate } from '@/types/portfolio'
import type { RealtimeItem } from '@/types/portfolio'

const props = defineProps<{
  visible: boolean
  editItem?: RealtimeItem | null
}>()
const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'created'): void
  (e: 'updated'): void
}>()

const store = usePortfolioStore()
const submitting = ref(false)

const form = reactive<PortfolioCreate>({
  stock_id: '',
  cost_price: 0,
  quantity: 1000,
  target_return_pct: 10,
})

const isEdit = ref(false)
const editId = ref(0)

watch(() => props.editItem, (item) => {
  if (item) {
    isEdit.value = true
    editId.value = item.portfolio_id
    form.stock_id = item.stock_id
    form.cost_price = item.cost_price
    form.quantity = item.quantity
    form.target_return_pct = item.target_return_pct
  } else {
    isEdit.value = false
    editId.value = 0
  }
}, { immediate: true })

function resetForm() {
  form.stock_id = ''
  form.cost_price = 0
  form.quantity = 1000
  form.target_return_pct = 10
  isEdit.value = false
  editId.value = 0
}

function handleClose() {
  emit('update:visible', false)
  resetForm()
}

async function handleSubmit() {
  if (!isEdit.value && !form.stock_id.trim()) {
    ElMessage.warning('請輸入股票代號')
    return
  }
  if (form.cost_price <= 0) {
    ElMessage.warning('成本價必須大於 0')
    return
  }
  if (form.quantity <= 0) {
    ElMessage.warning('股數必須大於 0')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await store.updatePortfolio(editId.value, {
        cost_price: form.cost_price,
        quantity: form.quantity,
        target_return_pct: form.target_return_pct,
      })
      ElMessage.success('更新成功')
      emit('updated')
    } else {
      await store.addPortfolio({ ...form, stock_id: form.stock_id.trim() })
      ElMessage.success('新增成功')
      emit('created')
    }
    handleClose()
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    ElMessage.error(detail || (isEdit.value ? '更新失敗' : '新增失敗，請確認股票代號是否正確'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="props.visible"
    :title="isEdit ? '編輯持股' : '新增持股'"
    width="min(440px, 92vw)"
    :before-close="handleClose"
    destroy-on-close
  >
    <el-form label-position="top" @submit.prevent="handleSubmit">
      <el-form-item label="股票代號">
        <el-input
          v-model="form.stock_id"
          placeholder="例：2330"
          maxlength="10"
          :disabled="isEdit"
        />
      </el-form-item>
      <el-form-item label="成本價">
        <el-input-number
          v-model="form.cost_price"
          :min="0"
          :precision="2"
          :step="1"
          controls-position="right"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="股數">
        <el-input-number
          v-model="form.quantity"
          :min="1"
          :step="1000"
          controls-position="right"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="目標報酬率 (%)">
        <el-input-number
          v-model="form.target_return_pct"
          :min="0"
          :max="999"
          :precision="1"
          :step="1"
          controls-position="right"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ isEdit ? '更新' : '新增' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
:deep(.el-dialog) {
  background: var(--bg-card, #1a1f2e);
  border: 1px solid var(--border, #243049);
}

:deep(.el-dialog__title) {
  color: var(--text, #e8ecf4);
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: var(--text-secondary, #8c9ab5);
}

:deep(.el-form-item__label) {
  color: var(--text-secondary, #8c9ab5) !important;
}

:deep(.el-input__wrapper),
:deep(.el-input-number .el-input__wrapper) {
  background: var(--bg-dark, #0e1525);
  border: 1px solid var(--border, #243049);
  box-shadow: none;
}

:deep(.el-input__inner) {
  color: var(--text, #e8ecf4);
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  background: var(--bg-surface, #161d2e);
  border-color: var(--border, #243049) !important;
  color: var(--text-secondary, #8c9ab5);
}

:deep(.el-input-number__decrease:hover),
:deep(.el-input-number__increase:hover) {
  color: var(--amber, #f59e0b);
}

:deep(.el-input-number .el-input__wrapper) {
  border-right: none;
  border-left: none;
}

:deep(.el-input-number) {
  border: 1px solid var(--border, #243049);
  border-radius: 6px;
  overflow: hidden;
}

:deep(.el-input-number .el-input__wrapper),
:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  box-shadow: none !important;
}

:deep(.el-input.is-disabled .el-input__wrapper) {
  background: var(--bg-surface, #161d2e);
  opacity: 0.6;
}

:deep(.el-button--primary) {
  background: var(--amber, #f59e0b);
  border-color: var(--amber, #f59e0b);
  color: #000;
}

:deep(.el-button--default) {
  background: transparent;
  border-color: var(--border, #243049);
  color: var(--text-secondary, #8c9ab5);
}

:deep(.el-dialog__footer) {
  border-top: 1px solid var(--border, #243049);
}
</style>
