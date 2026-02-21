# Phase 05: 前端 Register & Profile 頁面

## Context Links
- [Login View](../../frontend/src/views/login-view.vue) (117 lines)
- [Router](../../frontend/src/router/index.ts) (63 lines)
- [App.vue](../../frontend/src/App.vue) (64 lines template)
- [Frontend Report](research/researcher-frontend-ratelimiter-report.md)

## Overview
- **Priority:** P1
- **Status:** completed
- **Description:** 建立註冊頁面（clone login-view 結構）、個人資料頁、路由設定、login 頁連結到 register

## Key Insights
- login-view.vue 117 行，結構簡單：full-vh flex center + card + el-form
- 註冊頁多加 email + confirm password 欄位
- App.vue 用 `isLoginPage` computed 決定是否顯示 layout — 需擴展為 `isPublicPage` 含 register
- Router beforeEach 用 `meta.public` 控制，register 設 `meta: { public: true }`

## Requirements

### Functional
- 註冊頁面：username + email + password + confirm password
- 註冊成功後導向 /login 並顯示成功訊息
- Login 頁底部有「註冊新帳號」連結
- Register 頁底部有「已有帳號？登入」連結
- Profile 頁面顯示：username, email, membership tier, 帳號建立日期
- Profile 從 sidebar 進入（或 header user 區域點擊）

### Non-Functional
- 視覺風格完全一致（dark theme + amber gold）
- 手動前端驗證：all fields required, password match, email format
- 響應式設計（mobile-friendly）

## Architecture

### 頁面結構

**register-view.vue** (~120 lines)
- Clone login-view 結構
- 表單欄位：username (User icon), email (Message icon), password (Lock icon), confirmPassword (Lock icon)
- Submit → authStore.register() → success: router.push('/login') + ElMessage.success
- Error handling: 409 → 「帳號或 Email 已存在」

**profile-view.vue** (~100 lines)
- Card layout 類似 settings-view
- 顯示 user info（從 authStore.user 讀取）
- 會員等級 badge（Premium 金色 / Free 灰色）
- 不做編輯功能（YAGNI）

### Route 設定
```typescript
{ path: '/register', name: 'register', component: () => import('@/views/register-view.vue'), meta: { public: true } },
{ path: '/profile', name: 'profile', component: () => import('@/views/profile-view.vue') },
```

### App.vue 更新
```typescript
const isPublicPage = computed(() => ['/login', '/register'].includes(route.path))
```

## Related Code Files

### 新增
- `frontend/src/views/register-view.vue`
- `frontend/src/views/profile-view.vue`

### 修改
- `frontend/src/router/index.ts` — 新增 /register 和 /profile 路由
- `frontend/src/views/login-view.vue` — 底部加「註冊新帳號」連結
- `frontend/src/App.vue` — `isLoginPage` 改為 `isPublicPage` 含 register

## Implementation Steps

1. **修改 `frontend/src/router/index.ts`**
   - 在 login route 後新增：
     ```typescript
     {
       path: '/register',
       name: 'register',
       component: () => import('@/views/register-view.vue'),
       meta: { public: true },
     },
     ```
   - 在 settings route 後新增：
     ```typescript
     {
       path: '/profile',
       name: 'profile',
       component: () => import('@/views/profile-view.vue'),
     },
     ```

2. **新增 `frontend/src/views/register-view.vue`**
   - `<script setup lang="ts">`: import useRouter, useAuthStore, ElMessage, ref
   - State: username, email, password, confirmPassword, loading (all ref)
   - `handleRegister()`:
     - 驗證 all fields non-empty
     - 驗證 password === confirmPassword → `ElMessage.warning('密碼不一致')`
     - 驗證 password.length >= 8
     - try/catch: `await authStore.register(username, email, password)`
     - 成功: `ElMessage.success('註冊成功，請登入')` + `router.push('/login')`
     - Error 409: `ElMessage.error('帳號或 Email 已被使用')`
     - Other errors: `ElMessage.error('註冊失敗，請稍後再試')`
   - Template: 同 login-view 結構
     - `.register-page` > `.register-card` > title + subtitle + el-form
     - 四個 el-form-item: username (User), email (Message), password (Lock, show-password), confirmPassword (Lock, show-password)
     - el-button type="warning" 「註冊」
     - 底部連結：`<p>已有帳號？<a @click="router.push('/login')">登入</a></p>`
   - Style: 複製 login-view 的 style，改 class name prefix 為 register-*

3. **修改 `frontend/src/views/login-view.vue`**
   - 在 `</el-form>` 後、`</div>` (login-card) 前加：
     ```html
     <p class="login-link">
       還沒有帳號？<a @click="router.push('/register')">註冊新帳號</a>
     </p>
     ```
   - 新增 CSS:
     ```css
     .login-link {
       text-align: center;
       margin-top: 16px;
       font-size: 0.85rem;
       color: var(--text-secondary, #8c9ab5);
     }
     .login-link a {
       color: #e5a91a;
       cursor: pointer;
       font-weight: 500;
     }
     .login-link a:hover {
       text-decoration: underline;
     }
     ```

4. **新增 `frontend/src/views/profile-view.vue`**
   - `<script setup lang="ts">`: import useAuthStore, computed
   - Computed: `user = computed(() => authStore.user)`
   - Template:
     ```html
     <div class="profile-page">
       <div class="card profile-card">
         <div class="profile-header">
           <div class="profile-avatar">{{ user?.username?.charAt(0).toUpperCase() }}</div>
           <div>
             <h2 class="profile-name">{{ user?.username }}</h2>
             <span class="membership-badge" :class="user?.membership_tier">
               {{ user?.membership_tier === 'premium' ? 'Premium' : 'Free' }}
             </span>
           </div>
         </div>
         <div class="profile-info">
           <div class="info-row"><span class="info-label">Email</span><span>{{ user?.email }}</span></div>
           <div class="info-row"><span class="info-label">會員等級</span><span>{{ user?.membership_tier }}</span></div>
           <div class="info-row"><span class="info-label">帳號狀態</span><span>{{ user?.is_active ? '啟用中' : '已停用' }}</span></div>
         </div>
       </div>
     </div>
     ```
   - Style: dark card theme, `.membership-badge.premium` 用 amber 色, `.free` 用 grey

5. **修改 `frontend/src/App.vue`**
   - `isLoginPage` 改名為 `isPublicPage`:
     ```typescript
     const isPublicPage = computed(() => ['/login', '/register'].includes(route.path))
     ```
   - Template: `v-if="isPublicPage"` 取代 `v-if="isLoginPage"`

6. **編譯驗證**
   ```bash
   cd frontend && npm run build
   ```

## Todo List
- [x] Router 新增 /register (public) 和 /profile (protected)
- [x] register-view.vue（表單 + 驗證 + 錯誤處理）
- [x] profile-view.vue（顯示用戶資訊 + badge）
- [x] login-view.vue 加「註冊」連結
- [x] App.vue isLoginPage → isPublicPage
- [x] 視覺一致性檢查
- [x] 編譯通過

## Success Criteria
- /register 可存取（未登入狀態）
- 註冊表單驗證正確（必填、密碼一致、長度）
- 註冊成功導向 /login
- /profile 顯示完整用戶資訊 + tier badge
- Login ↔ Register 互相連結
- Mobile 響應式正常

## Risk Assessment
- **register-view 過大**：含 4 個欄位 + 驗證 + style 可能超 200 行
  - 緩解：style 可抽成共用 auth-page CSS（若超過再處理）
- **App.vue isLoginPage 重名**：其他地方可能引用
  - 緩解：全域搜尋確認只有 App.vue 使用

## Security Considerations
- 前端密碼驗證是 UX 層，後端仍有嚴格驗證
- confirmPassword 不傳到後端
- 註冊成功不自動登入（避免在公用電腦殘留 session）

## Next Steps
- Phase 06 加入 membership badge 到 header/sidebar + feature lock prompts
