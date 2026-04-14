<template>
  <div class="brand-page community-detail-page">
    <div class="brand-shell community-detail-shell">
      <section class="community-detail-hero">
        <a-button class="community-detail-back" @click="goBack">返回社区</a-button>
        <a-empty v-if="!card && !loading" description="没有找到这张推荐卡片" />
        <a-spin :spinning="loading">
          <div v-if="card" class="community-detail-card">
            <div class="community-detail-card__media">
              <img :src="card.cover_image_url" :alt="card.title" @error="handleImageError" />
              <div class="community-detail-card__score">匹配 {{ Math.round(card.match_score * 100) }}%</div>
            </div>

            <div class="community-detail-card__body">
              <div class="community-detail-card__topline">
                <span>{{ card.city }} · {{ card.days }} 天</span>
                <span>{{ budgetLabel(card.estimated_budget) }}</span>
                <span>{{ card.author_name }}</span>
              </div>

              <div class="community-detail-card__heading">
                <h1>{{ card.title }}</h1>
                <p>{{ card.subtitle }}</p>
              </div>

              <p class="community-detail-card__summary">{{ card.summary }}</p>

              <div class="community-chip-row">
                <span v-for="tag in card.tags" :key="`${card.id}-${tag}`" class="community-chip community-chip--soft">
                  {{ tagLabel(tag) }}
                </span>
              </div>

              <section class="community-detail-section">
                <strong>路线亮点</strong>
                <div class="community-detail-highlights">
                  <span v-for="item in card.highlights" :key="`${card.id}-${item}`">{{ item }}</span>
                </div>
              </section>

              <section class="community-detail-section community-detail-reason">
                <strong>为什么推荐给你</strong>
                <p>{{ card.match_reasons.join('，') }}</p>
              </section>

              <div class="community-detail-metrics">
                <span>{{ card.like_count }} 喜欢</span>
                <span>{{ card.favorite_count }} 收藏</span>
                <span>{{ card.comment_count }} 评论</span>
                <span>{{ card.reuse_count }} 复用</span>
              </div>

              <div class="community-detail-actions">
                <a-button size="large" @click="toggleLike">{{ card.liked_by_me ? '已喜欢' : '喜欢' }}</a-button>
                <a-button size="large" @click="toggleFavorite">{{ card.favorited_by_me ? '已收藏' : '收藏' }}</a-button>
                <a-button size="large" type="primary" @click="useCard">用它规划</a-button>
              </div>

              <section class="community-detail-comments">
                <div class="community-detail-comments__head">
                  <strong>社区交流</strong>
                  <span>{{ card.comment_count }} 条评论</span>
                </div>

                <div v-if="card.recent_comments.length" class="community-detail-comment-list">
                  <div v-for="comment in card.recent_comments" :key="comment.id" class="community-detail-comment-item">
                    <img
                      v-if="comment.author_avatar_url"
                      class="community-detail-comment-avatar-image"
                      :src="resolveMediaUrl(comment.author_avatar_url)"
                      :alt="`${comment.author_name} 的头像`"
                      @error="handleImageError"
                    />
                    <div
                      v-else
                      class="community-detail-comment-avatar"
                      :style="avatarStyle(comment.author_name)"
                    >
                      {{ avatarText(comment.author_name) }}
                    </div>
                    <div class="community-detail-comment-meta">
                      <div class="community-detail-comment-topline">
                        <span>{{ comment.author_name }}</span>
                        <small>{{ formatTime(comment.created_at) }}</small>
                      </div>
                      <p>{{ comment.content }}</p>
                    </div>
                  </div>
                </div>
                <p v-else class="community-detail-comment-empty">还没有评论，来补一句真实感受。</p>

                <div v-if="authenticated" class="community-detail-comment-box">
                  <a-input
                    v-model:value="commentDraft"
                    placeholder="写一句你的看法"
                    :maxlength="300"
                    @pressEnter="submitComment"
                  />
                  <a-button size="small" :loading="submittingComment" @click="submitComment">发送</a-button>
                </div>
                <p v-else class="community-detail-comment-empty">登录后可以参与路线交流。</p>
              </section>
            </div>
          </div>
        </a-spin>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import {
  addCommunityCardComment,
  getCommunityFeed,
  resolveMediaUrl,
  reuseCommunityCard,
  toggleCommunityCardFavorite,
  toggleCommunityCardLike,
} from '@/services/api'
import type { CommunityTripCard } from '@/types'
import { useAuthState } from '@/utils/auth'
import { avatarStyle, avatarText } from '@/utils/avatar'
import { readCommunityCards, readSelectedCommunityCard, saveCommunityCards, upsertStoredCommunityCard } from '@/utils/communityCards'

const route = useRoute()
const router = useRouter()
const authState = useAuthState()

const loading = ref(false)
const submittingComment = ref(false)
const commentDraft = ref('')
const card = ref<CommunityTripCard | null>(null)

const authenticated = computed(() => Boolean(authState.token && authState.user))
const cardId = computed(() => String(route.params.cardId || ''))

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

const requireLogin = () => {
  if (authenticated.value) return true
  message.info('登录后可以参与社区互动')
  router.push('/login')
  return false
}

const syncCard = (nextCard: CommunityTripCard) => {
  card.value = nextCard
  upsertStoredCommunityCard(nextCard)
}

const loadCard = async () => {
  const cachedCard = readSelectedCommunityCard(cardId.value)
    || readCommunityCards().find((item) => item.id === cardId.value)
  if (cachedCard) {
    card.value = cachedCard
  }

  if (!authenticated.value) return

  loading.value = true
  try {
    const response = await getCommunityFeed(20)
    if (!response.success) {
      throw new Error(response.message || '获取推荐详情失败')
    }
    saveCommunityCards(response.data.cards)
    const matched = response.data.cards.find((item) => item.id === cardId.value)
    if (matched) {
      syncCard(matched)
    }
  } catch (error: any) {
    if (!card.value) {
      message.warning(error.message || '获取推荐详情失败')
    }
  } finally {
    loading.value = false
  }
}

const toggleLike = async () => {
  if (!card.value || !requireLogin()) return
  const previous = card.value.liked_by_me
  try {
    const response = await toggleCommunityCardLike(card.value.id)
    syncCard({
      ...card.value,
      liked_by_me: response.active,
      like_count: card.value.like_count + (response.active && !previous ? 1 : !response.active && previous ? -1 : 0),
    })
  } catch (error: any) {
    message.error(error.message || '更新喜欢状态失败')
  }
}

const toggleFavorite = async () => {
  if (!card.value || !requireLogin()) return
  const previous = card.value.favorited_by_me
  try {
    const response = await toggleCommunityCardFavorite(card.value.id)
    syncCard({
      ...card.value,
      favorited_by_me: response.active,
      favorite_count: card.value.favorite_count + (response.active && !previous ? 1 : !response.active && previous ? -1 : 0),
    })
  } catch (error: any) {
    message.error(error.message || '更新收藏状态失败')
  }
}

const submitComment = async () => {
  if (!card.value || !requireLogin()) return
  const content = commentDraft.value.trim()
  if (!content) {
    message.info('先写一点评论内容')
    return
  }
  submittingComment.value = true
  try {
    const response = await addCommunityCardComment(card.value.id, content)
    if (!response.success || !response.data) {
      throw new Error(response.message || '发表评论失败')
    }
    syncCard({
      ...card.value,
      comment_count: card.value.comment_count + 1,
      recent_comments: [response.data, ...card.value.recent_comments].slice(0, 5),
    })
    commentDraft.value = ''
    message.success('评论已发布')
  } catch (error: any) {
    message.error(error.message || '发表评论失败')
  } finally {
    submittingComment.value = false
  }
}

const useCard = async () => {
  if (!card.value) return
  sessionStorage.setItem('communityPlannerSeed', JSON.stringify(card.value))
  if (authenticated.value) {
    try {
      await reuseCommunityCard(card.value.id)
      syncCard({
        ...card.value,
        reuse_count: card.value.reuse_count + 1,
      })
    } catch {
      // Planner seed is still useful even if tracking fails.
    }
  }
  message.success(`已把“${card.value.title}”作为规划灵感`)
  router.push('/planner')
}

const goBack = () => router.push('/')

const formatTime = (value: string) => new Date(value).toLocaleString('zh-CN')

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80'
}

onMounted(() => {
  void loadCard()
})
</script>

<style scoped>
.community-detail-shell {
  display: grid;
}

.community-detail-hero {
  display: grid;
  gap: 18px;
}

.community-detail-back {
  justify-self: start;
}

.community-detail-card {
  display: grid;
  grid-template-columns: minmax(320px, 460px) minmax(0, 1fr);
  gap: 22px;
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 24px 60px rgba(65, 110, 168, 0.14);
  backdrop-filter: blur(18px);
  overflow: hidden;
}

.community-detail-card__media {
  position: relative;
  min-height: 420px;
}

.community-detail-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.community-detail-card__score {
  position: absolute;
  top: 18px;
  right: 18px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #1d5d9b;
  font-size: 14px;
  font-weight: 800;
}

.community-detail-card__body {
  display: grid;
  gap: 18px;
  padding: 28px;
}

.community-detail-card__topline,
.community-detail-metrics,
.community-detail-actions,
.community-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.community-detail-card__topline,
.community-detail-metrics {
  color: #5f7893;
  font-size: 14px;
  font-weight: 700;
}

.community-detail-card__heading {
  display: grid;
  gap: 8px;
}

.community-detail-card__heading h1 {
  margin: 0;
  color: #111111;
  font-size: 32px;
  line-height: 1.2;
}

.community-detail-card__heading p,
.community-detail-card__summary,
.community-detail-reason p,
.community-detail-comment-list p,
.community-detail-comment-empty {
  margin: 0;
  color: var(--brand-muted);
  line-height: 1.7;
}

.community-detail-card__summary {
  color: #2f4156;
  font-size: 17px;
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

.community-detail-section {
  display: grid;
  gap: 12px;
}

.community-detail-section strong,
.community-detail-comments__head strong {
  color: var(--brand-text);
}

.community-detail-highlights {
  display: grid;
  gap: 8px;
}

.community-detail-highlights span {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(244, 249, 255, 0.9);
  color: #2f4156;
  font-size: 15px;
  font-weight: 700;
}

.community-detail-reason {
  padding: 16px;
  border-radius: 8px;
  background: rgba(231, 243, 255, 0.72);
}

.community-detail-comments {
  display: grid;
  gap: 12px;
  padding: 18px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(208, 225, 243, 0.78);
}

.community-detail-comments__head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #5f7893;
  font-size: 14px;
  font-weight: 700;
}

.community-detail-comment-list {
  display: grid;
  gap: 8px;
}

.community-detail-comment-item {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
}

.community-detail-comment-avatar,
.community-detail-comment-avatar-image {
  width: 38px;
  height: 38px;
  border-radius: 8px;
}

.community-detail-comment-avatar-image {
  object-fit: cover;
  display: block;
}

.community-detail-comment-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 14px;
  font-weight: 800;
}

.community-detail-comment-meta {
  display: grid;
  gap: 4px;
}

.community-detail-comment-topline {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
}

.community-detail-comment-topline span {
  color: #20364f;
  font-size: 15px;
  font-weight: 800;
}

.community-detail-comment-topline small {
  color: rgba(129, 145, 164, 0.72);
  font-size: 12px;
  font-weight: 500;
}

.community-detail-comment-meta p {
  color: #3b4f66;
  font-size: 15px;
  font-weight: 500;
}

.community-detail-comment-box {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

@media (max-width: 980px) {
  .community-detail-card {
    grid-template-columns: 1fr;
  }

  .community-detail-card__media {
    min-height: 280px;
  }
}

@media (max-width: 640px) {
  .community-detail-card__body {
    padding: 20px;
  }

  .community-detail-card__heading h1 {
    font-size: 26px;
  }

  .community-detail-comment-box {
    grid-template-columns: 1fr;
  }
}
</style>
