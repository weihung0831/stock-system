import apiClient from './client'
import type { RegisterRequest, TokenResponse, User } from '@/types/auth'

export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', { username, password })
  return data
}

export async function register(data: RegisterRequest): Promise<User> {
  const { data: user } = await apiClient.post<User>('/auth/register', data)
  return user
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>('/auth/me')
  return data
}

export async function updateEmail(email: string): Promise<User> {
  const { data } = await apiClient.put<User>('/auth/profile/email', { email })
  return data
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await apiClient.put('/auth/profile/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}
