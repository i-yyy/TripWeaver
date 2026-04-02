import axios from 'axios'

import type {
  BasicResponse,
  AuthChangePasswordPayload,
  DayRoutePayload,
  DayRouteResponse,
  AuthLoginPayload,
  AuthLoginResponse,
  AuthRegisterPayload,
  AuthUserResponse,
  FeedbackPayload,
  FeedbackResponse,
  KBEvaluatePayload,
  KBEvaluateResponse,
  TravelTracksResponse,
  TripFormData,
  TripPlanResponse,
  UpdateProfilePayload,
  UserProfileResponse,
} from '@/types'
import { clearAuthSession, getAccessToken } from '@/utils/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 1200000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthSession()
      if (!['/', '/login', '/register'].includes(window.location.pathname)) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export async function registerUser(payload: AuthRegisterPayload): Promise<AuthUserResponse> {
  try {
    const response = await apiClient.post<AuthUserResponse>('/api/auth/register', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '注册失败')
  }
}

export async function loginUser(payload: AuthLoginPayload): Promise<AuthLoginResponse> {
  try {
    const response = await apiClient.post<AuthLoginResponse>('/api/auth/login', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '登录失败')
  }
}

export async function getCurrentUser(): Promise<AuthUserResponse> {
  try {
    const response = await apiClient.get<AuthUserResponse>('/api/auth/me')
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取当前用户失败')
  }
}

export async function updateAccountProfile(payload: UpdateProfilePayload): Promise<AuthUserResponse> {
  try {
    const response = await apiClient.put<AuthUserResponse>('/api/auth/profile', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '更新个人信息失败')
  }
}

export async function changeAccountPassword(payload: AuthChangePasswordPayload): Promise<AuthUserResponse> {
  try {
    const response = await apiClient.put<AuthUserResponse>('/api/auth/password', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '修改密码失败')
  }
}

export async function deleteCurrentAccount(): Promise<AuthUserResponse> {
  try {
    const response = await apiClient.delete<AuthUserResponse>('/api/auth/me')
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '注销账号失败')
  }
}

export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '行程生成失败')
  }
}

export async function submitFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
  try {
    const response = await apiClient.post<FeedbackResponse>('/api/feedback/submit', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '提交反馈失败')
  }
}

export async function getMyUserProfile(): Promise<UserProfileResponse> {
  try {
    const response = await apiClient.get<UserProfileResponse>('/api/user/profile/me')
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取用户画像失败')
  }
}

export async function getTravelTracks(): Promise<TravelTracksResponse> {
  try {
    const response = await apiClient.get<TravelTracksResponse>('/api/tracks')
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取旅行轨迹失败')
  }
}

export async function deleteTravelTrack(trackId: string): Promise<BasicResponse> {
  try {
    const response = await apiClient.delete<BasicResponse>(`/api/tracks/${trackId}`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '删除旅行轨迹失败')
  }
}

export async function getDayRouteDetail(payload: DayRoutePayload): Promise<DayRouteResponse> {
  try {
    const response = await apiClient.post<DayRouteResponse>('/api/map/day-route', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '加载每日路线失败')
  }
}

export async function evaluateKnowledgeBase(payload: KBEvaluatePayload): Promise<KBEvaluateResponse> {
  try {
    const response = await apiClient.post<KBEvaluateResponse>('/api/kb/evaluate', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '知识库评估失败')
  }
}

export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    throw new Error(error.message || '健康检查失败')
  }
}

export default apiClient
