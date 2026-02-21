<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listUsers, updateUserTier, updateUserEmail, toggleUserActive } from '@/api/admin-api'
import type { User, MembershipTier } from '@/types/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const users = ref<User[]>([])
const loading = ref(false)

/* Inline email editing state */
const editingEmailId = ref<number | null>(null)
const editEmailValue = ref('')

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await listUsers()
  } catch {
    ElMessage.error('無法載入用戶列表')
  } finally {
    loading.value = false
  }
}

function updateUser(updated: User) {
  const idx = users.value.findIndex((u) => u.id === updated.id)
  if (idx >= 0) users.value[idx] = updated
}

async function handleTierChange(user: User, newTier: MembershipTier) {
  try {
    await ElMessageBox.confirm(
      `確定將 ${user.username} 改為${newTier === 'premium' ? '進階會員' : '免費會員'}？`,
      '變更等級',
      { confirmButtonText: '確定', cancelButtonText: '取消', type: 'warning' },
    )
    updateUser(await updateUserTier(user.id, newTier))
    ElMessage.success('等級已更新')
  } catch { /* cancelled */ }
}

function startEditEmail(user: User) {
  editingEmailId.value = user.id
  editEmailValue.value = user.email || ''
}

async function saveEmail(user: User) {
  if (!editEmailValue.value.trim()) {
    ElMessage.warning('請輸入 Email')
    return
  }
  try {
    updateUser(await updateUserEmail(user.id, editEmailValue.value.trim()))
    editingEmailId.value = null
    ElMessage.success('Email 已更新')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail ?? '更新失敗')
  }
}

async function handleToggleActive(user: User) {
  const action = user.is_active ? '停用' : '啟用'
  try {
    await ElMessageBox.confirm(
      `確定${action} ${user.username}？`,
      `${action}帳號`,
      { confirmButtonText: '確定', cancelButtonText: '取消', type: 'warning' },
    )
    updateUser(await toggleUserActive(user.id))
    ElMessage.success(`${user.username} 已${action}`)
  } catch { /* cancelled */ }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="admin-users-page" style="animation: fadeIn 0.3s ease">
    <div class="section-title">
      會員管理
      <span class="badge">{{ users.length }} 位用戶</span>
    </div>

    <div class="card">
      <table class="stock-table">
        <thead>
          <tr>
            <th style="width: 60px">ID</th>
            <th>帳號</th>
            <th>Email</th>
            <th>等級</th>
            <th>角色</th>
            <th style="width: 80px">狀態</th>
            <th style="width: 220px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in users" :key="row.id">
            <td class="rank-num">{{ row.id }}</td>
            <td class="stock-code">{{ row.username }}</td>
            <td>
              <!-- Inline email editing -->
              <div v-if="editingEmailId === row.id" class="inline-edit">
                <input
                  v-model="editEmailValue"
                  class="inline-input"
                  placeholder="輸入 Email"
                  @keyup.enter="saveEmail(row)"
                  @keyup.escape="editingEmailId = null"
                />
                <button class="inline-btn save" @click.stop="saveEmail(row)">✓</button>
                <button class="inline-btn cancel" @click.stop="editingEmailId = null">✕</button>
              </div>
              <span v-else class="editable" @click.stop="startEditEmail(row)">
                {{ row.email || '—' }}
                <svg class="edit-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.12 2.12 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </span>
            </td>
            <td>
              <span class="tier-badge" :class="row.membership_tier">
                {{ row.membership_tier }}
              </span>
            </td>
            <td>
              <span v-if="row.is_admin" class="role-admin">管理員</span>
              <span v-else style="color: var(--text-muted)">用戶</span>
            </td>
            <td>
              <span
                class="status-toggle"
                :style="{ color: row.is_active ? 'var(--up)' : 'var(--down)' }"
                @click.stop="handleToggleActive(row)"
              >
                {{ row.is_active ? '啟用' : '停用' }}
              </span>
            </td>
            <td>
              <button
                v-if="row.membership_tier === 'free'"
                class="action-btn upgrade"
                @click.stop="handleTierChange(row, 'premium')"
              >
                升級 Premium
              </button>
              <button
                v-else
                class="action-btn downgrade"
                @click.stop="handleTierChange(row, 'free')"
              >
                降為免費
              </button>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 40px">
              {{ loading ? '載入中...' : '尚無用戶' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-users-page {
  padding: 24px 28px;
}
.tier-badge {
  display: inline-block;
  font-size: 0.7rem;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-family: var(--font-mono);
}
.tier-badge.premium {
  background: rgba(229, 169, 26, 0.15);
  color: #e5a91a;
}
.tier-badge.free {
  background: rgba(140, 154, 181, 0.15);
  color: #8c9ab5;
}
.role-admin {
  color: #e5a91a;
  font-weight: 600;
  font-size: 0.82rem;
}
.action-btn {
  padding: 4px 14px;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border);
  transition: all 0.15s;
  background: transparent;
}
.action-btn.upgrade {
  color: #e5a91a;
  border-color: rgba(229, 169, 26, 0.3);
}
.action-btn.upgrade:hover {
  background: rgba(229, 169, 26, 0.1);
  border-color: #e5a91a;
}
.action-btn.downgrade {
  color: var(--text-muted);
}
.action-btn.downgrade:hover {
  background: rgba(140, 154, 181, 0.1);
  border-color: var(--text-muted);
}
/* Inline edit */
.editable {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  transition: color 0.15s;
}
.editable:hover {
  color: #e5a91a;
}
.edit-icon {
  opacity: 0;
  transition: opacity 0.15s;
}
.editable:hover .edit-icon {
  opacity: 0.6;
}
.inline-edit {
  display: flex;
  align-items: center;
  gap: 6px;
}
.inline-input {
  background: var(--bg-surface, #1a2236);
  border: 1px solid var(--border, #243049);
  border-radius: 4px;
  color: var(--text);
  padding: 3px 8px;
  font-size: 0.85rem;
  width: 160px;
  outline: none;
}
.inline-input:focus {
  border-color: #e5a91a;
}
.inline-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 2px 4px;
  transition: color 0.15s;
}
.inline-btn.save { color: var(--up, #22c55e); }
.inline-btn.save:hover { color: #4ade80; }
.inline-btn.cancel { color: var(--text-muted); }
.inline-btn.cancel:hover { color: var(--down, #ef4444); }
/* Status toggle */
.status-toggle {
  cursor: pointer;
  font-size: 0.85rem;
  transition: opacity 0.15s;
}
.status-toggle:hover {
  opacity: 0.7;
}
</style>
