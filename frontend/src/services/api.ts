import axios from 'axios'
import type {
  FeedbackPayload,
  FeedbackResponse,
  KBEvaluatePayload,
  KBEvaluateResponse,
  TripFormData,
  TripPlanResponse,
  UserProfileResponse,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config) => {
    console.log('请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  },
)

apiClient.interceptors.response.use(
  (response) => {
    console.log('响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  },
)

export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
    return response.data
  } catch (error: any) {
    console.error('生成行程失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '生成行程失败')
  }
}

export async function submitFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
  try {
    const response = await apiClient.post<FeedbackResponse>('/api/feedback/submit', payload)
    return response.data
  } catch (error: any) {
    console.error('提交反馈失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '提交反馈失败')
  }
}

export async function getUserProfile(userId: string): Promise<UserProfileResponse> {
  try {
    const response = await apiClient.get<UserProfileResponse>(`/api/user/profile/${userId}`)
    return response.data
  } catch (error: any) {
    console.error('获取用户画像失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '获取用户画像失败')
  }
}

export async function evaluateKnowledgeBase(payload: KBEvaluatePayload): Promise<KBEvaluateResponse> {
  try {
    const response = await apiClient.post<KBEvaluateResponse>('/api/kb/evaluate', payload)
    return response.data
  } catch (error: any) {
    console.error('评估知识库失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '评估知识库失败')
  }
}

export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    console.error('健康检查失败:', error)
    throw new Error(error.message || '健康检查失败')
  }
}

export default apiClient
