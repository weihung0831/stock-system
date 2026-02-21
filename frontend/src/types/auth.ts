export type MembershipTier = 'free' | 'premium'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
  is_active: boolean
  membership_tier: MembershipTier
}
