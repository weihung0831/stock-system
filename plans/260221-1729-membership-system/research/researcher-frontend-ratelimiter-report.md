# Frontend Auth & Rate Limiter Research Report
Date: 2026-02-21

---

## 1. Auth Store (`auth-store.ts`) — Current Pattern

**State:** `token` (localStorage-persisted), `user: User | null`, `isAuthenticated` (computed)

**Methods:** `login()`, `fetchUser()`, `logout()`

**What to add for membership:**
- `user.membership_tier` field (e.g. `'free' | 'pro' | 'premium'`)
- `register(username, password, email)` action → call new POST `/api/auth/register`
- Computed `isProOrAbove = computed(() => ['pro','premium'].includes(user.value?.membership_tier ?? ''))`
- No need to change token/localStorage strategy — already correct

---

## 2. TypeScript Interfaces (`auth.ts`) — What to Extend

Current `User` interface is minimal (id, username, is_admin).

**Add to `User`:**
```ts
export type MembershipTier = 'free' | 'pro' | 'premium'

export interface User {
  id: number
  username: string
  email: string            // add
  is_admin: boolean
  membership_tier: MembershipTier  // add
  membership_expires_at: string | null  // add (ISO datetime or null)
}
```

**Add new interfaces:**
```ts
export interface RegisterRequest {
  username: string
  email: string
  password: string
}
```

No other interfaces needed — `LoginRequest` and `TokenResponse` remain unchanged.

---

## 3. Login Page Patterns to Reuse for Register Page

`login-view.vue` is 117 lines — register page can mirror structure exactly.

**Reusable patterns:**
- Layout: `.login-page` → full-vh flex center, dark gradient bg `#080c14 → #151d2e`
- Card: `.login-card` 400px, `rgba(21,29,46,0.9)`, gold border `rgba(229,169,26,0.2)`
- Title: `#e5a91a`, JetBrains Mono font
- `el-form` with `@submit.prevent`, `el-form-item` + `el-input` with `prefix-icon`
- `el-button type="warning"` full-width, gold bg `#e5a91a`
- `ElMessage.warning/error` for validation feedback
- `loading` ref pattern for async submit

**Register-page additions over login:**
- Add `email` field: `el-input type="email" prefix-icon="Message"`
- Add password confirm field
- Link back to `/login` — use `router.push('/login')`
- Link from login page to `/register`

---

## 4. Rate Limiter (`chat_rate_limiter.py`) — Making It Tier-Aware

**Current:** singleton `ChatRateLimiter(per_minute=3, per_day=20)` — flat for all users.

**Architecture:** In-memory dict keyed by `user_id`. Two stores: `_minute_log` (sliding window) + `_daily_log` (daily count reset).

**Tier-aware strategy — minimal change:**

Option A (simplest): per-tier limits passed at `check()` call time.
```python
TIER_LIMITS = {
    'free':    {'per_minute': 3,  'per_day': 20},
    'pro':     {'per_minute': 10, 'per_day': 100},
    'premium': {'per_minute': 20, 'per_day': 500},
}

def check(self, user_id: str, tier: str = 'free') -> tuple[bool, str]:
    limits = TIER_LIMITS.get(tier, TIER_LIMITS['free'])
    # use limits['per_minute'] and limits['per_day'] instead of self.per_minute/per_day
```

This avoids storing tier in limiter state — caller (route handler) passes tier from JWT/DB user object. No structural refactor needed.

**Where tier comes from:** `current_user.membership_tier` from FastAPI dependency injection.

---

## 5. Router — Patterns for New Routes

**Current guard:** `router.beforeEach` checks `localStorage.getItem('access_token')`. Routes use `meta: { public: true }` to bypass.

**Add routes:**
```ts
{ path: '/register', name: 'register', component: () => import('@/views/register-view.vue'), meta: { public: true } },
{ path: '/profile',  name: 'profile',  component: () => import('@/views/profile-view.vue') },
```

**No guard changes needed** — profile is protected by default (no `meta.public`), register is public.

**Optional tier guard** (if needed for gated features): extend `meta` type:
```ts
declare module 'vue-router' {
  interface RouteMeta { public?: boolean; requireTier?: MembershipTier }
}
```
Then check in `beforeEach` via auth store.

---

## 6. Element Plus Component Patterns in Project

| Component | Usage in login-view |
|---|---|
| `el-form` | `@submit.prevent` binding |
| `el-form-item` | wrapper for each field |
| `el-input` | `v-model`, `prefix-icon` (string name), `size="large"`, `show-password`, `@keyup.enter` |
| `el-button` | `type="warning"`, `size="large"`, `:loading` binding |
| `ElMessage` | imported directly, `.warning()` / `.error()` calls |

No `el-form` ref / `validate()` rules used — validation is manual (check empty, then try/catch). Register page should follow the same simple pattern.

---

## Summary

- Auth store needs `register()` action + membership fields on `User`
- TypeScript: add `MembershipTier`, `email`, `membership_expires_at` to `User`; add `RegisterRequest`
- Register view: clone login-view structure, add email + confirm-password fields
- Rate limiter: pass `tier` at `check()` call, use `TIER_LIMITS` dict — no class refactor
- Router: two new routes (`/register` public, `/profile` protected), no guard logic changes needed

---

## Unresolved Questions

1. Does membership tier live in JWT payload or requires DB lookup on each request?
2. Is `membership_expires_at` enforced server-side or just informational on frontend?
3. Should `/profile` allow tier upgrade (payment flow) or just display current tier?
4. Redis vs in-memory for rate limiter if multi-process deployment planned?
