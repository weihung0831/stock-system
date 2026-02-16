<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSectorTagsStore } from '@/stores/sector-tags-store'
import { ElMessage, ElMessageBox } from 'element-plus'

const emit = defineEmits<{
  (e: 'sector-change', sector: string): void
}>()

const store = useSectorTagsStore()
const activeSector = ref('全部')

// Dialog state
const dialogVisible = ref(false)
const editingTag = ref<{ id?: number; name: string; color: string; keywords: string } | null>(null)

onMounted(() => {
  store.fetchTags()
})

const handleSectorChange = (sector: string) => {
  activeSector.value = sector
  emit('sector-change', sector)
}

// Open dialog for creating a new tag
function openCreateDialog() {
  editingTag.value = { name: '', color: '#9ca3af', keywords: '' }
  dialogVisible.value = true
}

// Open dialog for editing an existing tag
function openEditDialog(tag: { id: number; name: string; color: string; keywords: string }) {
  editingTag.value = { ...tag }
  dialogVisible.value = true
}

// Save (create or update)
async function handleSave() {
  if (!editingTag.value || !editingTag.value.name.trim()) {
    ElMessage.warning('請輸入標籤名稱')
    return
  }
  try {
    if (editingTag.value.id) {
      await store.editTag(editingTag.value.id, {
        name: editingTag.value.name,
        color: editingTag.value.color,
        keywords: editingTag.value.keywords,
      })
      ElMessage.success('標籤已更新')
    } else {
      await store.addTag({
        name: editingTag.value.name,
        color: editingTag.value.color,
        keywords: editingTag.value.keywords || editingTag.value.name,
        sort_order: store.tags.length + 1,
      })
      ElMessage.success('標籤已新增')
    }
    dialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失敗')
  }
}

// Delete tag
async function handleDelete(tag: { id: number; name: string }) {
  try {
    await ElMessageBox.confirm(`確定要刪除標籤「${tag.name}」嗎？`, '刪除確認', {
      confirmButtonText: '刪除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await store.removeTag(tag.id)
    if (activeSector.value === tag.name) {
      activeSector.value = '全部'
      emit('sector-change', '全部')
    }
    ElMessage.success('標籤已刪除')
  } catch {
    // User cancelled
  }
}
</script>

<template>
  <div class="sector-filter-tabs">
    <!-- 全部 tab (always present) -->
    <button
      :class="['tab-button', { active: activeSector === '全部' }]"
      @click="handleSectorChange('全部')"
    >
      全部
    </button>

    <!-- Dynamic tags -->
    <div
      v-for="tag in store.tags"
      :key="tag.id"
      class="tag-wrapper"
      @contextmenu.prevent="openEditDialog(tag)"
    >
      <button
        :class="['tab-button', { active: activeSector === tag.name }]"
        @click="handleSectorChange(tag.name)"
      >
        <span class="tag-dot" :style="{ backgroundColor: tag.color }"></span>
        {{ tag.name }}
      </button>
      <span class="tag-actions">
        <button class="action-btn edit-btn" title="編輯" @click.stop="openEditDialog(tag)">✎</button>
        <button class="action-btn delete-btn" title="刪除" @click.stop="handleDelete(tag)">✕</button>
      </span>
    </div>

    <!-- Add button -->
    <button class="tab-button add-btn" @click="openCreateDialog">＋</button>
  </div>

  <!-- Create/Edit Dialog -->
  <el-dialog
    v-model="dialogVisible"
    :title="editingTag?.id ? '編輯標籤' : '新增標籤'"
    width="400px"
    destroy-on-close
  >
    <el-form v-if="editingTag" label-width="80px">
      <el-form-item label="名稱">
        <el-input v-model="editingTag.name" placeholder="例：半導體" maxlength="20" />
      </el-form-item>
      <el-form-item label="顏色">
        <el-color-picker v-model="editingTag.color" />
      </el-form-item>
      <el-form-item label="關鍵字">
        <el-input
          v-model="editingTag.keywords"
          placeholder="用於比對產業欄位，例：半導體"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSave">儲存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.sector-filter-tabs {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-wrap: wrap;
  align-items: center;
}

.tag-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.tag-wrapper:hover .tag-actions {
  display: flex;
}

.tag-actions {
  position: absolute;
  top: -8px;
  right: -8px;
  display: none;
  gap: 2px;
}

.action-btn {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}

.edit-btn {
  background: #3b82f6;
  color: #fff;
}

.delete-btn {
  background: #ef4444;
  color: #fff;
}

.tab-button {
  padding: 8px 20px;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #9ca3af;
  font-size: 14px;
  font-family: 'Noto Sans TC', sans-serif;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tab-button:hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(229, 169, 26, 0.3);
}

.tab-button.active {
  background-color: rgba(229, 169, 26, 0.15);
  border-color: #e5a91a;
  color: #e5a91a;
}

.tag-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.add-btn {
  border-style: dashed;
  color: #6b7280;
  padding: 8px 16px;
}

.add-btn:hover {
  color: #e5a91a;
  border-color: rgba(229, 169, 26, 0.5);
}
</style>
