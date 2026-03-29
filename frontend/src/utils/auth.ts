import { reactive } from 'vue'

import type { AuthUserData } from '@/types'

const ACCESS_TOKEN_KEY = 'trip_planner_access_token'
const AUTH_USER_KEY = 'trip_planner_auth_user'

function readStoredUser(): AuthUserData | null {
  const raw = localStorage.getItem(AUTH_USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUserData
  } catch {
    localStorage.removeItem(AUTH_USER_KEY)
    return null
  }
}

const authState = reactive<{
  token: string
  user: AuthUserData | null
}>({
  token: localStorage.getItem(ACCESS_TOKEN_KEY) || '',
  user: readStoredUser(),
})

export function useAuthState() {
  return authState
}

export function getAccessToken() {
  return authState.token
}

export function isAuthenticated() {
  return Boolean(authState.token && authState.user)
}

export function setAuthSession(token: string, user: AuthUserData) {
  authState.token = token
  authState.user = user
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
}

export function updateStoredUser(user: AuthUserData) {
  authState.user = user
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
}

export function clearAuthSession() {
  authState.token = ''
  authState.user = null
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(AUTH_USER_KEY)
}
