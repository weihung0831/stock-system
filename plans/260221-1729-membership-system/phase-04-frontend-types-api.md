# Phase 04: 前端 Types & API Layer

## Context Links
- [Auth Types](../../frontend/src/types/auth.ts) (15 lines)
- [Auth API](../../frontend/src/api/auth-api.ts) (12 lines)
- [Chat API](../../frontend/src/api/chat-api.ts) (35 lines)
- [Auth Store](../../frontend/src/stores/auth-store.ts) (33 lines)
- [Frontend Report](research/researcher-frontend-ratelimiter-report.md)

## Overview
- **Priority:** P1
- **Status:** completed
- **Description:** 更新 TypeScript 介面、新增 register API function、auth store 加 register action 與 membership computed

## Key Insights
- 現有 `User` interface 只有 id/username/is_admin
- Auth store 用 composition API (setup syntax)，新增 action 很簡單
- Chat API 用獨立 axios instance（不觸發全局 401 redirect）
- Register API 用 auth-api 的 `apiClient`（共用 base client）

## Requirements

### Functional
- `User` interface 加 `email`, `membership_tier`, `is_active`
- `MembershipTier` type alias
- `RegisterRequest` interface
- `register()` API function
- Auth store 加 `register()` action + `isPremium` computed

### Non-Functional
- Strict TypeScript 型別
- 不改變現有 login/logout 流程

## Architecture

### Type 擴展
```typescript
// frontend/src/types/auth.ts
export type MembershipTier = 'free' | 'premium'

export interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
  is_active: boolean
  membership_tier: MembershipTier
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}
```

### API 擴展
```typescript
// frontend/src/api/auth-api.ts — 新增
export async function register(data: RegisterRequest): Promise<User> {
  const { data: user } = await apiClient.post<User>('/auth/register', data)
  return user
}
```

### Store 擴展
```typescript
// auth-store.ts — 新增
const isPremium = computed(() =>
  user.value?.membership_tier === 'premium' || user.value?.is_admin === true
)

async function register(username: string, email: string, password: string) {
  await apiRegister({ username, email, password })
  // 註冊成功後不自動登入，導向 login 頁
}
```

## Related Code Files

### 修改
- `frontend/src/types/auth.ts` — 擴展 User, 新增 MembershipTier, RegisterRequest
- `frontend/src/api/auth-api.ts` — 新增 register function
- `frontend/src/stores/auth-store.ts` — 新增 register action, isPremium computed

### 不動
- `frontend/src/api/chat-api.ts` — 暫不改（Phase 06 才加 quota 顯示）
- `frontend/src/api/client.ts` — 不動

## Implementation Steps

1. **修改 `frontend/src/types/auth.ts`**
   - 新增 `export type MembershipTier = 'free' | 'premium'`
   - `User` interface 加入：
     - `email: string`
     - `is_active: boolean`
     - `membership_tier: MembershipTier`
   - 新增 `export interface RegisterRequest { username: string; email: string; password: string }`

2. **修改 `frontend/src/api/auth-api.ts`**
   - Import `RegisterRequest` from types
   - 新增 function:
     ```typescript
     export async function register(data: RegisterRequest): Promise<User> {
       const { data: user } = await apiClient.post<User>('/auth/register', data)
       return user
     }
     ```

3. **修改 `frontend/src/stores/auth-store.ts`**
   - Import `register as apiRegister` from auth-api, `RegisterRequest` from types
   - 新增 computed:
     ```typescript
     const isPremium = computed(() =>
       user.value?.membership_tier === 'premium' || user.value?.is_admin === true
     )
     ```
   - 新增 action:
     ```typescript
     async function register(username: string, email: string, password: string) {
       await apiRegister({ username, email, password })
     }
     ```
   - 更新 return：加入 `isPremium, register`

4. **TypeScript 編譯驗證**
   ```bash
   cd frontend && npx vue-tsc --noEmit
   ```

## Todo List
- [x] MembershipTier type + User interface 更新
- [x] RegisterRequest interface
- [x] register() API function
- [x] Auth store register action
- [x] Auth store isPremium computed
- [x] TypeScript 編譯通過

## Success Criteria
- `vue-tsc --noEmit` 無錯誤
- `User` interface 含所有新欄位
- `register()` 可被 Vue 元件呼叫
- `isPremium` 正確反映 tier

## Risk Assessment
- **User interface 變更影響範圍**：所有使用 `user.xxx` 的元件可能因缺少新欄位而報 TS 錯誤
  - 緩解：`email` 和 `membership_tier` 是 required，後端 `/me` 已回傳這些欄位（Phase 01 已更新 UserResponse）
- **is_active 新增**：現有程式碼未用到 `is_active`，加入不影響

## Security Considerations
- Token 儲存方式不變（localStorage）
- Register function 不儲存密碼到任何 state

## Next Steps
- Phase 05 使用 `register()` action 建立註冊頁
- Phase 06 使用 `isPremium` computed 控制 UI
