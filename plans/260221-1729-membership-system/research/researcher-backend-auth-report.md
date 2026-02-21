# Backend Auth & Membership Research Report
Date: 2026-02-21

## Current State

### User Model (`backend/app/models/user.py`)
Fields: `id`, `username(50)`, `hashed_password(128)`, `is_admin`, `is_active`, `created_at`/`updated_at` (via TimestampMixin)

**Missing fields to add:**
- `email = Column(String(255), unique=True, nullable=False, index=True)`
- `membership_tier = Column(Enum('free','premium','admin'), default='free', nullable=False)`

Note: `is_admin` can be kept for backward compat OR replaced by `membership_tier == 'admin'`. Recommend keeping both short-term.

---

### Auth Endpoints (`backend/app/routers/auth.py`)
Current:
- `POST /api/auth/login` → returns `TokenResponse`
- `GET /api/auth/me` → returns `UserResponse`

**Register endpoint to add:**
```python
@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    # check duplicate username/email
    # hash_password(request.password)
    # create User(membership_tier='free')
    # return user
```

---

### Password Validation (`backend/app/schemas/auth.py`)
Current patterns:
- `username`: `min_length=3, max_length=50`
- `password`: `min_length=6`

**For RegisterRequest, add stronger validation:**
```python
from pydantic import BaseModel, Field, EmailStr, field_validator

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

---

### JWT Token (`backend/app/services/auth_service.py`)
Current token payload: `{"sub": username, "exp": expire}`

Uses: `python-jose`, `passlib[bcrypt]`, settings from `app.config.settings`
- `settings.JWT_EXPIRE_MINUTES`
- `settings.JWT_SECRET_KEY`
- `settings.JWT_ALGORITHM`

**To include membership_tier, update `create_access_token` call in login:**
```python
access_token = create_access_token(data={
    "sub": user.username,
    "tier": user.membership_tier
})
```
No changes needed to `create_access_token` itself — it accepts arbitrary `Dict[str, Any]`.

**To read tier from token in dependencies** (avoid extra DB query):
```python
tier: str = payload.get("tier", "free")
```

---

### Dependency Injection (`backend/app/dependencies.py`)
Pattern: `HTTPBearer` → `decode_access_token` → DB lookup by username → return `User`

Existing dependency chain:
```
get_current_user → verifies JWT, fetches User from DB
require_admin    → wraps get_current_user, checks is_admin
```

**New tier-aware dependency to add (same pattern as `require_admin`):**
```python
def require_premium(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if current_user.membership_tier not in ('premium', 'admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium membership required"
        )
    return current_user
```

Usage in routers:
```python
@router.get("/ai-report")
def get_ai_report(user: Annotated[User, Depends(require_premium)]):
    ...
```

---

### UserResponse Schema — fields to add:
```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool
    membership_tier: str   # add this

    class Config:
        from_attributes = True
```

---

## Implementation Checklist
1. Add `email` + `membership_tier` columns to `User` model
2. Create Alembic migration
3. Add `RegisterRequest` schema with email + stronger password validation
4. Update `UserResponse` to expose `membership_tier`
5. Update `login` to embed `tier` in JWT payload
6. Add `require_premium` dependency in `dependencies.py`
7. Add `POST /api/auth/register` endpoint
8. Add `email-validator` to requirements if not present (needed for `EmailStr`)

---

## Unresolved Questions
- Should `is_admin` be removed in favor of `membership_tier == 'admin'`? Recommend keeping both for backward compat during transition.
- Membership upgrade flow: who sets `membership_tier='premium'`? Admin-only endpoint or payment webhook?
- Token refresh strategy: current tokens expire per `JWT_EXPIRE_MINUTES`; no refresh token mechanism exists yet.
- Email uniqueness: registration needs case-insensitive email dedup (`lower(email)` or normalize before insert)?
- Rate limiting on `/register` to prevent spam accounts?
