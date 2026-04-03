export interface Location {
  longitude: number
  latitude: number
}

export interface Attraction {
  name: string
  address: string
  location: Location
  visit_duration: number
  description: string
  category?: string
  rating?: number
  photos?: string[]
  poi_id?: string
  image_url?: string
  image_source?: string
  image_status?: string
  map_image_url?: string
  ticket_price?: number
}

export interface Meal {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  name: string
  address?: string
  location?: Location
  description?: string
  estimated_cost?: number
}

export interface Hotel {
  name: string
  address: string
  location?: Location
  price_range: string
  rating: string
  distance: string
  type: string
  estimated_cost?: number
  map_image_url?: string
}

export interface Budget {
  total_attractions: number
  total_hotels: number
  total_meals: number
  total_transportation: number
  total: number
}

export interface RecommendationReason {
  source_type: 'knowledge_base' | 'profile' | 'memory' | string
  title: string
  reason: string
  snippet: string
  score: number
  rerank_mode?: string
  source_doc?: string | null
  metadata?: Record<string, unknown>
}

export interface AppliedSkill {
  key: string
  name: string
  description?: string
  score?: number
  priority?: number
  layer?: string
  category?: string
  source?: string
  matched_fields?: string[]
  matched_terms?: string[]
  reasons?: string[]
  hard_rules?: string[]
  soft_rules?: string[]
}

export interface DayPlan {
  date: string
  day_index: number
  description: string
  transportation: string
  transportation_detail?: string
  transportation_cost?: number
  accommodation: string
  hotel?: Hotel
  attractions: Attraction[]
  meals: Meal[]
  route_summary?: string
  route_map_url?: string
}

export interface DayRouteStopPayload {
  name: string
  address?: string
  location?: Location
  image_url?: string
}

export interface DayRouteMarker {
  label: string
  title: string
  kind: string
  address: string
  location: Location
  image_url?: string | null
}

export interface DayRouteSegment {
  start_label: string
  end_label: string
  route_type: string
  distance: number
  duration: number
  description: string
  polyline: Location[]
}

export interface DayRouteInfo {
  route_type: string
  summary: string
  distance: number
  duration: number
  markers: DayRouteMarker[]
  segments: DayRouteSegment[]
  fallback_static_map_url?: string | null
}

export interface DayRoutePayload {
  city: string
  route_type: 'walking' | 'driving' | 'transit'
  hotel?: DayRouteStopPayload | null
  attractions: DayRouteStopPayload[]
}

export interface DayRouteResponse {
  success: boolean
  message: string
  data?: DayRouteInfo | null
}

export interface WeatherInfo {
  date: string
  day_weather: string
  night_weather: string
  day_temp: number
  night_temp: number
  wind_direction: string
  wind_power: string
}

export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  days: DayPlan[]
  weather_info: WeatherInfo[]
  overall_suggestions: string
  budget?: Budget
  recommendation_reasons?: RecommendationReason[]
  applied_skills?: AppliedSkill[]
}

export interface TripFormData {
  user_id: string
  session_id: string
  city: string
  start_date: string
  end_date: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
  budget_level?: string | null
  travel_style: string[]
  companions: string[]
  dietary_restrictions: string[]
  mobility_needs: string[]
}

export interface TripPlanResponse {
  success: boolean
  message: string
  data?: TripPlan
}

export interface FeedbackPayload {
  user_id: string
  session_id: string
  target_type: 'attraction' | 'hotel' | 'plan'
  target_name: string
  feedback_type: 'like' | 'dislike' | 'replace' | 'satisfied' | 'unsatisfied'
  reason?: string
  metadata?: Record<string, unknown>
}

export interface FeedbackResponse {
  success: boolean
  message: string
  feedback_id?: string
}

export interface UserProfileData {
  user_id: string
  preferred_transportation?: string
  preferred_accommodation?: string
  budget_level?: string
  pace_level?: string
  interest_weights: Record<string, number>
  dietary_restrictions: string[]
  mobility_needs: string[]
  avoid_tags: string[]
  updated_at?: string
}

export interface UserProfileResponse {
  success: boolean
  message: string
  data?: UserProfileData
}

export interface AuthUserData {
  id: string
  email: string
  nickname: string
  is_active: boolean
  created_at?: string
}

export interface AuthRegisterPayload {
  nickname: string
  email: string
  password: string
}

export interface AuthLoginPayload {
  email: string
  password: string
}

export interface UpdateProfilePayload {
  nickname: string
  email: string
}

export interface AuthChangePasswordPayload {
  current_password: string
  new_password: string
}

export interface AuthUserResponse {
  success: boolean
  message: string
  data?: AuthUserData
}

export interface AuthLoginResponse extends AuthUserResponse {
  access_token: string
  token_type: string
}

export interface TravelTrackItem {
  id: string
  city: string
  start_date: string
  end_date: string
  searched_at: string
  trip_summary: string
  city_longitude?: number | null
  city_latitude?: number | null
}

export interface TravelTracksResponse {
  success: boolean
  message: string
  data: TravelTrackItem[]
}

export interface BasicResponse {
  success: boolean
  message: string
}

export interface KBEvaluatePayload {
  query: string
  city?: string | null
  top_k?: number
  tags?: string | null
  crowd_type?: string | null
  budget_level?: string | null
  expected_terms?: string[]
  rerank?: boolean
}

export interface KBEvaluateMetrics {
  recall_count: number
  final_count: number
  expected_term_count: number
  expected_hit_count: number
  expected_hit_rate: number
  score_avg: number
  score_max: number
  score_min: number
  top1_gain: number
  rerank_mode: string
}

export interface KBEvaluateItem {
  rank: number
  score: number
  base_score: number
  rerank_score: number
  rerank_mode: string
  city_hint?: string
  source_doc?: string
  snippet: string
  metadata?: Record<string, unknown>
}

export interface KBEvaluateResponse {
  status: string
  message: string
  query: string
  city_filter?: string
  metadata_filters?: Record<string, unknown>
  metrics: KBEvaluateMetrics
  items: KBEvaluateItem[]
}
