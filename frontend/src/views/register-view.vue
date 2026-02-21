<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth-store'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function handleRegister() {
  if (!username.value || !email.value || !password.value || !confirmPassword.value) {
    ElMessage.warning('請填寫所有欄位')
    return
  }
  if (password.value !== confirmPassword.value) {
    ElMessage.warning('密碼不一致')
    return
  }
  if (password.value.length < 8) {
    ElMessage.warning('密碼需至少 8 個字元')
    return
  }

  loading.value = true
  try {
    await authStore.register(username.value, email.value, password.value)
    ElMessage.success('註冊成功，請登入')
    router.push('/login')
  } catch (err: any) {
    const status = err?.response?.status
    if (status === 409) {
      ElMessage.error('帳號或 Email 已被使用')
    } else if (status === 422) {
      const detail = err?.response?.data?.detail
      const msg = Array.isArray(detail) ? detail[0]?.msg : detail
      ElMessage.error(msg || '輸入格式不正確')
    } else {
      ElMessage.error('註冊失敗，請稍後再試')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <div class="register-card">
      <h1 class="register-title">TW Stock Screener</h1>
      <p class="register-subtitle">建立新帳號</p>
      <el-form @submit.prevent="handleRegister" class="register-form">
        <el-form-item>
          <el-input
            v-model="username"
            placeholder="帳號"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="email"
            placeholder="Email"
            prefix-icon="Message"
            size="large"
            type="email"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="密碼（至少 8 位）"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="confirmPassword"
            type="password"
            placeholder="確認密碼"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        <el-button
          type="warning"
          size="large"
          :loading="loading"
          class="register-btn"
          @click="handleRegister"
        >
          註冊
        </el-button>
      </el-form>
      <p class="auth-link">
        已有帳號？<a @click="router.push('/login')">登入</a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #080c14 0%, #151d2e 100%);
}
.register-card {
  width: 400px;
  padding: 48px 40px;
  border-radius: 12px;
  background: rgba(21, 29, 46, 0.9);
  border: 1px solid rgba(229, 169, 26, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}
.register-title {
  text-align: center;
  color: #e5a91a;
  font-family: 'JetBrains Mono', monospace;
  font-size: 24px;
  margin: 0 0 8px;
}
.register-subtitle {
  text-align: center;
  color: #8b95a5;
  font-family: 'Noto Sans TC', sans-serif;
  font-size: 14px;
  margin: 0 0 32px;
}
.register-form {
  display: flex;
  flex-direction: column;
}
.register-btn {
  width: 100%;
  margin-top: 8px;
  background: #e5a91a;
  border-color: #e5a91a;
  color: #080c14;
  font-weight: 600;
}
.register-btn:hover {
  background: #f0b830;
  border-color: #f0b830;
}
.auth-link {
  text-align: center;
  margin-top: 16px;
  font-size: 0.85rem;
  color: var(--text-secondary, #8c9ab5);
}
.auth-link a {
  color: #e5a91a;
  cursor: pointer;
  font-weight: 500;
}
.auth-link a:hover {
  text-decoration: underline;
}
</style>
