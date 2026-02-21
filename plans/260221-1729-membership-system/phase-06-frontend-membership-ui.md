# Phase 06: 前端 Membership UI（Badge、Lock Prompt、Quota）

## Context Links
- [App Header](../../frontend/src/components/layout/app-header.vue) (151 lines)
- [App Sidebar](../../frontend/src/components/layout/app-sidebar.vue) (302 lines)
- [AI Assistant Widget](../../frontend/src/components/ai-assistant/ai-assistant-widget.vue) (484 lines)
- [App.vue CSS Variables](../../frontend/src/App.vue) — design tokens

## Overview
- **Priority:** P2
- **Status:** completed
- **Description:** Sidebar footer 顯示 membership badge、AI chat panel 顯示剩餘配額、功能超限時顯示升級提示

## Key Insights
- Sidebar footer 已有 `user-role` div 固定顯示「管理員」— 改為動態顯示 tier
- AI chat widget 429 錯誤已處理（顯示 detail message）— 可加強為 dialog 提示
- Header `.header-meta` 區域可放 user 資訊 + badge（替代「系統運行中」或並列）
- 不需要新的全局 store — 用 authStore.user.membership_tier 就夠

## Requirements

### Functional
- Sidebar footer: user-role 改為動態 tier badge（Free 灰 / Premium 金）
- Sidebar footer: username 點擊導向 /profile
- Header: 右側顯示 user avatar + tier badge（可選，若 header 空間足夠）
- AI Chat: panel header 旁顯示「剩餘 N/10 則」(daily quota)
- Feature lock: 429 回應時顯示升級提示 dialog（而非只是錯誤訊息）

### Non-Functional
- Badge 風格統一：Premium 用 amber (#e5a91a) bg, Free 用 muted bg
- 不引入新 UI 組件庫
- 響應式支援

## Architecture

### Membership Badge Component（可選抽取）
由於 badge 在 sidebar footer 和 profile page 都用到，可抽為小元件。
但只有兩處使用，直接 inline CSS class 即可（YAGNI）。

### 配額顯示
後端 chat rate limiter check() 回傳 quota dict → 但目前 429 才觸發回傳。
**方案 A**（簡單）：前端從 429 response detail 解析剩餘數。
**方案 B**（完整）：新增 `GET /api/chat/quota` endpoint 回傳配額。

選擇 **方案 B**：新增輕量 endpoint，前端 chat panel 開啟時呼叫一次。

### Quota Endpoint
```python
# backend/app/routers/chat.py
@router.get("/quota")
def get_chat_quota(current_user: User = Depends(get_current_user)):
    tier = current_user.membership_tier if not current_user.is_admin else 'premium'
    allowed, reason, quota = chat_rate_limiter.check_quota(str(current_user.id), tier)
    return {"tier": tier, **quota}
```
需在 ChatRateLimiter 加 `check_quota()` 方法（只讀，不計數）。

### Feature Lock Dialog
```html
<el-dialog v-model="showUpgradeDialog" title="功能限制" width="360px">
  <p>您已達到 Free 會員每日使用上限。</p>
  <p>升級 Premium 解鎖更多配額。</p>
  <template #footer>
    <el-button @click="showUpgradeDialog = false">知道了</el-button>
  </template>
</el-dialog>
```

## Related Code Files

### 修改
- `frontend/src/components/layout/app-sidebar.vue` — footer tier badge + profile link
- `frontend/src/components/ai-assistant/ai-assistant-widget.vue` — quota display + upgrade dialog
- `backend/app/routers/chat.py` — 新增 GET /quota endpoint
- `backend/app/services/chat_rate_limiter.py` — 新增 check_quota() 方法

### 新增
- `frontend/src/api/chat-api.ts` — 新增 getChatQuota() function

### 可選修改
- `frontend/src/components/layout/app-header.vue` — 右側 user badge（若空間足夠）

## Implementation Steps

1. **修改 `backend/app/services/chat_rate_limiter.py`**
   - 新增 `check_quota(self, user_id: str, tier: str = 'free') -> dict` 方法：
     - 不計數，只回傳 `{"daily_limit": N, "daily_used": N, "daily_remaining": N, "minute_limit": N}`
     - 讀取 `_daily_log[user_id]` 取已用量

2. **修改 `backend/app/routers/chat.py`**
   - 新增 endpoint:
     ```python
     @router.get("/quota")
     def get_chat_quota(
         current_user: Annotated[User, Depends(get_current_user)]
     ):
         tier = current_user.membership_tier if not current_user.is_admin else 'premium'
         quota = chat_rate_limiter.check_quota(str(current_user.id), tier)
         return {"tier": tier, **quota}
     ```

3. **修改 `frontend/src/api/chat-api.ts`**
   - 新增:
     ```typescript
     export interface ChatQuota {
       tier: string
       daily_limit: number
       daily_used: number
       daily_remaining: number
       minute_limit: number
     }

     export async function getChatQuota(): Promise<ChatQuota> {
       const { data } = await chatClient.get<ChatQuota>('/chat/quota')
       return data
     }
     ```

4. **修改 `frontend/src/components/layout/app-sidebar.vue`**
   - `user-role` div 改為動態:
     ```html
     <div class="user-role">
       <span :class="['tier-badge', authStore.user?.membership_tier]">
         {{ authStore.user?.membership_tier === 'premium' ? 'Premium' : 'Free' }}
       </span>
     </div>
     ```
   - Username 區域包 `<a @click="navigate('/profile')">`:
     ```html
     <div class="user-name" style="cursor: pointer" @click="navigate('/profile')">
       {{ authStore.user?.username ?? '使用者' }}
     </div>
     ```
   - CSS 新增:
     ```css
     .tier-badge {
       font-size: 0.65rem;
       padding: 1px 8px;
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
     ```

5. **修改 `frontend/src/components/ai-assistant/ai-assistant-widget.vue`**
   - Import `getChatQuota, type ChatQuota`
   - 新增 state: `const quota = ref<ChatQuota | null>(null)`
   - 新增 `const showUpgradeDialog = ref(false)`
   - 在 `togglePanel()` 中，開啟時呼叫:
     ```typescript
     if (isOpen.value) {
       getChatQuota().then(q => quota.value = q).catch(() => {})
     }
     ```
   - Panel header 加配額顯示:
     ```html
     <span v-if="quota" class="quota-text">
       {{ quota.daily_remaining }}/{{ quota.daily_limit }}
     </span>
     ```
   - 429 catch 中加 `showUpgradeDialog.value = true`（取代直接 push error message 或並列）
   - 加 el-dialog（upgrade prompt）在 template 末尾

6. **CSS 新增**（ai-assistant-widget.vue）
   ```css
   .quota-text {
     font-size: 0.7rem;
     color: var(--text-muted);
     font-family: var(--font-mono);
   }
   ```

## Todo List
- [x] ChatRateLimiter.check_quota() 方法
- [x] GET /chat/quota endpoint
- [x] getChatQuota() frontend API
- [x] Sidebar footer tier badge
- [x] Sidebar username → profile link
- [x] AI chat panel quota display
- [x] 429 upgrade dialog
- [x] CSS 樣式
- [x] 編譯驗證

## Success Criteria
- Sidebar footer 顯示正確 tier（Free 灰 / Premium 金）
- Username 點擊可到 /profile
- AI chat panel header 顯示「剩餘 N/M」
- 超限後彈出 upgrade dialog
- Mobile 響應式正常

## Risk Assessment
- **ai-assistant-widget.vue 已 484 行**：加入 quota + dialog 可能超過 500 行
  - 緩解：el-dialog 和 quota 邏輯可抽成 composable 或子元件（若超 200 行 script）
- **chat quota endpoint 額外 API 呼叫**：每次開啟 panel 都呼叫
  - 緩解：輕量 endpoint，只讀 in-memory dict，性能可接受

## Security Considerations
- /chat/quota 需要 auth（用 get_current_user）
- 前端 quota 僅做顯示，真正限制在後端

## Next Steps
- Phase 07 測試所有新功能
- 完成後檢查 ai-assistant-widget.vue 行數，超過 500 行則拆分為子元件
<!-- Updated: Validation Session 1 - 先加再拆策略，功能完成後模組化 -->
