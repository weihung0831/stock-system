<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth-store'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    ElMessage.warning('請輸入帳號和密碼')
    return
  }
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    router.push('/')
  } catch {
    ElMessage.error('帳號或密碼錯誤')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">TW Stock Screener</h1>
      <p class="login-subtitle">台灣股市多因子篩選平台</p>
      <el-form @submit.prevent="handleLogin" class="login-form">
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
            v-model="password"
            type="password"
            placeholder="密碼"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          type="warning"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          登入
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #080c14 0%, #151d2e 100%);
}
.login-card {
  width: 400px;
  padding: 48px 40px;
  border-radius: 12px;
  background: rgba(21, 29, 46, 0.9);
  border: 1px solid rgba(229, 169, 26, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}
.login-title {
  text-align: center;
  color: #e5a91a;
  font-family: 'JetBrains Mono', monospace;
  font-size: 24px;
  margin: 0 0 8px;
}
.login-subtitle {
  text-align: center;
  color: #8b95a5;
  font-family: 'Noto Sans TC', sans-serif;
  font-size: 14px;
  margin: 0 0 32px;
}
.login-form {
  display: flex;
  flex-direction: column;
}
.login-btn {
  width: 100%;
  margin-top: 8px;
  background: #e5a91a;
  border-color: #e5a91a;
  color: #080c14;
  font-weight: 600;
}
.login-btn:hover {
  background: #f0b830;
  border-color: #f0b830;
}
</style>
