<template>
  <div class="brand-page community-page">
    <div class="brand-shell community-shell">
      <section class="community-hero">
        <div class="community-hero__copy">
          <span class="page-kicker">社区交流</span>
          <h1 class="page-title community-title">从大家分享的路线里，找到下一次出发的灵感</h1>
          <p class="page-subtitle community-subtitle">
            {{ authenticated ? feedSummary : '浏览社区旅行卡片，登录后会结合你的偏好、反馈和历史行程排序推荐。' }}
          </p>
          <div class="community-actions">
            <a-button type="primary" size="large" @click="goPlanner">开始规划</a-button>
            <a-button v-if="!authenticated" size="large" @click="goLogin">登录获取个性推荐</a-button>
          </div>
        </div>

        <div class="community-hero__panel">
          <div class="community-profile-card">
            <span class="community-profile-card__label">推荐依据</span>
            <strong>{{ authenticated ? '你的旅行偏好' : '社区热门路线' }}</strong>
            <p>{{ profileInsight }}</p>
            <div class="community-chip-row">
              <span v-for="tag in visiblePreferenceTags" :key="tag" class="community-chip">{{ tagLabel(tag) }}</span>
            </div>
          </div>
        </div>
      </section>

      <section class="community-layout">
        <div class="community-main">
          <div class="community-section-head">
            <div>
              <h2>为你推荐的旅行卡片</h2>
              <p>卡片会根据偏好匹配度、社区热度、收藏和复用次数排序。</p>
            </div>
            <a-button v-if="authenticated" :loading="loading" @click="loadFeed(true)">刷新推荐</a-button>
          </div>

          <a-spin :spinning="loading">
            <a-empty v-if="!displayCards.length" description="暂时没有社区推荐" />
            <div v-else class="community-card-grid">
              <article
                v-for="card in displayCards"
                :key="card.id"
                class="trip-share-card"
                role="button"
                tabindex="0"
                @click="openCardDetail(card)"
                @keyup.enter="openCardDetail(card)"
              >
                <div class="trip-share-card__media">
                  <img :src="card.cover_image_url" :alt="card.title" @error="handleImageError" />
                  <div class="trip-share-card__score">匹配 {{ Math.round(card.match_score * 100) }}%</div>
                </div>
                <div class="trip-share-card__body">
                  <div class="trip-share-card__topline">
                    <span>{{ card.city }} · {{ card.days }} 天</span>
                    <span>{{ budgetLabel(card.estimated_budget) }}</span>
                  </div>
                  <h3>{{ card.title }}</h3>
                  <p class="trip-share-card__subtitle">{{ card.subtitle }}</p>
                  <p class="trip-share-card__summary">{{ card.summary }}</p>

                  <div class="community-chip-row">
                    <span v-for="tag in card.tags.slice(0, 4)" :key="`${card.id}-${tag}`" class="community-chip community-chip--soft">
                      {{ tagLabel(tag) }}
                    </span>
                  </div>
                  <p class="trip-share-card__hint">点击卡片查看路线详情、评论、点赞和收藏</p>

                  <div class="trip-share-card__highlights">
                    <span v-for="item in card.highlights" :key="`${card.id}-${item}`">{{ item }}</span>
                  </div>

                  <div class="trip-share-card__reason">
                    <strong>为什么推荐</strong>
                    <span>{{ card.match_reasons.join('；') }}</span>
                  </div>

                  <div class="trip-share-card__footer">
                    <div class="trip-share-card__metrics">
                      <span>{{ card.author_name }}</span>
                      <span>{{ card.like_count }} 喜欢</span>
                      <span>{{ card.favorite_count }} 收藏</span>
                      <span>{{ card.reuse_count }} 复用</span>
                    </div>
                    <div class="trip-share-card__actions">
                      <a-button size="small" @click="toggleLike(card)">{{ card.liked_by_me ? '已喜欢' : '喜欢' }}</a-button>
                      <a-button size="small" @click="toggleFavorite(card)">{{ card.favorited_by_me ? '已收藏' : '收藏' }}</a-button>
                      <a-button size="small" type="primary" @click="useCard(card)">用它规划</a-button>
                    </div>
                  </div>

                  <div class="trip-share-card__comments">
                    <strong>社区交流</strong>
                    <div v-if="card.recent_comments.length" class="trip-share-card__comment-list">
                      <p v-for="comment in card.recent_comments" :key="comment.id">
                        <span>{{ comment.author_name }}：</span>{{ comment.content }}
                      </p>
                    </div>
                    <p v-else class="trip-share-card__comment-empty">还没有评论，来补一句真实感受。</p>
                    <div v-if="authenticated" class="trip-share-card__comment-box">
                      <a-input
                        v-model:value="commentDrafts[card.id]"
                        placeholder="写一句你的看法"
                        :maxlength="300"
                        @pressEnter="submitComment(card)"
                      />
                      <a-button size="small" :loading="submittingCommentId === card.id" @click="submitComment(card)">
                        发送
                      </a-button>
                    </div>
                    <p v-else class="trip-share-card__comment-empty">登录后可以参与路线交流。</p>
                  </div>
                </div>
              </article>
            </div>
          </a-spin>
        </div>

        <aside class="community-side">
          <section class="community-side-panel">
            <h3>社区动态</h3>
            <div class="community-activity-list">
              <article v-for="item in communityActivities" :key="item.title" class="community-activity">
                <strong>{{ item.title }}</strong>
                <p>{{ item.text }}</p>
              </article>
            </div>
          </section>

          <section class="community-side-panel">
            <h3>最近关注</h3>
            <div v-if="recentCities.length" class="community-city-list">
              <span v-for="city in recentCities" :key="city">{{ city }}</span>
            </div>
            <p v-else class="community-muted">生成一次行程后，这里会显示你最近关注的城市。</p>
          </section>
        </aside>
      </section>

      <section class="moments-layout">
        <div class="moments-main">
          <div class="community-section-head">
            <div>
              <h2>旅行动态</h2>
              <p>像朋友圈一样发一条旅行心情，晒图、交流、关注有趣的作者。</p>
            </div>
            <div class="moments-header-actions">
              <a-button v-if="authenticated" type="primary" @click="openPostComposer">发布旅行动态</a-button>
              <a-button v-if="authenticated" :loading="postLoading" @click="loadPosts">刷新动态</a-button>
            </div>
          </div>

          <section v-if="showPostComposer" class="moments-composer">
            <div class="moments-composer__head">
              <strong>{{ authenticated ? '发布一条新的旅行动态' : '登录后发布你的旅行动态' }}</strong>
              <span>支持图文、城市和标签</span>
            </div>
            <a-textarea
              v-model:value="postDraft.content"
              :rows="4"
              :maxlength="600"
              placeholder="这一趟你最喜欢什么？踩坑也可以直说。"
              :disabled="!authenticated"
            />
            <div class="moments-composer__grid">
              <a-input v-model:value="postDraft.city" placeholder="关联城市，例如：杭州" :disabled="!authenticated" />
              <a-input
                v-model:value="postDraft.tagsText"
                placeholder="标签，逗号分隔，例如：citywalk, 美食, 夜景"
                :disabled="!authenticated"
              />
            </div>
            <a-select
              v-model:value="postDraft.linkedTrackId"
              allow-clear
              placeholder="请选择要关联的行程（可选）"
              :not-found-content="trackLoading ? '正在加载行程...' : '暂无可关联行程，请先生成旅行规划'"
              :disabled="!authenticated || trackLoading"
              :loading="trackLoading"
              @change="handleLinkedTrackChange"
            >
              <a-select-option v-for="track in availableTracks" :key="track.id" :value="track.id">
                {{ track.city }} · {{ track.start_date }} - {{ track.end_date }}
              </a-select-option>
            </a-select>
            <div class="moments-composer__images">
              <input
                ref="imageInputRef"
                class="moments-composer__file-input"
                type="file"
                accept="image/*"
                multiple
                @change="handleImageFiles"
              />
              <div v-if="postDraft.imageUrls.length" class="moments-composer__preview-grid">
                <div
                  v-for="(imageUrl, index) in postDraft.imageUrls"
                  :key="`${imageUrl}-${index}`"
                  class="moments-composer__preview"
                >
                  <img :src="imageUrl" :alt="`旅行动态图片 ${index + 1}`" @error="handleImageError" />
                  <a-button
                    size="small"
                    class="moments-composer__preview-remove"
                    @click="removeDraftImage(index)"
                    :disabled="!authenticated || uploadingImages"
                  >
                    移除
                  </a-button>
                </div>
              </div>
              <div class="moments-composer__toolbar">
                <div class="moments-composer__toolbar-actions">
                  <a-button
                    size="small"
                    :loading="uploadingImages"
                    @click="openImagePicker"
                    :disabled="!authenticated || uploadingImages || postDraft.imageUrls.length >= 9"
                  >
                    选择本地图片
                  </a-button>
                  <span class="moments-composer__toolbar-hint">{{ postDraft.imageUrls.length }}/9 张</span>
                </div>
                <div class="moments-composer__toolbar-actions">
                  <a-button @click="closePostComposer" :disabled="publishingPost || uploadingImages">取消</a-button>
                  <a-button
                    type="primary"
                    :loading="publishingPost"
                    @click="publishPost"
                    :disabled="!authenticated || uploadingImages"
                  >
                    发布动态
                  </a-button>
                </div>
              </div>
            </div>
          </section>

          <div class="moments-feed">
            <a-empty v-if="!posts.length && !postLoading" description="还没有社区动态，发第一条吧" />
            <article v-for="post in posts" :key="post.id" class="moment-card">
              <div class="moment-card__head">
                <div class="moment-card__author">
                  <img
                    v-if="post.author_avatar_url"
                    class="moment-card__avatar-image"
                    :src="resolveMediaUrl(post.author_avatar_url)"
                    :alt="`${post.author_name} 的头像`"
                    @error="handleImageError"
                  />
                  <div v-else class="moment-card__avatar" :style="avatarStyle(post.author_name)">{{ avatarText(post.author_name) }}</div>
                  <div class="moment-card__author-meta">
                    <strong>{{ post.author_name }}</strong>
                    <p>{{ formatTime(post.created_at) }}<span v-if="post.city"> · {{ post.city }}</span></p>
                  </div>
                </div>
                <a-button
                  v-if="authenticated && authState.user?.id !== post.user_id"
                  size="small"
                  type="primary"
                  ghost
                  @click="toggleFollow(post)"
                >
                  {{ post.followed_author ? '已关注' : '+ 关注' }}
                </a-button>
              </div>

              <p class="moment-card__content">{{ post.content }}</p>

              <div v-if="post.tags.length" class="community-chip-row">
                <span v-for="tag in post.tags" :key="`${post.id}-${tag}`" class="community-chip community-chip--soft">
                  {{ tag }}
                </span>
              </div>

              <div v-if="post.image_urls.length" class="moment-card__images">
                <a-image-preview-group>
                  <a-image
                    v-for="(imageUrl, index) in post.image_urls"
                    :key="`${post.id}-image-${index}`"
                    :src="imageUrl"
                    :alt="`${post.author_name} 的旅行图片 ${index + 1}`"
                    @error="handleImageError"
                  />
                </a-image-preview-group>
              </div>

              <button
                v-if="post.linked_track_id"
                class="moment-card__plan-link"
                type="button"
                @click="openPostPlan(post)"
              >
                <span class="moment-card__plan-link-label">查看关联规划</span>
                <strong>{{ post.linked_track_title || '旅行规划' }}</strong>
                <span class="moment-card__plan-link-arrow">进入</span>
              </button>

              <div class="moment-card__meta">
                <span>❤️ {{ post.like_count }} 喜欢</span>
                <span>{{ post.comment_count }} 评论</span>
              </div>

              <div class="moment-card__actions">
                <a-button size="small" @click="togglePostLike(post)">{{ post.liked_by_me ? '❤️ 已喜欢' : '❤️ 喜欢' }}</a-button>
              </div>

              <div class="moment-card__comments">
                <p v-if="!post.recent_comments.length" class="trip-share-card__comment-empty">还没有评论，来做第一个回应。</p>
                <button
                  v-for="comment in post.recent_comments"
                  :key="comment.id"
                  type="button"
                  class="moment-card__comment-item"
                  @click="startReplyToComment(post, comment)"
                >
                  <div class="moment-card__comment-head">
                    <img
                      v-if="comment.author_avatar_url"
                      class="moment-card__comment-avatar-image"
                      :src="resolveMediaUrl(comment.author_avatar_url)"
                      :alt="`${comment.author_name} 的头像`"
                      @error="handleImageError"
                    />
                    <div
                      v-else
                      class="moment-card__comment-avatar"
                      :style="avatarStyle(comment.author_name)"
                    >
                      {{ avatarText(comment.author_name) }}
                    </div>
                    <div class="moment-card__comment-meta">
                      <span class="moment-card__comment-author">{{ comment.author_name }}</span>
                      <span class="moment-card__comment-time">{{ formatCommentTime(comment.created_at) }}</span>
                    </div>
                  </div>
                  <span class="moment-card__comment-content">{{ comment.content }}</span>
                </button>
                <div v-if="authenticated" class="trip-share-card__comment-box">
                  <div v-if="postReplyTargets[post.id]" class="moment-card__replying">
                    <span>回复 {{ postReplyTargets[post.id]?.author_name }}</span>
                    <a-button type="link" size="small" @click="cancelReplyToComment(post.id)">取消</a-button>
                  </div>
                  <a-input
                    v-model:value="postCommentDrafts[post.id]"
                    :placeholder="postReplyTargets[post.id] ? `回复 ${postReplyTargets[post.id]?.author_name}` : '给这条动态留一句评论'"
                    :maxlength="300"
                    @pressEnter="submitPostComment(post)"
                  />
                  <a-button size="small" :loading="submittingPostCommentId === post.id" @click="submitPostComment(post)">
                    发送
                  </a-button>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import {
  addCommunityCardComment,
  addCommunityPostComment,
  getCommunityPostPlan,
  getCommunityFeed,
  getCommunityPosts,
  getTravelTracks,
  publishCommunityPost,
  reuseCommunityCard,
  resolveMediaUrl,
  toggleCommunityAuthorFollow,
  toggleCommunityCardFavorite,
  toggleCommunityCardLike,
  toggleCommunityPostLike,
  uploadCommunityImage,
} from '@/services/api'
import type { CommunityFeedData, CommunityPost, CommunityTripCard, TravelTrackItem } from '@/types'
import { useAuthState } from '@/utils/auth'
import { avatarStyle, avatarText } from '@/utils/avatar'
import { saveCommunityCards, saveSelectedCommunityCard } from '@/utils/communityCards'

const router = useRouter()
const authState = useAuthState()
const loading = ref(false)
const postLoading = ref(false)
const trackLoading = ref(false)
const publishingPost = ref(false)
const uploadingImages = ref(false)
const showPostComposer = ref(false)
const feed = ref<CommunityFeedData | null>(null)
const posts = ref<CommunityPost[]>([])
const availableTracks = ref<TravelTrackItem[]>([])
const commentDrafts = ref<Record<string, string>>({})
const submittingCommentId = ref('')
const postCommentDrafts = ref<Record<string, string>>({})
const submittingPostCommentId = ref('')
const postReplyTargets = ref<Record<string, { id: string; author_name: string } | null>>({})
const imageInputRef = ref<HTMLInputElement | null>(null)
const postDraft = ref({
  content: '',
  city: '',
  tagsText: '',
  imageUrls: [] as string[],
  linkedTrackId: undefined as string | undefined,
  linkedTrackTitle: '',
})

const authenticated = computed(() => Boolean(authState.token && authState.user))
const displayCards = computed(() => feed.value?.cards?.length ? feed.value.cards : publicCards)
const preferenceTags = computed(() => feed.value?.preference_tags || [])
const recentCities = computed(() => feed.value?.recent_cities || [])
const summaryTagLabels: Record<string, string> = {
  citywalk: '城市漫游',
  culture: '文化体验',
  tea: '茶馆',
  photo_friendly: '适合拍照',
  slow: '慢节奏',
  family: '亲子',
  museum: '博物馆',
  rainy_day: '雨天友好',
  indoor: '室内',
  less_walking: '少步行',
  food: '美食',
  night: '夜景',
  local_flavor: '本地风味',
  budget: '预算友好',
  public_transit: '公共交通',
  history: '历史',
  nature: '自然',
  friends: '朋友出行',
  couple: '情侣',
  solo: '独行',
}
const localizeSummary = (summary: string) =>
  Object.entries(summaryTagLabels)
    .reduce((text, [key, label]) => text.replace(new RegExp(`\\b${key}\\b`, 'g'), label), summary)
    .replace(/, /g, '、')
const feedSummary = computed(() => localizeSummary(feed.value?.summary || '正在根据你的偏好整理社区路线。'))
const visiblePreferenceTags = computed(() => {
  if (preferenceTags.value.length) return preferenceTags.value.slice(0, 6)
  return ['citywalk', 'food', 'museum', 'slow', 'family', 'local_flavor']
})

const profileInsight = computed(() => {
  if (!authenticated.value) {
    return '当前展示的是社区里复用率较高的旅行路线。登录后，系统会按你的画像重新排序。'
  }
  if (preferenceTags.value.length) {
    return `优先参考 ${preferenceTags.value.slice(0, 3).map(tagLabel).join('、')} 等偏好。`
  }
  return '你的画像还在积累中，先从热度高、复用多的社区路线开始。'
})

const communityActivities = [
  { title: '杭州城市漫游被多次收藏', text: '慢节奏、茶馆和湖边散步路线很受欢迎。' },
  { title: '亲子用户更偏好室内备选', text: '雨天博物馆路线的复用率正在上升。' },
  { title: '夜景路线适合朋友出行', text: '上海和重庆的夜间路线讨论最多。' },
]

const publicCards: CommunityTripCard[] = [
  {
    id: 'public-hangzhou',
    city: '杭州',
    title: '西湖边的轻量城市漫游',
    subtitle: '适合第一次来杭州，也适合想慢慢走的人',
    summary: '把西湖、茶馆、老街和傍晚湖岸串在同一天，节奏轻，拍照和休息点都比较充足。',
    cover_image_url: 'https://images.unsplash.com/photo-1598751337485-0d57b0c50b7a?auto=format&fit=crop&w=1200&q=80',
    days: 2,
    estimated_budget: 'medium',
    tags: ['citywalk', 'culture', 'tea', 'slow'],
    travel_style: ['citywalk', 'slow'],
    companions: ['solo', 'couple'],
    highlights: ['西湖湖岸散步', '龙井茶体验', '傍晚城市夜色'],
    author_name: '阿禾',
    like_count: 328,
    favorite_count: 146,
    comment_count: 42,
    reuse_count: 89,
    match_score: 0.82,
    match_reasons: ['社区热度高，适合作为灵感起点'],
    liked_by_me: false,
    favorited_by_me: false,
    recent_comments: [],
  },
  {
    id: 'public-beijing',
    city: '北京',
    title: '雨天也稳的亲子博物馆路线',
    subtitle: '室内为主，适合家庭和低强度出行',
    summary: '上午看展，午餐放在馆区周边，下午用科技馆或书店补充，减少下雨天反复折返。',
    cover_image_url: 'https://images.unsplash.com/photo-1599571234909-29ed5d1321d6?auto=format&fit=crop&w=1200&q=80',
    days: 2,
    estimated_budget: 'medium',
    tags: ['family', 'museum', 'rainy_day', 'indoor'],
    travel_style: ['museum', 'slow'],
    companions: ['family'],
    highlights: ['博物馆主线', '室内备选', '亲子低步行'],
    author_name: '小鹿一家',
    like_count: 421,
    favorite_count: 205,
    comment_count: 58,
    reuse_count: 132,
    match_score: 0.79,
    match_reasons: ['社区热度高，适合作为灵感起点'],
    liked_by_me: false,
    favorited_by_me: false,
    recent_comments: [],
  },
  {
    id: 'public-shanghai',
    city: '上海',
    title: '外滩夜景和街区美食短途',
    subtitle: '朋友或情侣都适合的一晚一日路线',
    summary: '白天把历史街区和咖啡馆串联，晚上留给外滩夜景和本地小吃，适合轻社交出行。',
    cover_image_url: 'https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?auto=format&fit=crop&w=1200&q=80',
    days: 2,
    estimated_budget: 'medium',
    tags: ['food', 'night', 'citywalk', 'local_flavor'],
    travel_style: ['citywalk', 'local'],
    companions: ['couple', 'friends'],
    highlights: ['外滩夜景', '街区小吃', '咖啡馆停留'],
    author_name: '周末在路上',
    like_count: 386,
    favorite_count: 178,
    comment_count: 46,
    reuse_count: 104,
    match_score: 0.76,
    match_reasons: ['社区热度高，适合作为灵感起点'],
    liked_by_me: false,
    favorited_by_me: false,
    recent_comments: [],
  },
]

const tagLabels: Record<string, string> = {
  citywalk: '城市漫游',
  culture: '文化',
  tea: '茶馆',
  photo_friendly: '适合拍照',
  slow: '慢节奏',
  family: '亲子',
  museum: '博物馆',
  rainy_day: '雨天',
  indoor: '室内',
  less_walking: '少步行',
  food: '美食',
  night: '夜景',
  local_flavor: '本地风味',
  budget: '预算友好',
  public_transit: '公共交通',
  history: '历史',
  nature: '自然',
  friends: '朋友',
  couple: '情侣',
  solo: '独行',
}

const tagLabel = (tag: string) => tagLabels[tag] || tag
const budgetLabel = (value: string) => {
  if (value === 'low') return '低预算'
  if (value === 'high') return '高预算'
  return '中预算'
}

const loadFeed = async (forceRefresh = false) => {
  if (!authenticated.value) return
  loading.value = true
  try {
    const response = await getCommunityFeed(8, forceRefresh ? `${Date.now()}-${Math.random()}` : '')
    if (!response.success) {
      throw new Error(response.message || '获取社区推荐失败')
    }
    feed.value = response.data
  } catch (error: any) {
    message.warning(error.message || '获取社区推荐失败，已展示默认社区路线')
  } finally {
    loading.value = false
  }
}

const loadPosts = async () => {
  if (!authenticated.value) {
    posts.value = []
    return
  }
  postLoading.value = true
  try {
    const response = await getCommunityPosts(20)
    if (!response.success) {
      throw new Error(response.message || '获取社区动态失败')
    }
    posts.value = response.data
  } catch (error: any) {
    message.warning(error.message || '获取社区动态失败')
  } finally {
    postLoading.value = false
  }
}

const loadAvailableTracks = async () => {
  if (!authenticated.value) {
    availableTracks.value = []
    return
  }
  trackLoading.value = true
  try {
    const response = await getTravelTracks()
    availableTracks.value = response.data || []
  } catch {
    availableTracks.value = []
  } finally {
    trackLoading.value = false
  }
}

const openPostComposer = () => {
  if (!requireLogin()) return
  showPostComposer.value = true
  if (!availableTracks.value.length) {
    void loadAvailableTracks()
  }
}

const closePostComposer = () => {
  showPostComposer.value = false
  resetPostDraft()
}

const goPlanner = () => router.push('/planner')
const goLogin = () => router.push('/login')

const openCardDetail = (card: CommunityTripCard) => {
  saveSelectedCommunityCard(card)
  router.push({ name: 'CommunityCardDetail', params: { cardId: card.id } })
}

const requireLogin = () => {
  if (authenticated.value) return true
  message.info('登录后可以参与社区互动')
  router.push('/login')
  return false
}

const openImagePicker = () => {
  if (!requireLogin()) return
  imageInputRef.value?.click()
}

const handleImageFiles = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  target.value = ''
  if (!files.length) return
  if (!requireLogin()) return

  const remainingSlots = Math.max(0, 9 - postDraft.value.imageUrls.length)
  if (!remainingSlots) {
    message.info('最多上传 9 张图片')
    return
  }

  const selectedFiles = files.slice(0, remainingSlots)
  if (files.length > remainingSlots) {
    message.info(`最多上传 9 张图片，已选择前 ${remainingSlots} 张`)
  }

  uploadingImages.value = true
  try {
    for (const file of selectedFiles) {
      const response = await uploadCommunityImage(file)
      if (!response.success || !response.url) {
        throw new Error(response.message || `${file.name} 上传失败`)
      }
      postDraft.value.imageUrls.push(response.url)
    }
    message.success(`已上传 ${selectedFiles.length} 张图片`)
  } catch (error: any) {
    message.error(error.message || '上传图片失败')
  } finally {
    uploadingImages.value = false
  }
}

const removeDraftImage = (index: number) => {
  postDraft.value.imageUrls.splice(index, 1)
}

const resetPostDraft = () => {
  postDraft.value = {
    content: '',
    city: '',
    tagsText: '',
    imageUrls: [],
    linkedTrackId: undefined,
    linkedTrackTitle: '',
  }
}

const handleLinkedTrackChange = (trackId?: string) => {
  const track = availableTracks.value.find((item) => item.id === trackId)
  postDraft.value.linkedTrackTitle = track ? `${track.city} ${track.start_date} - ${track.end_date}` : ''
  if (track && !postDraft.value.city.trim()) {
    postDraft.value.city = track.city
  }
}

const toggleLike = async (card: CommunityTripCard) => {
  if (!requireLogin()) return
  const previous = card.liked_by_me
  try {
    const response = await toggleCommunityCardLike(card.id)
    card.liked_by_me = response.active
    card.like_count += response.active && !previous ? 1 : !response.active && previous ? -1 : 0
  } catch (error: any) {
    message.error(error.message || '更新喜欢状态失败')
  }
}

const toggleFavorite = async (card: CommunityTripCard) => {
  if (!requireLogin()) return
  const previous = card.favorited_by_me
  try {
    const response = await toggleCommunityCardFavorite(card.id)
    card.favorited_by_me = response.active
    card.favorite_count += response.active && !previous ? 1 : !response.active && previous ? -1 : 0
  } catch (error: any) {
    message.error(error.message || '更新收藏状态失败')
  }
}

const submitComment = async (card: CommunityTripCard) => {
  if (!requireLogin()) return
  const content = (commentDrafts.value[card.id] || '').trim()
  if (!content) {
    message.info('先写一点评论内容')
    return
  }
  submittingCommentId.value = card.id
  try {
    const response = await addCommunityCardComment(card.id, content)
    if (!response.success || !response.data) {
      throw new Error(response.message || '发表评论失败')
    }
    card.recent_comments = [response.data, ...card.recent_comments].slice(0, 2)
    card.comment_count += 1
    commentDrafts.value[card.id] = ''
    message.success('评论已发布')
  } catch (error: any) {
    message.error(error.message || '发表评论失败')
  } finally {
    submittingCommentId.value = ''
  }
}

const useCard = async (card: CommunityTripCard) => {
  sessionStorage.setItem('communityPlannerSeed', JSON.stringify(card))
  if (authenticated.value) {
    try {
      await reuseCommunityCard(card.id)
      card.reuse_count += 1
    } catch {
      // The seed is still useful even if the tracking request fails.
    }
  }
  message.success(`已把“${card.title}”作为规划灵感`)
  router.push('/planner')
}

const publishPost = async () => {
  if (!requireLogin()) return
  const content = postDraft.value.content.trim()
  if (!content) {
    message.info('先写一点动态内容')
    return
  }
  publishingPost.value = true
  try {
    const imageUrls = postDraft.value.imageUrls.map((item) => item.trim()).filter(Boolean)
    const tags = postDraft.value.tagsText.split(',').map((item) => item.trim()).filter(Boolean)
    const response = await publishCommunityPost({
      content,
      city: postDraft.value.city.trim(),
      tags,
      image_urls: imageUrls,
      linked_track_id: postDraft.value.linkedTrackId || '',
      linked_track_title: postDraft.value.linkedTrackTitle,
    })
    if (!response.success || !response.data) {
      throw new Error(response.message || '发布动态失败')
    }
    posts.value = [response.data, ...posts.value]
    closePostComposer()
    message.success('动态已发布')
  } catch (error: any) {
    message.error(error.message || '发布动态失败')
  } finally {
    publishingPost.value = false
  }
}

const openPostPlan = async (post: CommunityPost) => {
  if (!requireLogin()) return
  try {
    const response = await getCommunityPostPlan(post.id)
    if (!response.success || !response.data) {
      throw new Error(response.message || '没有找到关联规划')
    }
    sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
    sessionStorage.setItem('tripPlannerSessionId', post.linked_track_id)
    sessionStorage.removeItem('tripPlannerSummary')
    router.push({ path: '/result', query: { postId: post.id, trackId: post.linked_track_id } })
  } catch (error: any) {
    message.error(error.message || '打开关联规划失败')
  }
}

const togglePostLike = async (post: CommunityPost) => {
  if (!requireLogin()) return
  const previous = post.liked_by_me
  try {
    const response = await toggleCommunityPostLike(post.id)
    post.liked_by_me = response.active
    post.like_count += response.active && !previous ? 1 : !response.active && previous ? -1 : 0
  } catch (error: any) {
    message.error(error.message || '更新动态喜欢失败')
  }
}

const submitPostComment = async (post: CommunityPost) => {
  if (!requireLogin()) return
  const content = (postCommentDrafts.value[post.id] || '').trim()
  if (!content) {
    message.info('先写一点评论内容')
    return
  }
  const replyTarget = postReplyTargets.value[post.id]
  const payloadContent = replyTarget ? `回复 ${replyTarget.author_name}：${content}` : content
  if (payloadContent.length > 300) {
    message.info('评论内容过长，请精简后再发送')
    return
  }
  submittingPostCommentId.value = post.id
  try {
    const response = await addCommunityPostComment(post.id, payloadContent)
    if (!response.success || !response.data) {
      throw new Error(response.message || '评论动态失败')
    }
    post.recent_comments = [response.data, ...post.recent_comments].slice(0, 3)
    post.comment_count += 1
    postCommentDrafts.value[post.id] = ''
    postReplyTargets.value[post.id] = null
    message.success('评论已发布')
  } catch (error: any) {
    message.error(error.message || '评论动态失败')
  } finally {
    submittingPostCommentId.value = ''
  }
}

const startReplyToComment = (post: CommunityPost, comment: { id: string; author_name: string }) => {
  postReplyTargets.value[post.id] = {
    id: comment.id,
    author_name: comment.author_name,
  }
}

const cancelReplyToComment = (postId: string) => {
  postReplyTargets.value[postId] = null
}

const toggleFollow = async (post: CommunityPost) => {
  if (!requireLogin()) return
  try {
    const response = await toggleCommunityAuthorFollow(post.user_id)
    posts.value.forEach((item) => {
      if (item.user_id === post.user_id) {
        item.followed_author = response.active
      }
    })
  } catch (error: any) {
    message.error(error.message || '关注状态更新失败')
  }
}

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80'
}

const formatTime = (value: string) => new Date(value).toLocaleString('zh-CN')
const formatCommentTime = (value: string) => new Date(value).toLocaleString('zh-CN')

watch(displayCards, (cards) => {
  saveCommunityCards(cards)
}, { immediate: true, deep: true })

onMounted(() => {
  void loadFeed()
  void loadPosts()
  void loadAvailableTracks()
})
</script>

<style scoped>
.community-page {
  overflow: visible;
}

.community-shell {
  display: grid;
  gap: 24px;
}

.community-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  gap: 22px;
  align-items: stretch;
  min-height: 360px;
}

.community-hero__copy,
.community-hero__panel,
.community-main,
.community-side-panel {
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 24px 60px rgba(65, 110, 168, 0.14);
  backdrop-filter: blur(18px);
}

.community-hero__copy {
  display: grid;
  align-content: center;
  padding: 42px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.7), rgba(225, 243, 255, 0.28)),
    url("https://images.unsplash.com/photo-1471922694854-ff1b63b20054?auto=format&fit=crop&w=1600&q=80") center/cover !important;
  background-blend-mode: screen;
  overflow: hidden;
}

.community-title {
  max-width: 820px;
  letter-spacing: 0;
}

.community-subtitle {
  max-width: 780px;
}

.community-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.community-hero__panel {
  display: grid;
  align-items: end;
  padding: 26px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.76)),
    url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1000&q=80") center/cover;
}

.community-profile-card {
  display: grid;
  gap: 12px;
  padding: 22px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.72);
}

.community-profile-card__label {
  color: var(--brand-primary);
  font-size: 15px;
  font-weight: 800;
}

.community-profile-card strong {
  color: var(--brand-text);
  font-size: 24px;
  line-height: 1.25;
}

.community-profile-card p,
.community-muted {
  margin: 0;
  color: var(--brand-muted);
  line-height: 1.7;
}

.community-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 22px;
  align-items: start;
}

.community-main,
.community-side-panel {
  padding: 26px;
}

.community-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.community-section-head h2,
.community-side-panel h3 {
  margin: 0 0 8px;
  color: #111111;
  font-weight: 800;
}

.community-section-head p {
  margin: 0;
  color: var(--brand-muted);
}

.community-card-grid {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: calc((100% - 32px) / 3);
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
  scroll-snap-type: x proximity;
  scrollbar-width: thin;
}

.trip-share-card {
  overflow: hidden;
  border: 1px solid rgba(191, 214, 239, 0.76);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 18px 38px rgba(77, 122, 181, 0.12);
  cursor: pointer;
  scroll-snap-align: start;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.trip-share-card:hover,
.trip-share-card:focus-visible {
  transform: translateY(-4px);
  box-shadow: 0 24px 44px rgba(77, 122, 181, 0.16);
}

.trip-share-card:focus-visible {
  outline: 2px solid rgba(29, 93, 155, 0.48);
  outline-offset: 2px;
}

.trip-share-card__media {
  position: relative;
  height: 210px;
  overflow: hidden;
}

.trip-share-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.trip-share-card__score {
  display: none;
}

.trip-share-card__body {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.trip-share-card__topline,
.trip-share-card__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: #5f7893;
  font-size: 14px;
  font-weight: 700;
}

.trip-share-card h3 {
  margin: 0;
  color: #111111;
  font-size: 24px;
  line-height: 1.25;
}

.trip-share-card__subtitle,
.trip-share-card__summary,
.trip-share-card__reason span {
  margin: 0;
  color: var(--brand-muted);
  line-height: 1.7;
}

.trip-share-card__subtitle {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 3.4em;
}

.trip-share-card__summary {
  color: #2f4156;
}

.trip-share-card__hint {
  margin: 0;
  color: #4c6988;
  font-size: 14px;
  font-weight: 700;
}

.community-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.community-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(45, 134, 231, 0.12);
  color: #1d5d9b;
  font-size: 14px;
  font-weight: 800;
}

.community-chip--soft {
  background: rgba(239, 246, 255, 0.92);
  color: #42617f;
}

.trip-share-card__highlights {
  display: none;
}

.trip-share-card__highlights span {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(244, 249, 255, 0.9);
  color: #2f4156;
  font-size: 15px;
  font-weight: 700;
}

.trip-share-card__reason {
  display: none;
}

.trip-share-card__reason strong {
  color: var(--brand-text);
}

.trip-share-card__footer {
  display: none;
}

.trip-share-card__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.trip-share-card__comments {
  display: none;
}

.trip-share-card__comments > strong {
  color: var(--brand-text);
}

.trip-share-card__comment-list {
  display: grid;
  gap: 8px;
}

.trip-share-card__comment-list p,
.trip-share-card__comment-empty {
  margin: 0;
  color: var(--brand-muted);
  font-size: 15px;
  line-height: 1.65;
}

.trip-share-card__comment-list span {
  color: #2f4156;
  font-weight: 800;
}

.trip-share-card__comment-box {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

.community-side {
  display: grid;
  gap: 18px;
}

.community-activity-list,
.community-city-list {
  display: grid;
  gap: 12px;
}

.community-activity {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.58);
}

.community-activity strong {
  color: var(--brand-text);
}

.community-activity p {
  margin: 6px 0 0;
  color: var(--brand-muted);
  line-height: 1.7;
}

.community-city-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.community-city-list span {
  padding: 12px;
  border-radius: 16px;
  background: rgba(244, 249, 255, 0.88);
  color: #2f4156;
  font-weight: 800;
  text-align: center;
}

.moments-layout {
  display: grid;
}

.moments-main {
  padding: 26px;
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 24px 60px rgba(65, 110, 168, 0.14);
  backdrop-filter: blur(18px);
}

.moments-composer,
.moment-card {
  border: 1px solid rgba(191, 214, 239, 0.76);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 18px 38px rgba(77, 122, 181, 0.1);
}

.moments-composer {
  display: grid;
  gap: 14px;
  padding: 20px;
  margin-bottom: 22px;
}

.moments-composer__head {
  display: grid;
  gap: 4px;
}

.moments-composer__head strong {
  color: var(--brand-text);
  font-size: 22px;
}

.moments-composer__head span {
  color: var(--brand-muted);
}

.moments-composer__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.moments-composer__images {
  display: grid;
  gap: 10px;
}

.moments-composer__toolbar,
.moment-card__head,
.moment-card__meta,
.moment-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.moments-composer__toolbar {
  justify-content: space-between;
}

.moments-header-actions,
.moments-composer__toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.moments-composer__file-input {
  display: none;
}

.moments-composer__preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.moments-composer__preview {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  background: rgba(236, 244, 255, 0.92);
  aspect-ratio: 1;
}

.moments-composer__preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.moments-composer__preview-remove {
  position: absolute;
  top: 8px;
  right: 8px;
}

.moments-composer__toolbar-hint {
  align-self: center;
  color: var(--brand-muted);
  font-size: 14px;
}

.moments-feed {
  display: grid;
  gap: 18px;
}

.moment-card {
  display: grid;
  gap: 14px;
  padding: 20px;
}

.moment-card__head {
  align-items: center;
  justify-content: space-between;
}

.moment-card__author {
  display: flex;
  align-items: center;
  gap: 12px;
}

.moment-card__avatar {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 18px;
  font-weight: 800;
  box-shadow: 0 10px 18px rgba(77, 122, 181, 0.16);
}

.moment-card__avatar-image,
.moment-card__comment-avatar-image {
  object-fit: cover;
  display: block;
  border-radius: 8px;
}

.moment-card__avatar-image {
  width: 48px;
  height: 48px;
  box-shadow: 0 10px 18px rgba(77, 122, 181, 0.16);
}

.moment-card__author-meta {
  display: grid;
  gap: 4px;
}

.moment-card__head strong {
  color: var(--brand-text);
  font-size: 20px;
}

.moment-card__head p,
.moment-card__content,
.moment-card__meta,
.moment-card__comments p {
  margin: 0;
  color: var(--brand-muted);
  line-height: 1.7;
}

.moment-card__content {
  color: #2f4156;
  font-size: 17px;
}

.moment-card__plan-link {
  width: fit-content;
  max-width: min(100%, 420px);
  min-height: 40px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  justify-self: start;
  padding: 8px 12px;
  border: 1px solid rgba(45, 134, 231, 0.36);
  border-radius: 8px;
  background: rgba(231, 243, 255, 0.96);
  color: #17324f;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 10px 18px rgba(82, 138, 208, 0.1);
}

.moment-card__plan-link:hover {
  border-color: rgba(45, 134, 231, 0.72);
  background: rgba(218, 237, 255, 0.98);
}

.moment-card__plan-link-label,
.moment-card__plan-link-arrow {
  color: #1d5d9b;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.moment-card__plan-link strong {
  min-width: 0;
  overflow: hidden;
  color: #17324f;
  font-size: 14px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.moment-card__images {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.moment-card__images :deep(.ant-image) {
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 8px;
}

.moment-card__images :deep(.ant-image-img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.moment-card__meta {
  gap: 16px;
  font-size: 15px;
  font-weight: 700;
}

.moment-card__comments {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 8px;
  background: rgba(244, 249, 255, 0.88);
}

.moment-card__comment-item {
  display: grid;
  gap: 4px;
  padding: 10px 12px;
  border: 0;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.78);
  text-align: left;
  cursor: pointer;
}

.moment-card__comment-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.moment-card__comment-avatar,
.moment-card__comment-avatar-image {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
}

.moment-card__comment-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 14px;
  font-weight: 800;
}

.moment-card__comment-meta {
  display: grid;
  gap: 2px;
}

.moment-card__comment-author {
  color: #20364f;
  font-size: 15px;
  font-weight: 800;
}

.moment-card__comment-content,
.moment-card__comment-time {
  line-height: 1.6;
}

.moment-card__comment-content {
  color: #3b4f66;
  font-size: 15px;
  font-weight: 500;
  padding-left: 44px;
}

.moment-card__comment-time {
  color: rgba(129, 145, 164, 0.72);
  font-size: 12px;
  font-weight: 500;
}

.moment-card__replying {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  grid-column: 1 / -1;
  padding: 6px 0 0;
  color: #4c6988;
  font-size: 14px;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .community-hero,
  .community-layout {
    grid-template-columns: 1fr;
  }

  .community-card-grid {
    grid-auto-columns: calc((100% - 16px) / 2);
  }
}

@media (max-width: 760px) {
  .community-hero__copy,
  .community-hero__panel,
  .community-main,
  .community-side-panel {
    padding: 20px;
    border-radius: 22px;
  }

  .community-card-grid {
    grid-auto-columns: minmax(78vw, 1fr);
  }

  .community-section-head {
    display: grid;
  }

  .moments-composer__grid {
    grid-template-columns: 1fr;
  }

  .moment-card__images {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .moment-card__images {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .moment-card__author {
    align-items: flex-start;
  }

  .moment-card__head {
    align-items: flex-start;
  }
}
</style>
