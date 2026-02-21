import apiClient from './client'
import type { User, MembershipTier } from '@/types/auth'

export async function listUsers(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/admin/users')
  return data
}

export async function updateUserTier(userId: number, tier: MembershipTier): Promise<User> {
  const { data } = await apiClient.patch<User>(`/admin/users/${userId}/tier`, {
    membership_tier: tier,
  })
  return data
}

export async function updateUserEmail(userId: number, email: string): Promise<User> {
  const { data } = await apiClient.patch<User>(`/admin/users/${userId}/email`, { email })
  return data
}

export async function toggleUserActive(userId: number): Promise<User> {
  const { data } = await apiClient.patch<User>(`/admin/users/${userId}/active`)
  return data
}
