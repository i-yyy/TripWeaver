import axios from 'axios'

import type {
  BasicResponse,
  AuthChangePasswordPayload,
  CommunityCommentResponse,
  CommunityFeedResponse,
  CommunityImageUploadResponse,
  CommunityInteractionResponse,
  CommunityPostCommentResponse,
  CommunityPostFeedResponse,
  CommunityProfileHomeResponse,
  CommunityPostResponse,
  CollabTripCommentResponse,
  CollabTripInviteResponse,
  CollabTripListResponse,
  CollabTripResponse,
  CollabTripVoteResponse,
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
  TravelTrackPlanResponse,
  TripFormData,
  TripPlanResponse,
  TripScorePayload,
  TripScoreResponse,
  UpdateProfilePayload,
  UserProfileResponse,
} from '@/types'
import { clearAuthSession, getAccessToken } from '@/utils/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_BASE_URL_NORMALIZED = API_BASE_URL.replace(/\/$/, '')

export function resolveMediaUrl(url?: string | null) {
  if (!url) return ''
  if (/^(https?:)?\/\//.test(url) || url.startsWith('data:') || url.startsWith('blob:')) {
    return url
  }
  if (url.startsWith('/')) {
    return `${API_BASE_URL_NORMALIZED}${url}`
  }
  return url
}

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

export async function uploadAccountAvatar(file: File): Promise<AuthUserResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<AuthUserResponse>('/api/auth/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '上传头像失败')
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

export async function evaluateTripDecisionScore(payload: TripScorePayload): Promise<TripScoreResponse> {
  try {
    const response = await apiClient.post<TripScoreResponse>('/api/trip/score', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '评分计算失败')
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

export async function getTravelTrackPlan(trackId: string): Promise<TravelTrackPlanResponse> {
  try {
    const response = await apiClient.get<TravelTrackPlanResponse>(`/api/tracks/${trackId}/plan`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取旅行规划失败')
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

export async function getCommunityFeed(limit = 8, refreshToken = ''): Promise<CommunityFeedResponse> {
  try {
    const response = await apiClient.get<CommunityFeedResponse>('/api/community/feed', {
      params: { limit, refresh_token: refreshToken },
    })
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取社区推荐失败')
  }
}

export async function toggleCommunityCardLike(cardId: string): Promise<CommunityInteractionResponse> {
  try {
    const response = await apiClient.post<CommunityInteractionResponse>(`/api/community/cards/${cardId}/like`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '更新喜欢状态失败')
  }
}

export async function toggleCommunityCardFavorite(cardId: string): Promise<CommunityInteractionResponse> {
  try {
    const response = await apiClient.post<CommunityInteractionResponse>(`/api/community/cards/${cardId}/favorite`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '更新收藏状态失败')
  }
}

export async function reuseCommunityCard(cardId: string): Promise<CommunityInteractionResponse> {
  try {
    const response = await apiClient.post<CommunityInteractionResponse>(`/api/community/cards/${cardId}/reuse`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '记录复用失败')
  }
}

export async function addCommunityCardComment(cardId: string, content: string): Promise<CommunityCommentResponse> {
  try {
    const response = await apiClient.post<CommunityCommentResponse>(`/api/community/cards/${cardId}/comments`, {
      content,
    })
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '发表评论失败')
  }
}

export async function getCommunityPosts(limit = 20): Promise<CommunityPostFeedResponse> {
  try {
    const response = await apiClient.get<CommunityPostFeedResponse>('/api/community/posts', {
      params: { limit },
    })
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取社区动态失败')
  }
}

export async function getMyCommunityProfile(limit = 60): Promise<CommunityProfileHomeResponse> {
  try {
    const response = await apiClient.get<CommunityProfileHomeResponse>('/api/community/profile/me', {
      params: { limit },
    })
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取个人主页失败')
  }
}

export async function getCommunityProfile(userId: string, limit = 60): Promise<CommunityProfileHomeResponse> {
  try {
    const response = await apiClient.get<CommunityProfileHomeResponse>(`/api/community/profile/${userId}`, {
      params: { limit },
    })
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取作者主页失败')
  }
}

export async function publishCommunityPost(payload: {
  content: string
  image_urls: string[]
  city: string
  tags: string[]
  linked_track_id?: string
  linked_track_title?: string
}): Promise<CommunityPostResponse> {
  try {
    const response = await apiClient.post<CommunityPostResponse>('/api/community/posts', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '发布动态失败')
  }
}

export async function uploadCommunityImage(file: File): Promise<CommunityImageUploadResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<CommunityImageUploadResponse>('/api/community/uploads/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '上传图片失败')
  }
}

export async function toggleCommunityPostLike(postId: string): Promise<CommunityInteractionResponse> {
  try {
    const response = await apiClient.post<CommunityInteractionResponse>(`/api/community/posts/${postId}/like`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '更新动态喜欢失败')
  }
}

export async function deleteCommunityPost(postId: string): Promise<CommunityPostResponse> {
  try {
    const response = await apiClient.delete<CommunityPostResponse>(`/api/community/posts/${postId}`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '删除动态失败')
  }
}

export async function updateCommunityPost(postId: string, payload: {
  content: string
  image_urls: string[]
  city: string
  tags: string[]
  linked_track_id?: string
  linked_track_title?: string
}): Promise<CommunityPostResponse> {
  try {
    const response = await apiClient.patch<CommunityPostResponse>(`/api/community/posts/${postId}`, payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '编辑动态失败')
  }
}

export async function addCommunityPostComment(postId: string, content: string): Promise<CommunityPostCommentResponse> {
  try {
    const response = await apiClient.post<CommunityPostCommentResponse>(`/api/community/posts/${postId}/comments`, {
      content,
    })
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '评论动态失败')
  }
}

export async function getCommunityPostPlan(postId: string): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.get<TripPlanResponse>(`/api/community/posts/${postId}/plan`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取帖子关联规划失败')
  }
}

export async function toggleCommunityAuthorFollow(userId: string): Promise<CommunityInteractionResponse> {
  try {
    const response = await apiClient.post<CommunityInteractionResponse>(`/api/community/users/${userId}/follow`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '关注状态更新失败')
  }
}

export async function getCollabTrips(): Promise<CollabTripListResponse> {
  try {
    const response = await apiClient.get<CollabTripListResponse>('/api/collab/trips')
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取协同行程失败')
  }
}

export async function createCollabTrip(payload: { source_track_id: string; title?: string }): Promise<CollabTripResponse> {
  try {
    const response = await apiClient.post<CollabTripResponse>('/api/collab/trips', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '创建协同行程失败')
  }
}

export async function getCollabTrip(tripId: string): Promise<CollabTripResponse> {
  try {
    const response = await apiClient.get<CollabTripResponse>(`/api/collab/trips/${tripId}`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '获取协同行程详情失败')
  }
}

export async function deleteCollabTrip(tripId: string): Promise<BasicResponse> {
  try {
    const response = await apiClient.delete<BasicResponse>(`/api/collab/trips/${tripId}`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '删除协同行程失败')
  }
}

export async function updateCollabTripPlan(
  tripId: string,
  payload: { plan_json: Record<string, unknown>; summary?: string },
): Promise<CollabTripResponse> {
  try {
    const response = await apiClient.put<CollabTripResponse>(`/api/collab/trips/${tripId}/plan`, payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '保存协同行程失败')
  }
}

export async function inviteCollabTripMember(
  tripId: string,
  payload: { identifier: string; role: string },
): Promise<CollabTripInviteResponse> {
  try {
    const response = await apiClient.post<CollabTripInviteResponse>(`/api/collab/trips/${tripId}/invites`, payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '邀请好友失败')
  }
}

export async function respondCollabInvite(inviteId: string, action: 'accept' | 'reject'): Promise<CollabTripInviteResponse> {
  try {
    const response = await apiClient.post<CollabTripInviteResponse>(`/api/collab/invites/${inviteId}/${action}`)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '处理邀请失败')
  }
}

export async function addCollabTripComment(
  tripId: string,
  payload: { content: string; day_index?: number | null },
): Promise<CollabTripCommentResponse> {
  try {
    const response = await apiClient.post<CollabTripCommentResponse>(`/api/collab/trips/${tripId}/comments`, payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '发送协同评论失败')
  }
}

export async function voteCollabTripItem(
  tripId: string,
  payload: { target_type: string; target_id: string; vote_type: string },
): Promise<CollabTripVoteResponse> {
  try {
    const response = await apiClient.post<CollabTripVoteResponse>(`/api/collab/trips/${tripId}/votes`, payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '更新投票失败')
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
