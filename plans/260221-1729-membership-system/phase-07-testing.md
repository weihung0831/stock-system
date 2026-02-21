# Phase 07: 測試

## Context Links
- [Existing Auth Tests](../../backend/tests/test_auth_service.py)
- [Existing Rate Limiter Tests](../../backend/tests/test_chat_rate_limiter.py)
- [Chat Service Tests](../../backend/tests/test_chat_service.py)

## Overview
- **Priority:** P1
- **Status:** completed
- **Description:** 新增 unit tests 覆蓋所有後端新功能，更新受影響的現有測試

## Key Insights
- 現有 267+ tests 用 pytest
- 需驗證現有測試不中斷（特別是 chat rate limiter 簽名變更）
- 重點測試區域：register validation, tier-aware rate limiting, admin tier API

## Requirements

### Functional
- Register endpoint tests: 成功、重複 username、重複 email、弱密碼、無效 email
- Login tests: JWT 含 tier 欄位
- Admin tier API tests: 成功升級、非 admin 拒絕、無效 tier
- Rate limiter tests: free vs premium 限制差異
- Report rate limiter tests: daily limit by tier
- require_premium dependency tests

### Non-Functional
- 覆蓋率 > 90% for new code
- 不 mock 密碼 hashing（用真實 bcrypt）
- 測試命名清晰：`test_register_success`, `test_register_duplicate_email` 等

## Architecture

### 測試檔案結構
```
backend/tests/
├── test_auth_service.py          # 現有 — 可能需更新
├── test_auth_register.py         # 新增 — register endpoint
├── test_auth_login_tier.py       # 新增 — login JWT tier
├── test_admin_tier_api.py        # 新增 — admin tier management
├── test_chat_rate_limiter.py     # 現有 — 需更新 check() 簽名
├── test_report_rate_limiter.py   # 新增 — report daily limiter
├── test_dependencies.py          # 新增 — require_premium
```

## Related Code Files

### 新增
- `backend/tests/test_auth_register.py`
- `backend/tests/test_auth_login_tier.py`
- `backend/tests/test_admin_tier_api.py`
- `backend/tests/test_report_rate_limiter.py`
- `backend/tests/test_dependencies.py`

### 修改
- `backend/tests/test_chat_rate_limiter.py` — 更新 check() 呼叫簽名
- `backend/tests/test_chat_service.py` — 可能需更新 mock

## Implementation Steps

1. **更新 `backend/tests/test_chat_rate_limiter.py`**
   - `check()` 回傳值從 `(bool, str)` 改為 `(bool, str, dict)`
   - 所有 `allowed, reason = limiter.check(...)` 改為 `allowed, reason, quota = limiter.check(...)`
   - 新增 tier 測試:
     ```python
     def test_free_tier_daily_limit():
         limiter = ChatRateLimiter()
         for i in range(10):
             allowed, reason, quota = limiter.check("user1", tier="free")
             assert allowed
         allowed, reason, quota = limiter.check("user1", tier="free")
         assert not allowed
         assert "10" in reason

     def test_premium_tier_daily_limit():
         limiter = ChatRateLimiter()
         for i in range(10):
             allowed, reason, quota = limiter.check("user2", tier="premium")
             assert allowed
         # Still allowed — premium limit is 100
         allowed, reason, quota = limiter.check("user2", tier="premium")
         assert allowed

     def test_free_tier_minute_limit():
         limiter = ChatRateLimiter()
         for i in range(3):
             allowed, _, _ = limiter.check("user3", tier="free")
             assert allowed
         allowed, reason, _ = limiter.check("user3", tier="free")
         assert not allowed

     def test_quota_info_returned():
         limiter = ChatRateLimiter()
         _, _, quota = limiter.check("user4", tier="free")
         assert "daily_remaining" in quota
         assert quota["daily_remaining"] == 9  # 10 - 1
     ```

2. **新增 `backend/tests/test_auth_register.py`**
   - 使用 TestClient + 測試 DB
   - Test cases:
     ```python
     def test_register_success():
         # POST /api/auth/register with valid data → 201
         # Response contains username, email, membership_tier='free'

     def test_register_duplicate_username():
         # Register twice with same username → 409

     def test_register_duplicate_email():
         # Register twice with same email → 409

     def test_register_duplicate_email_case_insensitive():
         # "Test@Email.com" and "test@email.com" → 409

     def test_register_weak_password_no_uppercase():
         # password="abc12345" → 422

     def test_register_weak_password_no_digit():
         # password="Abcdefgh" → 422

     def test_register_short_password():
         # password="Ab1" → 422

     def test_register_invalid_email():
         # email="not-an-email" → 422

     def test_register_missing_fields():
         # empty body → 422
     ```

3. **新增 `backend/tests/test_auth_login_tier.py`**
   - Test cases:
     ```python
     def test_login_jwt_contains_tier():
         # Register user → login → decode JWT → assert "tier" in payload

     def test_login_jwt_tier_matches_user():
         # Set user tier to 'premium' in DB → login → JWT tier == 'premium'
     ```

4. **新增 `backend/tests/test_admin_tier_api.py`**
   - Test cases:
     ```python
     def test_admin_upgrade_user():
         # Admin PATCH /api/admin/users/{id}/tier {"membership_tier":"premium"} → 200

     def test_admin_downgrade_user():
         # Admin PATCH → tier='free' → 200

     def test_non_admin_cannot_change_tier():
         # Normal user PATCH → 403

     def test_admin_invalid_tier():
         # PATCH tier='gold' → 422

     def test_admin_user_not_found():
         # PATCH /users/99999/tier → 404
     ```

5. **新增 `backend/tests/test_report_rate_limiter.py`**
   - Test cases:
     ```python
     def test_free_report_limit():
         limiter = ReportRateLimiter()
         for i in range(5):
             allowed, _ = limiter.check("user1", "free")
             assert allowed
         allowed, reason = limiter.check("user1", "free")
         assert not allowed

     def test_premium_report_unlimited():
         limiter = ReportRateLimiter()
         for i in range(20):
             allowed, _ = limiter.check("user2", "premium")
             assert allowed

     def test_daily_reset():
         # Mock date change → counter resets
     ```

6. **新增 `backend/tests/test_dependencies.py`**
   - Test cases:
     ```python
     def test_require_premium_allows_premium():
         # Mock user with tier='premium' → passes

     def test_require_premium_allows_admin():
         # Mock user with is_admin=True, tier='free' → passes

     def test_require_premium_blocks_free():
         # Mock user with tier='free', is_admin=False → 403
     ```

7. **執行完整測試**
   ```bash
   cd backend && python -m pytest -v --tb=short
   ```

8. **確認覆蓋率**
   ```bash
   cd backend && python -m pytest --cov=app --cov-report=term-missing
   ```

## Todo List
- [x] 更新 test_chat_rate_limiter.py（check() 簽名）
- [x] test_auth_register.py（9 test cases）
- [x] test_auth_login_tier.py（2 test cases）
- [x] test_admin_tier_api.py（5 test cases）
- [x] test_report_rate_limiter.py（3 test cases）
- [x] test_dependencies.py（3 test cases）
- [x] 完整測試通過 (301 existing + ~26 new)
- [x] 覆蓋率檢查

## Success Criteria
- 所有現有 267+ 測試通過
- 新增 ~26 tests 全部通過
- 新程式碼覆蓋率 > 90%
- 無跳過或 xfail 的測試

## Risk Assessment
- **TestClient DB fixture 差異**：不同測試可能用不同 DB fixture 方式
  - 緩解：先讀現有 conftest.py 理解 fixture 模式再寫
- **bcrypt 測試速度慢**：每次 hash 約 0.2 秒
  - 緩解：可接受，register 測試不多

## Security Considerations
- 測試中不 hardcode 真實密碼或 API keys
- 測試 DB 用獨立 session，不影響正式環境

## Next Steps
- 全部階段完成後更新 `docs/` 文件
- 更新 `docs/project-changelog.md` 記錄會員系統上線
