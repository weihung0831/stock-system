# Phase 03: 後端 Tier-Aware Rate Limiting

## Context Links
- [Chat Rate Limiter](../../backend/app/services/chat_rate_limiter.py) (62 lines)
- [Chat Router](../../backend/app/routers/chat.py) (81 lines)
- [Reports Router](../../backend/app/routers/reports.py) (260 lines)
- [Frontend Rate Limiter Report](research/researcher-frontend-ratelimiter-report.md)

## Overview
- **Priority:** P1
- **Status:** completed
- **Description:** Chat rate limiter 改為 tier-aware，AI Report 生成加每日限制

## Key Insights
- 現有 limiter 是固定 per_minute=3, per_day=20 的 singleton
- 最小變更：`check()` 接受 `tier` 參數，從 `TIER_LIMITS` dict 查限制值
- Report 端點目前無 rate limit，需加入 daily counter（可復用 limiter 模式）
- `check()` 回傳值可擴展含 remaining 資訊供前端顯示

## Requirements

### Functional
- AI Chat 限制：Free 3/min + 10/day, Premium 5/min + 100/day
- AI Report 生成限制：Free 5/day, Premium unlimited
- `check()` 回傳 remaining quota 資訊
- Admin 用戶視同 Premium

### Non-Functional
- 向下相容：`check(user_id)` 不帶 tier 時預設 'free'
- 記憶體效率：不改變現有資料結構

## Architecture

### TIER_LIMITS 配置
```python
CHAT_TIER_LIMITS = {
    'free':    {'per_minute': 3,  'per_day': 10},
    'premium': {'per_minute': 5,  'per_day': 100},
}

REPORT_TIER_LIMITS = {
    'free':    {'per_day': 5},
    'premium': {'per_day': 999999},  # unlimited
}
```

### check() 簽名更新
```python
def check(self, user_id: str, tier: str = 'free') -> tuple[bool, str, dict]:
    # dict = {"daily_remaining": N, "minute_remaining": N}
```

### Report Rate Limiter
新增 `ReportRateLimiter` class（或復用 ChatRateLimiter 只用 daily 部分）。
建議：新增獨立的簡單 class，只做 daily count。

```python
class ReportRateLimiter:
    def check(self, user_id: str, tier: str = 'free') -> tuple[bool, str]:
        limits = REPORT_TIER_LIMITS.get(tier, REPORT_TIER_LIMITS['free'])
        # daily count logic (same pattern as chat daily)
```

## Related Code Files

### 修改
- `backend/app/services/chat_rate_limiter.py` — `check()` 加 tier 參數 + TIER_LIMITS
- `backend/app/routers/chat.py` — 傳 `current_user.membership_tier` 給 limiter
- `backend/app/routers/reports.py` — `generate_stock_report` 加 report rate limit

### 新增
- `backend/app/services/report_rate_limiter.py` — AI Report daily limiter

## Implementation Steps

1. **修改 `backend/app/services/chat_rate_limiter.py`**
   - 在 class 外定義 `CHAT_TIER_LIMITS` dict
   - `__init__` 移除 `per_minute`/`per_day` 參數（改從 TIER_LIMITS 動態取）
   - `check(self, user_id: str, tier: str = 'free') -> tuple[bool, str, dict]`:
     - `limits = CHAT_TIER_LIMITS.get(tier, CHAT_TIER_LIMITS['free'])`
     - 用 `limits['per_day']` 取代 `self.per_day`
     - 用 `limits['per_minute']` 取代 `self.per_minute`
     - 回傳第三個值為 `{"daily_remaining": N, "minute_remaining": N}`
   - Singleton 初始化改為 `ChatRateLimiter()`（無參數）

2. **修改 `backend/app/routers/chat.py`**
   - 第 57 行：`chat_rate_limiter.check(str(current_user.id))` 改為：
     ```python
     tier = current_user.membership_tier if not current_user.is_admin else 'premium'
     allowed, reason, quota = chat_rate_limiter.check(str(current_user.id), tier)
     ```
   - 429 回應 detail 中包含 quota info（可選）

3. **新增 `backend/app/services/report_rate_limiter.py`**
   ```python
   """Per-user daily rate limiter for AI report generation."""
   import logging
   from datetime import date
   from threading import Lock

   logger = logging.getLogger(__name__)

   REPORT_TIER_LIMITS = {
       'free': {'per_day': 5},
       'premium': {'per_day': 999999},
   }

   class ReportRateLimiter:
       def __init__(self):
           self._lock = Lock()
           self._daily_log: dict[str, dict] = {}

       def check(self, user_id: str, tier: str = 'free') -> tuple[bool, str]:
           today = date.today()
           limits = REPORT_TIER_LIMITS.get(tier, REPORT_TIER_LIMITS['free'])
           with self._lock:
               daily = self._daily_log.get(user_id)
               if daily and daily["date"] == today:
                   if daily["count"] >= limits['per_day']:
                       return False, f"已達每日 AI 報告上限 {limits['per_day']} 次"
               else:
                   self._daily_log[user_id] = {"date": today, "count": 0}
               self._daily_log[user_id]["count"] += 1
               remaining = limits['per_day'] - self._daily_log[user_id]["count"]
               logger.info(f"Report rate OK: user={user_id}, remaining={remaining}")
               return True, ""

   report_rate_limiter = ReportRateLimiter()
   ```

4. **修改 `backend/app/routers/reports.py`**
   - Import `report_rate_limiter`
   - 在 `generate_stock_report` endpoint（第 74-156 行）加入：
     ```python
     tier = current_user.membership_tier if not current_user.is_admin else 'premium'
     allowed, reason = report_rate_limiter.check(str(current_user.id), tier)
     if not allowed:
         raise HTTPException(status_code=429, detail=reason)
     ```
   - 放在 stock 驗證之前（第 89 行前）

5. **驗證** — 執行現有 `test_chat_rate_limiter.py` 確認不中斷

## Todo List
- [x] CHAT_TIER_LIMITS 配置
- [x] chat_rate_limiter.check() 加 tier 參數
- [x] check() 回傳 quota info dict
- [x] Chat router 傳 tier
- [x] ReportRateLimiter 新增
- [x] Reports router 加 rate limit
- [x] 現有測試適配

## Success Criteria
- Free 用戶 chat 限制 3/min + 10/day
- Premium 用戶 chat 限制 5/min + 100/day
- Free 用戶 report 限制 5/day
- Premium 用戶 report 無限制
- Admin 視同 Premium
- 現有 rate limiter 測試通過（可能需小幅修改）

## Risk Assessment
- **現有測試中斷**：`test_chat_rate_limiter.py` 可能用固定參數測試
  - 緩解：調整測試傳入 tier 參數
- **check() 簽名變更**：第三回傳值可能影響現有呼叫者
  - 緩解：用 tuple unpacking 相容 `allowed, reason, *_ = check()`

## Security Considerations
- Rate limit 在伺服器端強制執行，前端僅做顯示
- Admin 用戶繞過限制（視同 premium）
- In-memory limiter 重啟後重置（可接受，非安全風險）

## Next Steps
- Phase 04 需要 quota info 在前端顯示剩餘次數
