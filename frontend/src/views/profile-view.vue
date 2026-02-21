<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth-store'
import { updateEmail, changePassword } from '@/api/auth-api'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const user = computed(() => authStore.user)

/* Email editing */
const editingEmail = ref(false)
const newEmail = ref('')
const emailLoading = ref(false)

function startEditEmail() {
  newEmail.value = user.value?.email ?? ''
  editingEmail.value = true
}

async function saveEmail() {
  if (!newEmail.value.trim()) {
    ElMessage.warning('請輸入 Email')
    return
  }
  emailLoading.value = true
  try {
    const updated = await updateEmail(newEmail.value.trim())
    authStore.user = updated
    editingEmail.value = false
    ElMessage.success('Email 已更新')
  } catch (err: any) {
    const msg = err.response?.data?.detail ?? '更新失敗'
    ElMessage.error(msg)
  } finally {
    emailLoading.value = false
  }
}

/* Password changing */
const showPasswordForm = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordLoading = ref(false)

async function savePassword() {
  if (!currentPassword.value) {
    ElMessage.warning('請輸入目前密碼')
    return
  }
  if (newPassword.value.length < 8) {
    ElMessage.warning('新密碼至少需要 8 個字元')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    ElMessage.warning('兩次輸入的新密碼不一致')
    return
  }
  passwordLoading.value = true
  try {
    await changePassword(currentPassword.value, newPassword.value)
    showPasswordForm.value = false
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    ElMessage.success('密碼已更新')
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      ElMessage.error(detail.map((d: any) => d.msg).join('；'))
    } else {
      ElMessage.error(detail ?? '更新失敗')
    }
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <div class="card profile-card">
      <!-- Header -->
      <div class="profile-header">
        <div class="profile-avatar">{{ user?.username?.charAt(0).toUpperCase() }}</div>
        <div>
          <h2 class="profile-name">{{ user?.username }}</h2>
          <span class="tier-badge" :class="user?.membership_tier">
            {{ user?.is_admin ? '管理員' : user?.membership_tier === 'premium' ? '進階會員' : '免費會員' }}
          </span>
        </div>
      </div>

      <!-- Info rows -->
      <div class="profile-info">
        <!-- Email -->
        <div class="info-row">
          <span class="info-label">Email</span>
          <div v-if="!editingEmail" class="info-value-group">
            <span>{{ user?.email || '未設定' }}</span>
            <button class="btn-edit" @click="startEditEmail">編輯</button>
          </div>
          <div v-else class="edit-group">
            <el-input v-model="newEmail" size="small" placeholder="輸入新 Email" />
            <el-button size="small" type="warning" :loading="emailLoading" @click="saveEmail">儲存</el-button>
            <el-button size="small" @click="editingEmail = false">取消</el-button>
          </div>
        </div>

        <!-- Membership -->
        <div class="info-row">
          <span class="info-label">會員等級</span>
          <span>{{ user?.is_admin ? '管理員' : user?.membership_tier === 'premium' ? '進階會員' : '免費會員' }}</span>
        </div>

        <!-- Account status -->
        <div class="info-row">
          <span class="info-label">帳號狀態</span>
          <span>{{ user?.is_active ? '啟用中' : '已停用' }}</span>
        </div>

        <!-- Password -->
        <div class="info-row">
          <span class="info-label">密碼</span>
          <div v-if="!showPasswordForm">
            <button class="btn-edit" @click="showPasswordForm = true">修改密碼</button>
          </div>
        </div>
      </div>

      <!-- Password form -->
      <div v-if="showPasswordForm" class="password-form">
        <el-input v-model="currentPassword" type="password" placeholder="目前密碼" size="default" show-password />
        <el-input v-model="newPassword" type="password" placeholder="新密碼（至少 8 字元）" size="default" show-password />
        <el-input v-model="confirmPassword" type="password" placeholder="確認新密碼" size="default" show-password @keyup.enter="savePassword" />
        <div class="password-actions">
          <el-button type="warning" :loading="passwordLoading" @click="savePassword">更新密碼</el-button>
          <el-button @click="showPasswordForm = false; currentPassword = ''; newPassword = ''; confirmPassword = ''">取消</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
  animation: fadeIn 0.3s ease;
}
.profile-card {
  padding: 32px;
}
.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}
.profile-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}
.profile-name {
  font-size: 1.3rem;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--text);
}
.tier-badge {
  font-size: 0.7rem;
  padding: 2px 10px;
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
.profile-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}
.info-row:last-child {
  border-bottom: none;
}
.info-label {
  color: var(--text-muted);
  font-weight: 500;
  flex-shrink: 0;
}
.info-value-group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.btn-edit {
  background: none;
  border: 1px solid var(--border, #243049);
  color: #e5a91a;
  padding: 2px 12px;
  border-radius: 6px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-edit:hover {
  background: rgba(229, 169, 26, 0.1);
  border-color: #e5a91a;
}
.edit-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.edit-group .el-input {
  width: 200px;
}
.password-form {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.password-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}
</style>
