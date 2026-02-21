---
title: "會員系統實作"
description: "自助註冊、兩層分級（Free/Premium）、功能限制、前端 UI、管理員 API"
status: completed
priority: P1
effort: 12h
branch: main
tags: [membership, auth, rate-limiting, frontend]
created: 2026-02-21
---

# 會員系統實作計畫

## 概述
為台灣股市多因子篩選平台建立會員系統：自助註冊、Free/Premium 兩層分級、AI 功能用量限制、前端會員 UI、管理員升降級 API。

## 不做的事項
- 付款整合、Email 驗證、忘記密碼、OAuth

## 階段總覽

| Phase | 標題 | 預估工時 | 狀態 |
|-------|------|---------|------|
| 01 | [後端 Model & Schema](phase-01-backend-model-schema.md) | 1.5h | completed |
| 02 | [後端 Auth API](phase-02-backend-auth-api.md) | 2h | completed |
| 03 | [後端 Rate Limiting](phase-03-backend-rate-limiting.md) | 1.5h | completed |
| 04 | [前端 Types & API](phase-04-frontend-types-api.md) | 1h | completed |
| 05 | [前端 Register & Profile](phase-05-frontend-register-profile.md) | 2h | completed |
| 06 | [前端 Membership UI](phase-06-frontend-membership-ui.md) | 2h | completed |
| 07 | [測試](phase-07-testing.md) | 2h | completed |

## 依賴關係
```
Phase 01 → Phase 02 → Phase 03
Phase 01 → Phase 04 → Phase 05 → Phase 06
Phase 01~06 → Phase 07
```

## 關鍵決策
- `membership_tier` 用 Enum('free','premium')，保留 `is_admin` 向下相容
- JWT payload 嵌入 `tier`，減少 DB 查詢
- Rate limiter 在 `check()` 時傳入 tier，不改結構
- 註冊頁 clone login-view 結構，保持視覺一致性
- 前端用 `MembershipTier` type union，不用 enum

## 研究報告
- [Backend Auth Report](research/researcher-backend-auth-report.md)
- [Frontend Rate Limiter Report](research/researcher-frontend-ratelimiter-report.md)
- [Brainstorm Report](../reports/brainstorm-260221-1729-membership-system.md)

## Validation Log

### Session 1 — 2026-02-21
**Trigger:** Initial plan creation validation
**Questions asked:** 4

#### Questions & Answers

1. **[Architecture]** 現有 User 資料庫表新增 email 欄位時，現有用戶怎麼處理？計畫中用 `username@placeholder.com` 作為臨時值。
   - Options: 用 placeholder email (推薦) | email 先設 nullable | 強制更新
   - **Answer:** 用 placeholder email
   - **Rationale:** 保持 email NOT NULL 約束一致性，避免後續代碼需處理 NULL 情況

2. **[Risk]** JWT token 中嵌入 tier 後，用戶被管理員升級後舊 token 仍帶 free。怎麼處理？
   - Options: 用戶重新登入 (推薦) | 強制登出 | DB 查詢 tier
   - **Answer:** 用戶重新登入
   - **Rationale:** 最簡單方案，token 24h 過期自然更新；admin 升級後前端可提示用戶重新登入

3. **[Security]** 註冊端點需要防濫用嗎？計畫中沒有加 rate limit 或 CAPTCHA。
   - Options: 暫不需要 (推薦) | 加簡單 rate limit | 加 CAPTCHA
   - **Answer:** 暫不需要
   - **Rationale:** 內部工具用戶量小，暫時可接受，未來視需要再加

4. **[Scope]** AI chat widget 已經 484 行，加入配額顯示 + 升級 dialog 可能超過 500 行。怎麼處理？
   - Options: 先加再拆 (推薦) | 先拆再加 | 不管行數
   - **Answer:** 先加再拆
   - **Rationale:** 優先完成功能，完成後再模組化拆分，避免先重構延遲交付

#### Confirmed Decisions
- 現有用戶 email: placeholder 方案 — 保持 NOT NULL 約束
- Token 同步: 用戶重新登入 — 最簡單，24h 自然過期
- 註冊安全: 暫不加防護 — 內部工具用戶量小
- Widget 行數: 先加再拆 — 功能優先

#### Action Items
- [ ] Phase 01: ALTER TABLE 使用 `username@placeholder.com` 作為現有用戶預設 email
- [ ] Phase 06: 完成後檢查 ai-assistant-widget.vue 行數，超過 500 行則拆分

#### Impact on Phases
- Phase 01: 確認 email 使用 NOT NULL + placeholder 策略（已符合計畫）
- Phase 06: 新增後續模組化步驟（功能完成後拆分 widget）
