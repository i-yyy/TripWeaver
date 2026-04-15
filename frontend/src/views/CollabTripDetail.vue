<template>
  <div class="brand-page">
    <div class="brand-shell collab-detail">
      <a-spin :spinning="loading">
        <template v-if="trip && draftPlan">
          <section class="collab-detail-hero">
            <div>
              <button class="collab-back" type="button" @click="router.push('/collab')">返回协同行程</button>
              <h1>{{ trip.title }}</h1>
              <p>{{ trip.city }} · {{ trip.start_date }} - {{ trip.end_date }} · 版本 v{{ trip.version }}</p>
            </div>
            <div class="collab-detail-actions">
              <a-button v-if="canInvite" @click="showInviteModal = true">邀请好友</a-button>
              <a-button danger :loading="deleting" @click="deleteCurrentTrip">{{ canInvite ? '删除协同行程' : '退出协同行程' }}</a-button>
              <a-button type="primary" :disabled="!canEdit" :loading="saving" @click="savePlan">保存修改</a-button>
            </div>
          </section>

          <section class="collab-detail-grid">
            <main class="collab-plan-panel">
              <div class="collab-section-head">
                <div>
                  <h2>共创行程内容</h2>
                  <p>{{ canEdit ? '你可以直接编辑每天的安排，保存后会产生一条修改记录。' : '你当前是仅查看成员，可以评论和投票。' }}</p>
                </div>
              </div>

              <div class="collab-overview-grid">
                <div class="collab-stat-card">
                  <span>目的地</span>
                  <strong>{{ draftPlan.city }}</strong>
                </div>
                <div class="collab-stat-card">
                  <span>行程天数</span>
                  <strong>{{ draftPlan.days.length }} 天</strong>
                </div>
                <div v-if="draftPlan.budget" class="collab-stat-card">
                  <span>预算总计</span>
                  <strong>{{ currency(draftPlan.budget.total) }}</strong>
                </div>
                <div class="collab-stat-card">
                  <span>协同版本</span>
                  <strong>v{{ trip.version }}</strong>
                </div>
              </div>

              <section class="collab-advice-card">
                <div>
                  <span>整体建议</span>
                  <p v-if="!canEdit">{{ draftPlan.overall_suggestions || '暂无整体建议' }}</p>
                </div>
                <a-textarea v-if="canEdit" v-model:value="draftPlan.overall_suggestions" :rows="3" />
              </section>

              <div class="collab-day-list">
                <article v-for="day in draftPlan.days" :key="day.day_index" class="collab-day-card">
                  <div class="collab-day-card__head">
                    <div>
                      <span>Day {{ day.day_index + 1 }}</span>
                      <strong>{{ day.date }}</strong>
                    </div>
                    <button class="collab-comment-jump" type="button" @click="commentForm.dayIndex = day.day_index">
                      讨论这一天
                    </button>
                  </div>

                  <div class="collab-day-visual-grid">
                    <section class="collab-info-card collab-info-card--wide">
                      <span>当日概览</span>
                      <a-textarea v-if="canEdit" v-model:value="day.description" :rows="3" />
                      <p v-else>{{ day.description || '暂无安排' }}</p>
                    </section>
                    <section class="collab-info-card">
                      <span>交通方式</span>
                      <a-input v-if="canEdit" v-model:value="day.transportation" />
                      <strong v-else>{{ day.transportation || '暂无' }}</strong>
                    </section>
                    <section class="collab-info-card">
                      <span>住宿方式</span>
                      <a-input v-if="canEdit" v-model:value="day.accommodation" />
                      <strong v-else>{{ day.accommodation || '暂无' }}</strong>
                    </section>
                    <section class="collab-info-card collab-info-card--wide">
                      <span>交通说明</span>
                      <a-textarea v-if="canEdit" v-model:value="day.transportation_detail" :rows="2" />
                      <p v-else>{{ day.transportation_detail || '暂无交通说明' }}</p>
                    </section>
                    <section class="collab-info-card collab-info-card--wide">
                      <span>路线备注</span>
                      <a-textarea v-if="canEdit" v-model:value="day.route_summary" :rows="2" />
                      <p v-else>{{ day.route_summary || '暂无路线备注' }}</p>
                    </section>
                  </div>

                  <section v-if="day.hotel" class="collab-hotel-card">
                    <div class="collab-subtitle">酒店安排</div>
                    <div class="collab-hotel-card__body">
                      <div>
                        <strong>{{ day.hotel.name }}</strong>
                        <p>{{ day.hotel.address || '暂无地址' }}</p>
                      </div>
                      <div class="collab-mini-metrics">
                        <span>{{ day.hotel.type || '住宿' }}</span>
                        <span>{{ day.hotel.rating || '暂无评分' }}</span>
                        <span>{{ currency(day.hotel.estimated_cost || 0) }}/晚</span>
                      </div>
                    </div>
                  </section>

                  <section v-if="day.attractions.length" class="collab-attraction-list">
                    <div class="collab-subtitle">景点安排与投票</div>
                    <article v-for="(attraction, index) in day.attractions" :key="targetId(day.day_index, attraction, index)" class="collab-attraction-row">
                      <img
                        class="collab-attraction-row__image"
                        :src="resolveAttractionImage(attraction)"
                        :alt="attraction.name"
                        @error="handleImageError"
                      />
                      <div class="collab-attraction-row__content">
                        <div>
                          <strong>{{ index + 1 }}. {{ attraction.name }}</strong>
                          <p>{{ attraction.address || '暂无地址' }}</p>
                        </div>
                        <div class="collab-mini-metrics">
                          <span>{{ attraction.visit_duration || 0 }} 分钟</span>
                          <span>{{ currency(attraction.ticket_price || 0) }}</span>
                          <span>想去 {{ voteCount(targetId(day.day_index, attraction, index)) }}</span>
                        </div>
                        <p class="collab-attraction-row__desc">{{ attraction.description || '暂无说明' }}</p>
                        <div v-if="canEdit" class="collab-attraction-edit">
                          <a-input v-model:value="attraction.address" placeholder="景点地址" />
                          <a-input-number v-model:value="attraction.visit_duration" :min="10" :max="480" addon-after="分钟" />
                          <a-input-number v-model:value="attraction.ticket_price" :min="0" addon-before="￥" />
                          <a-textarea v-model:value="attraction.description" :rows="2" placeholder="景点说明" />
                        </div>
                        <div class="collab-card-actions">
                          <a-button size="small" :disabled="!canEdit || index === 0" @click="moveAttraction(day.day_index, index, -1)">上移</a-button>
                          <a-button size="small" :disabled="!canEdit || index === day.attractions.length - 1" @click="moveAttraction(day.day_index, index, 1)">下移</a-button>
                          <a-button size="small" :type="hasVoted(targetId(day.day_index, attraction, index)) ? 'primary' : 'default'" @click="toggleVote(targetId(day.day_index, attraction, index))">
                            想去 {{ voteCount(targetId(day.day_index, attraction, index)) }}
                          </a-button>
                        </div>
                      </div>
                    </article>
                  </section>

                  <section v-if="day.meals.length" class="collab-meal-list">
                    <div class="collab-subtitle">餐饮安排</div>
                    <article v-for="meal in day.meals" :key="`${day.day_index}-${meal.type}-${meal.name}`" class="collab-meal-card">
                      <strong>{{ mealLabel(meal.type) }} · {{ meal.name }}</strong>
                      <p>{{ meal.description || '暂无推荐理由' }}</p>
                      <span>{{ currency(meal.estimated_cost || 0) }}</span>
                    </article>
                  </section>
                </article>
              </div>
            </main>

            <aside class="collab-side-panel">
              <section>
                <h2>成员</h2>
                <div class="collab-member-list">
                  <article v-for="member in activeMembers" :key="member.id" class="collab-user-row">
                    <img v-if="member.user.avatar_url" :src="resolveMediaUrl(member.user.avatar_url)" :alt="`${member.user.nickname} 的头像`" />
                    <div v-else class="collab-user-row__avatar" :style="avatarStyle(member.user.nickname)">{{ avatarText(member.user.nickname) }}</div>
                    <div>
                      <strong>{{ member.user.nickname }}</strong>
                      <p>{{ roleLabel(member.role) }}</p>
                    </div>
                  </article>
                </div>
              </section>

              <section>
                <h2>讨论</h2>
                <a-form layout="vertical">
                  <a-form-item label="关联到哪一天">
                    <a-select v-model:value="commentForm.dayIndex" allow-clear placeholder="整份行程">
                      <a-select-option v-for="day in draftPlan.days" :key="day.day_index" :value="day.day_index">
                        第 {{ day.day_index + 1 }} 天
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item>
                    <a-textarea v-model:value="commentForm.content" :rows="3" placeholder="写下你的建议" />
                  </a-form-item>
                  <a-button type="primary" :loading="commenting" @click="submitComment">发送评论</a-button>
                </a-form>
                <div class="collab-comment-list">
                  <article v-for="comment in trip.comments" :key="comment.id" class="collab-comment">
                    <div class="collab-comment__head">
                      <strong>{{ comment.user.nickname }}</strong>
                      <span>{{ comment.day_index == null ? '整份行程' : `第 ${comment.day_index + 1} 天` }} · {{ formatTime(comment.created_at) }}</span>
                    </div>
                    <p>{{ comment.content }}</p>
                  </article>
                </div>
              </section>

              <section>
                <h2>修改记录</h2>
                <div class="collab-change-list">
                  <article v-for="change in trip.changes" :key="change.id" class="collab-change">
                    <strong>{{ change.summary }}</strong>
                    <p>{{ change.user.nickname }} · {{ formatTime(change.created_at) }}</p>
                  </article>
                </div>
              </section>
            </aside>
          </section>
        </template>

        <a-empty v-else-if="!loading" description="没有找到协同行程" />
      </a-spin>

      <a-modal
        v-model:open="showInviteModal"
        title="邀请好友加入"
        ok-text="发送邀请"
        cancel-text="取消"
        :confirm-loading="inviting"
        @ok="sendInvite"
      >
        <a-form layout="vertical">
          <a-form-item label="好友邮箱或昵称">
            <a-input v-model:value="inviteForm.identifier" placeholder="输入好友注册邮箱或昵称" />
          </a-form-item>
          <a-form-item label="权限">
            <a-select v-model:value="inviteForm.role">
              <a-select-option value="editor">可编辑</a-select-option>
              <a-select-option value="viewer">仅查看</a-select-option>
            </a-select>
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import {
  addCollabTripComment,
  deleteCollabTrip,
  getCollabTrip,
  inviteCollabTripMember,
  resolveMediaUrl,
  updateCollabTripPlan,
  voteCollabTripItem,
} from '@/services/api'
import type { Attraction, CollabTripDetail, TripPlan } from '@/types'
import { avatarStyle, avatarText } from '@/utils/avatar'
import { useAuthState } from '@/utils/auth'

const route = useRoute()
const router = useRouter()
const authState = useAuthState()
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const inviting = ref(false)
const commenting = ref(false)
const showInviteModal = ref(false)
const trip = ref<CollabTripDetail | null>(null)
const draftPlan = ref<TripPlan | null>(null)

const inviteForm = reactive({
  identifier: '',
  role: 'editor',
})

const commentForm = reactive({
  dayIndex: undefined as number | undefined,
  content: '',
})

const tripId = computed(() => String(route.params.tripId || ''))
const canEdit = computed(() => ['owner', 'editor'].includes(trip.value?.my_role || ''))
const canInvite = computed(() => trip.value?.my_role === 'owner')
const activeMembers = computed(() => trip.value?.members.filter((item) => item.status === 'active') || [])

const loadTrip = async () => {
  if (!tripId.value) return
  loading.value = true
  try {
    const response = await getCollabTrip(tripId.value)
    if (!response.success || !response.data) {
      throw new Error(response.message || '获取协同行程失败')
    }
    trip.value = response.data
    draftPlan.value = structuredClone(response.data.plan_json)
  } catch (error: any) {
    message.error(error.message || '获取协同行程失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadTrip)

const savePlan = async () => {
  if (!draftPlan.value || !trip.value) return
  saving.value = true
  try {
    const response = await updateCollabTripPlan(trip.value.id, {
      plan_json: draftPlan.value as unknown as Record<string, unknown>,
      summary: '更新了行程内容和每日安排',
    })
    if (!response.success || !response.data) {
      throw new Error(response.message || '保存失败')
    }
    trip.value = response.data
    draftPlan.value = structuredClone(response.data.plan_json)
    message.success('协同行程已保存')
  } catch (error: any) {
    message.error(error.message || '保存协同行程失败')
  } finally {
    saving.value = false
  }
}

const deleteCurrentTrip = async () => {
  if (!trip.value) return
  const actionText = canInvite.value ? '删除' : '退出'
  const confirmed = window.confirm(`确定要${actionText}「${trip.value.title}」吗？`)
  if (!confirmed) return
  deleting.value = true
  try {
    await deleteCollabTrip(trip.value.id)
    message.success(canInvite.value ? '协同行程已删除' : '已退出协同行程')
    router.replace('/collab')
  } catch (error: any) {
    message.error(error.message || `${actionText}协同行程失败`)
  } finally {
    deleting.value = false
  }
}

const sendInvite = async () => {
  if (!trip.value) return
  if (!inviteForm.identifier.trim()) {
    message.error('请输入好友邮箱或昵称')
    return
  }
  inviting.value = true
  try {
    await inviteCollabTripMember(trip.value.id, {
      identifier: inviteForm.identifier.trim(),
      role: inviteForm.role,
    })
    inviteForm.identifier = ''
    inviteForm.role = 'editor'
    showInviteModal.value = false
    message.success('邀请已发送')
    await loadTrip()
  } catch (error: any) {
    message.error(error.message || '邀请好友失败')
  } finally {
    inviting.value = false
  }
}

const submitComment = async () => {
  if (!trip.value) return
  if (!commentForm.content.trim()) {
    message.error('请输入评论内容')
    return
  }
  commenting.value = true
  try {
    await addCollabTripComment(trip.value.id, {
      content: commentForm.content.trim(),
      day_index: commentForm.dayIndex ?? null,
    })
    commentForm.content = ''
    commentForm.dayIndex = undefined
    await loadTrip()
    message.success('评论已发送')
  } catch (error: any) {
    message.error(error.message || '发送评论失败')
  } finally {
    commenting.value = false
  }
}

const toggleVote = async (targetIdValue: string) => {
  if (!trip.value) return
  try {
    await voteCollabTripItem(trip.value.id, {
      target_type: 'attraction',
      target_id: targetIdValue,
      vote_type: 'want',
    })
    await loadTrip()
  } catch (error: any) {
    message.error(error.message || '投票失败')
  }
}

const moveAttraction = (dayIndex: number, index: number, direction: -1 | 1) => {
  if (!draftPlan.value) return
  const day = draftPlan.value.days.find((item) => item.day_index === dayIndex)
  if (!day) return
  const nextIndex = index + direction
  if (nextIndex < 0 || nextIndex >= day.attractions.length) return
  const nextAttractions = [...day.attractions]
  const [item] = nextAttractions.splice(index, 1)
  nextAttractions.splice(nextIndex, 0, item)
  day.attractions = nextAttractions
}

const targetId = (dayIndex: number, attraction: Attraction, index: number) =>
  `${dayIndex}:${attraction.poi_id || attraction.name || index}`

const voteCount = (targetIdValue: string) =>
  trip.value?.votes.filter((item) => item.target_type === 'attraction' && item.target_id === targetIdValue && item.vote_type === 'want').length || 0

const hasVoted = (targetIdValue: string) => {
  return Boolean(
    trip.value?.votes.some(
      (item) =>
        item.target_type === 'attraction' &&
        item.target_id === targetIdValue &&
        item.vote_type === 'want' &&
        item.user_id === authState.user?.id,
    ),
  )
}

const resolveAttractionImage = (attraction: Attraction) => {
  const image = attraction.image_url || attraction.map_image_url || attraction.photos?.[0]
  return resolveMediaUrl(image || `https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80`)
}

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80'
}

const currency = (value?: number) => `¥${Number(value || 0).toLocaleString('zh-CN')}`

const mealLabel = (type?: string) => {
  const labels: Record<string, string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '加餐',
  }
  return labels[type || ''] || '餐饮'
}

const roleLabel = (role: string) => {
  const labels: Record<string, string> = {
    owner: '管理员',
    editor: '可编辑',
    viewer: '仅查看',
  }
  return labels[role] || role
}

const formatTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.collab-detail {
  display: grid;
  gap: 24px;
}

.collab-detail-hero,
.collab-plan-panel,
.collab-side-panel section {
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 24px 60px rgba(65, 110, 168, 0.14);
  backdrop-filter: blur(18px);
}

.collab-detail-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 36px;
  background: #eaf5ff;
  overflow: hidden;
}

.collab-back {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--brand-primary);
  font-weight: 800;
  cursor: pointer;
}

.collab-detail-hero h1,
.collab-section-head h2,
.collab-side-panel h2,
.collab-day-card__head strong,
.collab-attraction-row strong,
.collab-comment strong,
.collab-change strong {
  margin: 0;
  color: #111111;
  font-weight: 800;
}

.collab-detail-hero h1 {
  margin-top: 10px;
  font-size: 34px;
  line-height: 1.2;
}

.collab-detail-hero p,
.collab-section-head p,
.collab-attraction-row p,
.collab-user-row p,
.collab-comment p,
.collab-change p {
  margin: 0;
  color: var(--brand-muted);
  line-height: 1.65;
}

.collab-detail-actions,
.collab-card-actions,
.collab-day-card__head,
.collab-comment__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.collab-detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 22px;
  align-items: start;
}

.collab-plan-panel,
.collab-side-panel section {
  padding: 26px;
}

.collab-side-panel {
  display: grid;
  gap: 18px;
}

.collab-section-head {
  margin-bottom: 18px;
}

.collab-day-list,
.collab-member-list,
.collab-comment-list,
.collab-change-list,
.collab-attraction-list,
.collab-meal-list {
  display: grid;
  gap: 12px;
}

.collab-day-card,
.collab-attraction-row,
.collab-hotel-card,
.collab-info-card,
.collab-meal-card,
.collab-advice-card,
.collab-stat-card,
.collab-user-row,
.collab-comment,
.collab-change {
  border: 1px solid rgba(82, 138, 208, 0.18);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 18px 38px rgba(77, 122, 181, 0.1);
}

.collab-day-card {
  display: grid;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
}

.collab-overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.collab-stat-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  background: rgba(239, 246, 255, 0.92);
}

.collab-stat-card span,
.collab-advice-card span,
.collab-info-card span {
  color: var(--brand-primary);
  font-size: 13px;
  font-weight: 800;
}

.collab-stat-card strong {
  overflow-wrap: anywhere;
  color: var(--brand-text);
  font-size: 22px;
}

.collab-advice-card {
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.86);
}

.collab-advice-card p,
.collab-info-card p {
  margin: 8px 0 0;
  color: #2f4156;
  line-height: 1.7;
}

.collab-day-visual-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.collab-info-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  background: rgba(239, 246, 255, 0.72);
}

.collab-info-card strong {
  color: var(--brand-text);
  font-size: 18px;
}

.collab-info-card--wide {
  grid-column: 1 / -1;
}

.collab-day-card__head span,
.collab-subtitle {
  color: var(--brand-primary);
  font-size: 13px;
  font-weight: 800;
}

.collab-comment-jump {
  min-height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(45, 134, 231, 0.28);
  border-radius: 999px;
  background: #ffffff;
  color: var(--brand-primary);
  font-weight: 800;
  cursor: pointer;
}

.collab-hotel-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  background: rgba(239, 246, 255, 0.74);
}

.collab-hotel-card__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
}

.collab-hotel-card strong,
.collab-meal-card strong {
  color: var(--brand-text);
  font-size: 17px;
}

.collab-hotel-card p,
.collab-meal-card p {
  margin: 6px 0 0;
  color: var(--brand-muted);
  line-height: 1.6;
}

.collab-mini-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.collab-mini-metrics span {
  padding: 5px 9px;
  border-radius: 999px;
  background: rgba(45, 134, 231, 0.12);
  color: #1d5d9b;
  font-size: 13px;
  font-weight: 800;
}

.collab-attraction-row {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr);
  align-items: stretch;
  gap: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.9);
}

.collab-attraction-row__image {
  width: 100%;
  height: 100%;
  min-height: 132px;
  border-radius: 18px;
  object-fit: cover;
}

.collab-attraction-row__content {
  min-width: 0;
  display: grid;
  gap: 10px;
}

.collab-attraction-row__desc {
  margin: 0;
  color: #2f4156;
  line-height: 1.65;
}

.collab-attraction-edit {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px 120px;
  gap: 8px;
}

.collab-attraction-edit :deep(.ant-input-textarea) {
  grid-column: 1 / -1;
}

.collab-meal-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.collab-meal-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.86);
}

.collab-meal-card span {
  width: fit-content;
  padding: 5px 9px;
  border-radius: 999px;
  background: rgba(45, 134, 231, 0.12);
  color: #1d5d9b;
  font-weight: 800;
}

.collab-user-row {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  padding: 12px;
}

.collab-user-row img,
.collab-user-row__avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
}

.collab-user-row img {
  display: block;
  object-fit: cover;
}

.collab-user-row__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
}

.collab-comment,
.collab-change {
  padding: 12px;
}

.collab-comment__head {
  margin-bottom: 6px;
}

.collab-comment__head span,
.collab-change p {
  color: #9aa7b5;
  font-size: 12px;
  font-weight: 700;
}

@media (max-width: 1050px) {
  .collab-detail-grid {
    grid-template-columns: 1fr;
  }

  .collab-overview-grid,
  .collab-meal-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .collab-detail-hero,
  .collab-detail-actions,
  .collab-day-card__head,
  .collab-attraction-row,
  .collab-hotel-card__body {
    display: grid;
  }

  .collab-overview-grid,
  .collab-day-visual-grid,
  .collab-meal-list,
  .collab-attraction-edit {
    grid-template-columns: 1fr;
  }
}
</style>
