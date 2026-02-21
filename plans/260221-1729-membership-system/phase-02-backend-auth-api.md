# Phase 02: 後端 Auth API

## Context Links
- [Auth Router](../../backend/app/routers/auth.py) (84 lines)
- [Auth Service](../../backend/app/services/auth_service.py) (84 lines)
- [Dependencies](../../backend/app/dependencies.py) (99 lines)
- [Backend Auth Report](research/researcher-backend-auth-report.md)

## Overview
- **Priority:** P1
- **Status:** completed
- **Description:** 新增 register endpoint、login JWT 嵌入 tier、admin 升降級 API、require_premium dependency

## Key Insights
- `create_access_token(data=dict)` 已接受任意 dict，只需在 login 時多傳 `tier`
- `require_admin` dependency 已存在，`require_premium` 同模式
- Admin 端點放 `/api/admin/users/{user_id}/tier` — 用現有 `require_admin` 保護

## Requirements

### Functional
- `POST /api/auth/register` — 建立 free 會員，回傳 UserResponse
- `POST /api/auth/login` — JWT payload 包含 `tier` 欄位
- `PATCH /api/admin/users/{user_id}/tier` — admin 升降級
- `require_premium` dependency 阻擋 free 用戶

### Non-Functional
- 註冊防重複：username + email 各自 unique check
- 註冊端點無需驗證（public）
- 錯誤訊息使用中文

## Architecture

### Register Endpoint
```python
@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest, db: Session):
    # 1. Check username duplicate
    # 2. Check email duplicate (case-insensitive)
    # 3. hash_password
    # 4. Create User(membership_tier='free')
    # 5. Return UserResponse
```

### Login JWT 更新
```python
# 在 login endpoint 中：
access_token = create_access_token(data={
    "sub": user.username,
    "tier": user.membership_tier
})
```

### Admin Tier API
```python
# 新檔案 backend/app/routers/admin.py
@router.patch("/users/{user_id}/tier")
def update_user_tier(
    user_id: int,
    request: TierUpdateRequest,
    db: Session,
    admin: User = Depends(require_admin)
):
    # Update user.membership_tier
    # Return updated UserResponse
```

### require_premium Dependency
```python
def require_premium(current_user: User = Depends(get_current_user)) -> User:
    if current_user.membership_tier not in ('premium',) and not current_user.is_admin:
        raise HTTPException(403, "需要 Premium 會員")
    return current_user
```

## Related Code Files

### 修改
- `backend/app/routers/auth.py` — 新增 register endpoint, login 嵌入 tier
- `backend/app/dependencies.py` — 新增 require_premium

### 新增
- `backend/app/routers/admin.py` — admin 升降級 API
- `backend/app/schemas/admin.py` — TierUpdateRequest schema

### 可能修改
- `backend/app/routers/__init__.py` — 註冊 admin router

## Implementation Steps

1. **修改 `backend/app/dependencies.py`**
   - 在 `require_admin` 函式後新增 `require_premium` 函式
   - 邏輯：`membership_tier not in ('premium',) and not is_admin` → 403

2. **修改 `backend/app/routers/auth.py`**
   - Import `RegisterRequest` from schemas, `hash_password` from auth_service
   - 新增 `POST /register` endpoint:
     - 檢查 `db.query(User).filter(User.username == request.username).first()`
     - 檢查 `db.query(User).filter(func.lower(User.email) == request.email.lower()).first()`
     - 重複時回 409 Conflict
     - `User(username=, email=request.email.lower().strip(), hashed_password=hash_password(), membership_tier='free')`
     - `db.add()`, `db.commit()`, `db.refresh()`
   - 修改 login endpoint:
     - `create_access_token(data={"sub": user.username, "tier": user.membership_tier})`

3. **新增 `backend/app/schemas/admin.py`**
   ```python
   from pydantic import BaseModel, field_validator

   class TierUpdateRequest(BaseModel):
       membership_tier: str

       @field_validator('membership_tier')
       @classmethod
       def valid_tier(cls, v):
           if v not in ('free', 'premium'):
               raise ValueError('tier 必須為 free 或 premium')
           return v
   ```

4. **新增 `backend/app/routers/admin.py`**
   - `APIRouter(prefix="/api/admin", tags=["admin"])`
   - `PATCH /users/{user_id}/tier`:
     - `Depends(require_admin)` 保護
     - 查詢 user by id，404 if not found
     - 更新 `user.membership_tier`
     - `db.commit()`, `db.refresh(user)`
     - 回傳 `UserResponse`

5. **註冊 admin router**
   - 在 `backend/app/routers/__init__.py` 或 `main.py` 中 `app.include_router(admin.router)`

6. **驗證**
   - 手動測試 register → login → /me → admin tier update 流程

## Todo List
- [x] `require_premium` dependency
- [x] Register endpoint（含重複檢查）
- [x] Login JWT 嵌入 tier
- [x] TierUpdateRequest schema
- [x] Admin tier management endpoint
- [x] 註冊 admin router
- [x] 手動 API 測試

## Success Criteria
- 新用戶可註冊並立即登入
- JWT token 含 tier 欄位
- Admin 可改變用戶 tier
- 重複 username/email 回 409
- require_premium 正確阻擋 free 用戶

## Risk Assessment
- **註冊濫用**：無 CAPTCHA，可能被大量註冊
  - 緩解：暫時可接受，未來加 rate limit on /register
- **JWT tier 過期**：用戶升級後舊 token 仍帶 free tier
  - 緩解：token 有 expire time，升級後用戶重新登入即可；或前端在 profile 頁面提示重新登入

## Security Considerations
- Register endpoint 無需 auth（public）
- Email 正規化防繞過（`lower().strip()`）
- Admin endpoint 用 `require_admin` 保護
- 密碼 hash 後存儲，永不明文

## Next Steps
- Phase 03 需要 `current_user.membership_tier` 來做 tier-aware rate limiting
