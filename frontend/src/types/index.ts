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

export interface DecisionScoreFactor {
  label: string
  impact: number
  reason: string
  value?: string
}

export interface DecisionScoreDimension {
  key: 'preference_fit' | 'budget_fit' | 'route_efficiency' | 'comfort' | 'resilience' | 'richness' | string
  label: string
  description: string
  score: number
  detail: string
  narrative?: string
  factors?: DecisionScoreFactor[]
}

export interface DecisionScoreSnapshot {
  overall: number
  dimensions: DecisionScoreDimension[]
  summary: string
  story?: string
  highlights: string[]
  risks: string[]
  budget: Budget
  estimated_distance_km: number
  estimated_distance_text: string
  comfort_text: string
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
  decision_score?: DecisionScoreSnapshot | null
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

export interface TripScoreSummary {
  budget_level?: string | null
  travel_style: string[]
  companions: string[]
  dietary_restrictions: string[]
  mobility_needs: string[]
  transportation: string
  free_text_input: string
}

export interface TripScorePayload {
  plan: TripPlan
  summary?: TripScoreSummary | null
}

export interface TripScoreResponse {
  success: boolean
  message: string
  data?: DecisionScoreSnapshot | null
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
  avatar_url?: string
  gender?: string
  is_active: boolean
  is_developer?: boolean
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
  gender?: string
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

export interface TravelTrackPlanResponse {
  success: boolean
  message: string
  data?: TripPlan | null
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

export interface CommunityTripCard {
  id: string
  city: string
  title: string
  subtitle: string
  summary: string
  cover_image_url: string
  days: number
  estimated_budget: 'low' | 'medium' | 'high' | string
  tags: string[]
  travel_style: string[]
  companions: string[]
  highlights: string[]
  author_name: string
  like_count: number
  favorite_count: number
  comment_count: number
  reuse_count: number
  match_score: number
  match_reasons: string[]
  liked_by_me: boolean
  favorited_by_me: boolean
  recent_comments: CommunityComment[]
}

export interface CommunityComment {
  id: string
  card_id: string
  author_name: string
  author_avatar_url?: string
  content: string
  created_at: string
}

export interface CommunityPostComment {
  id: string
  post_id: string
  author_name: string
  author_avatar_url?: string
  content: string
  created_at: string
}

export interface CommunityFeedData {
  cards: CommunityTripCard[]
  preference_tags: string[]
  recent_cities: string[]
  summary: string
}

export interface CommunityFeedResponse {
  success: boolean
  message: string
  data: CommunityFeedData
}

export interface CommunityInteractionResponse {
  success: boolean
  message: string
  active: boolean
}

export interface CommunityCommentResponse {
  success: boolean
  message: string
  data?: CommunityComment | null
}

export interface CommunityPost {
  id: string
  user_id: string
  author_name: string
  author_avatar_url?: string
  content: string
  image_urls: string[]
  city: string
  tags: string[]
  linked_track_id: string
  linked_track_title: string
  like_count: number
  comment_count: number
  created_at: string
  liked_by_me: boolean
  followed_author: boolean
  recent_comments: CommunityPostComment[]
}

export interface CommunityPostFeedResponse {
  success: boolean
  message: string
  data: CommunityPost[]
}

export interface CommunityUserSummary {
  id: string
  nickname: string
  email?: string
  avatar_url?: string
  gender?: string
  followed_by_me: boolean
}

export interface CommunityProfileHomeData {
  user: CommunityUserSummary
  follower_count: number
  following_count: number
  post_count: number
  followers: CommunityUserSummary[]
  following: CommunityUserSummary[]
  posts: CommunityPost[]
}

export interface CommunityProfileHomeResponse {
  success: boolean
  message: string
  data?: CommunityProfileHomeData | null
}

export interface CommunityPostResponse {
  success: boolean
  message: string
  data?: CommunityPost | null
}

export interface CommunityPostCommentResponse {
  success: boolean
  message: string
  data?: CommunityPostComment | null
}

export interface CommunityImageUploadResponse {
  success: boolean
  message: string
  url: string
}

export interface CollabUserData {
  id: string
  nickname: string
  email: string
  avatar_url?: string
}

export interface CollabTripMember {
  id: string
  trip_id: string
  user_id: string
  role: 'owner' | 'editor' | 'viewer' | string
  status: string
  joined_at: string
  user: CollabUserData
}

export interface CollabTripInvite {
  id: string
  trip_id: string
  inviter_user_id: string
  invitee_user_id: string
  invitee_email: string
  role: 'editor' | 'viewer' | string
  status: string
  created_at: string
  responded_at?: string | null
  inviter?: CollabUserData | null
  invitee?: CollabUserData | null
  trip_title: string
  city: string
}

export interface CollabTripComment {
  id: string
  trip_id: string
  day_index?: number | null
  user_id: string
  content: string
  created_at: string
  user: CollabUserData
}

export interface CollabTripVote {
  id: string
  trip_id: string
  target_type: string
  target_id: string
  user_id: string
  vote_type: string
  created_at: string
  user: CollabUserData
}

export interface CollabTripChange {
  id: string
  trip_id: string
  user_id: string
  change_type: string
  summary: string
  before_json: Record<string, unknown>
  after_json: Record<string, unknown>
  created_at: string
  user: CollabUserData
}

export interface CollabTripSummary {
  id: string
  owner_user_id: string
  source_track_id: string
  title: string
  city: string
  start_date: string
  end_date: string
  status: string
  version: number
  updated_at: string
  created_at: string
  owner: CollabUserData
  my_role: string
  member_count: number
  comment_count: number
}

export interface CollabTripDetail extends CollabTripSummary {
  plan_json: TripPlan
  members: CollabTripMember[]
  invites: CollabTripInvite[]
  comments: CollabTripComment[]
  votes: CollabTripVote[]
  changes: CollabTripChange[]
}

export interface CollabTripListResponse {
  success: boolean
  message: string
  data: CollabTripSummary[]
  pending_invites: CollabTripInvite[]
}

export interface CollabTripResponse {
  success: boolean
  message: string
  data?: CollabTripDetail | null
}

export interface CollabTripInviteResponse {
  success: boolean
  message: string
  data?: CollabTripInvite | null
}

export interface CollabTripCommentResponse {
  success: boolean
  message: string
  data?: CollabTripComment | null
}

export interface CollabTripVoteResponse {
  success: boolean
  message: string
  data?: CollabTripVote | null
  active: boolean
}
