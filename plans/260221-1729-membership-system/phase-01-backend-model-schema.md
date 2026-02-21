# Phase 01: 後端 Model & Schema 變更

## Context Links
- [User Model](../../backend/app/models/user.py)
- [Auth Schemas](../../backend/app/schemas/auth.py)
- [Requirements](../../backend/requirements.txt)
- [Backend Auth Report](research/researcher-backend-auth-report.md)

## Overview
- **Priority:** P1 (所有後續階段依賴此階段)
- **Status:** completed
- **Description:** 擴展 User model 加入 email 與 membership_tier 欄位，新增 RegisterRequest schema，更新 UserResponse

## Key Insights
- 現有 User model 只有 id/username/hashed_password/is_admin/is_active
- `is_admin` 保留不動，`membership_tier` 獨立管理分級
- SQLAlchemy 直接建表（無 Alembic），需手動 ALTER TABLE 處理現有資料
- `email-validator` 套件是 Pydantic `EmailStr` 的依賴

## Requirements

### Functional
- User model 新增 `email` (unique, indexed) 和 `membership_tier` (enum) 欄位
- RegisterRequest schema 含 username/email/password 驗證
- UserResponse 回傳 email 與 membership_tier
- 密碼強度驗證：>=8 字元、至少一大寫、至少一數字

### Non-Functional
- 向下相容：現有用戶預設 tier='free'
- Email 大小寫不敏感（存入前 lower()）

## Architecture

### User Model 變更
```python
# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, Enum as SAEnum

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    membership_tier = Column(
        SAEnum('free', 'premium', name='membership_tier_enum'),
        default='free', nullable=False, server_default='free'
    )
```

### Schema 變更
```python
# backend/app/schemas/auth.py — 新增
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密碼需包含至少一個大寫字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密碼需包含至少一個數字')
        return v

# UserResponse — 更新
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool
    membership_tier: str

    class Config:
        from_attributes = True
```

## Related Code Files

### 修改
- `backend/app/models/user.py` — 新增 email, membership_tier 欄位
- `backend/app/schemas/auth.py` — 新增 RegisterRequest, 更新 UserResponse
- `backend/requirements.txt` — 新增 `email-validator>=2.0.0`

### 不動
- `backend/app/models/base.py` — TimestampMixin 不變
- `backend/app/database.py` — 不變

## Implementation Steps

1. **在 `requirements.txt` 加入 `email-validator>=2.0.0`**
   - 位置：在 `pydantic-settings` 行後面

2. **安裝依賴**
   ```bash
   pip install email-validator>=2.0.0
   ```

3. **修改 `backend/app/models/user.py`**
   - Import `Enum as SAEnum`
   - 在 `hashed_password` 後加入 `email = Column(String(255), unique=True, nullable=False, index=True)`
   - 在 `is_active` 後加入 `membership_tier = Column(SAEnum('free', 'premium', name='membership_tier_enum'), default='free', nullable=False, server_default='free')`
   - 更新 `__repr__` 包含 tier

4. **修改 `backend/app/schemas/auth.py`**
   - Import `EmailStr` from pydantic, `field_validator` from pydantic
   - 新增 `RegisterRequest` class（含密碼強度驗證）
   - `UserResponse` 新增 `email: str` 和 `membership_tier: str` 欄位

5. **手動 ALTER TABLE（現有 DB）**
   ```sql
   ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT '' UNIQUE;
   ALTER TABLE users ADD COLUMN membership_tier ENUM('free','premium') NOT NULL DEFAULT 'free';
   -- 更新現有用戶 email 為 username@placeholder.com（臨時值）
   UPDATE users SET email = CONCAT(username, '@placeholder.com') WHERE email = '';
   ```

6. **驗證編譯** — 執行 `python -c "from app.models.user import User; from app.schemas.auth import RegisterRequest, UserResponse"` 確保無 import 錯誤

## Todo List
- [x] 加入 email-validator 依賴
- [x] User model 新增 email + membership_tier
- [x] RegisterRequest schema（含密碼驗證）
- [x] UserResponse 新增 email + membership_tier
- [x] ALTER TABLE 遷移腳本
- [x] 編譯驗證

## Success Criteria
- `User` model 含 email + membership_tier 欄位
- `RegisterRequest` 拒絕弱密碼、無效 email
- `UserResponse` 正確序列化新欄位
- 現有測試不中斷

## Risk Assessment
- **DB 遷移風險**：現有用戶無 email，需設定預設值或允許 nullable 過渡期
  - 緩解：使用 `server_default='free'` 和臨時 email 佔位
- **email-validator 版本衝突**：與現有 pydantic 版本可能衝突
  - 緩解：使用 `>=2.0.0` 寬鬆版本約束

## Security Considerations
- 密碼最低 8 字元 + 大寫 + 數字
- Email 存入前 `.lower().strip()` 正規化
- Email 加 unique index 防重複

## Next Steps
- Phase 02 依賴此階段完成後才能實作 register endpoint
- Phase 04 依賴 UserResponse 新欄位
