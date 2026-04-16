<template>
  <div class="brand-page">
    <div class="brand-shell collab-detail">
      <a-spin :spinning="loading">
        <template v-if="trip && draftPlan">
          <div class="glass-toolbar collab-result-toolbar">
            <div class="toolbar-group">
              <a-button size="large" @click="router.push('/collab')">↩️ 返回协同行程</a-button>
            </div>
            <div class="toolbar-group">
              <a-button v-if="canInvite" @click="showInviteModal = true">👥 邀请好友</a-button>
              <a-button danger :loading="deleting" @click="deleteCurrentTrip">{{ canInvite ? '删除协同行程' : '退出协同行程' }}</a-button>
              <a-button type="primary" :disabled="!canEdit" :loading="saving" @click="savePlan">💾 保存修改</a-button>
            </div>
          </div>

          <section class="glass-panel collab-result-hero">
            <span class="page-kicker">🤝 协同行程</span>
            <h1 class="page-title collab-result-title">{{ trip.title }}</h1>
            <p class="collab-result-meta">{{ trip.city }}｜{{ trip.start_date }} - {{ trip.end_date }}｜版本 v{{ trip.version }}</p>
            <div class="collab-result-tags">
              <span>{{ roleLabel(trip.my_role) }}</span>
              <span>{{ activeMembers.length }} 位成员</span>
              <span>{{ canEdit ? '可编辑' : '仅查看' }}</span>
            </div>
          </section>

          <section v-if="draftPlan.budget" class="glass-panel glass-panel--soft collab-result-panel">
            <div class="section-heading">
              <h2>💰 预算汇总</h2>
              <p>费用为参考估算，保存修改后会同步到这份协同行程中。</p>
            </div>
            <div class="collab-budget-grid">
              <div class="brand-stat">
                <span>📍 景点</span>
                <strong>{{ currency(draftPlan.budget.total_attractions) }}</strong>
              </div>
              <div class="brand-stat">
                <span>🏨 酒店</span>
                <strong>{{ currency(draftPlan.budget.total_hotels) }}</strong>
              </div>
              <div class="brand-stat">
                <span>🍽️ 餐饮</span>
                <strong>{{ currency(draftPlan.budget.total_meals) }}</strong>
              </div>
              <div class="brand-stat">
                <span>🚇 交通</span>
                <strong>{{ currency(draftPlan.budget.total_transportation) }}</strong>
              </div>
              <div class="brand-stat budget-total">
                <span>🧾 总计</span>
                <strong>{{ currency(draftPlan.budget.total) }}</strong>
              </div>
            </div>
          </section>

          <section class="glass-panel glass-panel--soft collab-result-panel">
            <div class="section-heading">
              <h2>🗓️ 每日行程</h2>
              <p>{{ canEdit ? '像旅行规划结果页一样浏览行程，并直接编辑景点、餐食、交通和住宿。' : '你当前只有查看权限，可以浏览行程并为景点投票。' }}</p>
            </div>

            <section class="collab-advice-card">
              <div>
                <span>整体建议</span>
                <p v-if="!canEdit">{{ draftPlan.overall_suggestions || '暂无整体建议' }}</p>
              </div>
              <a-textarea v-if="canEdit" v-model:value="draftPlan.overall_suggestions" :rows="3" placeholder="填写整体建议" />
            </section>

            <a-collapse ghost>
              <a-collapse-panel
                v-for="day in draftPlan.days"
                :key="String(day.day_index)"
                :header="`第 ${day.day_index + 1} 天 · ${day.date}`"
              >
                <div class="collab-day-layout">
                  <div class="entity-card collab-day-summary-card">
                    <div class="section-heading compact-heading">
                      <h3>📝 每日行程</h3>
                    </div>
                    <div class="collab-day-summary">
                      <label>
                        <strong>当日概览</strong>
                        <a-textarea v-if="canEdit" v-model:value="day.description" :rows="3" placeholder="填写当天行程概览" />
                        <span v-else>{{ day.description || '暂无安排' }}</span>
                      </label>
                      <label>
                        <strong>交通方式</strong>
                        <a-input v-if="canEdit" v-model:value="day.transportation" placeholder="例如：地铁、步行、打车" />
                        <span v-else>{{ day.transportation || '暂无' }}</span>
                      </label>
                      <label>
                        <strong>住宿安排</strong>
                        <a-input v-if="canEdit" v-model:value="day.accommodation" placeholder="例如：市中心酒店" />
                        <span v-else>{{ day.accommodation || '暂无' }}</span>
                      </label>
                      <label>
                        <strong>路线摘要</strong>
                        <a-textarea v-if="canEdit" v-model:value="day.route_summary" :rows="2" placeholder="填写路线摘要" />
                        <span v-else>{{ day.route_summary || '暂无路线摘要' }}</span>
                      </label>
                    </div>
                  </div>

                  <div v-if="day.hotel" class="entity-card collab-hotel-card">
                    <div class="section-heading compact-heading">
                      <h3>🏨 酒店推荐</h3>
                    </div>
                    <div v-if="canEdit" class="collab-edit-grid">
                      <a-input v-model:value="day.hotel.name" placeholder="酒店名称" />
                      <a-input v-model:value="day.hotel.address" placeholder="酒店地址" />
                      <a-input v-model:value="day.hotel.type" placeholder="住宿类型" />
                      <a-input v-model:value="day.hotel.rating" placeholder="评分" />
                      <a-input-number v-model:value="day.hotel.estimated_cost" :min="0" addon-before="￥" addon-after="晚" />
                    </div>
                    <div v-else class="collab-hotel-card__body">
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
                  </div>
                </div>

                <section class="day-section day-section--full day-section--divider">
                  <div class="section-heading compact-heading collab-meal-head">
                    <div>
                      <h3>📍 景点安排</h3>
                      <p>可以调整游玩顺序，也可以直接修改景点名称、地址、停留时间和门票。</p>
                    </div>
                    <a-button v-if="canEdit" size="small" type="primary" @click="addAttraction(day.day_index)">新增景点</a-button>
                  </div>
                  <template v-if="day.attractions.length">
                    <article v-for="(attraction, index) in day.attractions" :key="targetId(day.day_index, attraction, index)" class="entity-card entity-card--full collab-attraction-row">
                      <img
                        class="collab-attraction-row__image"
                        :src="resolveAttractionImage(attraction)"
                        :alt="attraction.name"
                        @error="handleImageError"
                      />
                      <div class="collab-attraction-row__content">
                        <div class="entity-card__header">
                          <strong>{{ index + 1 }}. {{ attraction.name }}</strong>
                          <a-space v-if="canEdit">
                            <a-button size="small" :disabled="index === 0" @click="moveAttraction(day.day_index, index, -1)">⬆️ 上移</a-button>
                            <a-button size="small" :disabled="index === day.attractions.length - 1" @click="moveAttraction(day.day_index, index, 1)">⬇️ 下移</a-button>
                            <a-button size="small" danger @click="deleteAttraction(day.day_index, index)">🗑️ 删除</a-button>
                          </a-space>
                        </div>

                        <div v-if="canEdit" class="collab-attraction-edit">
                          <a-input v-model:value="attraction.name" placeholder="景点名称" />
                          <a-input v-model:value="attraction.address" placeholder="景点地址" />
                          <a-input-number v-model:value="attraction.visit_duration" :min="10" :max="480" addon-after="分钟" />
                          <a-input-number v-model:value="attraction.ticket_price" :min="0" addon-before="￥" />
                          <a-textarea v-model:value="attraction.description" :rows="3" placeholder="景点说明" />
                        </div>
                        <template v-else>
                          <div class="collab-mini-metrics">
                            <span>{{ attraction.visit_duration || 0 }} 分钟</span>
                            <span>{{ currency(attraction.ticket_price || 0) }}</span>
                            <span>想去 {{ voteCount(targetId(day.day_index, attraction, index)) }}</span>
                          </div>
                          <p class="collab-attraction-row__desc">{{ attraction.description || '暂无说明' }}</p>
                        </template>

                        <div class="collab-card-actions">
                          <a-button size="small" :type="hasVoted(targetId(day.day_index, attraction, index)) ? 'primary' : 'default'" @click="toggleVote(targetId(day.day_index, attraction, index))">
                            想去 {{ voteCount(targetId(day.day_index, attraction, index)) }}
                          </a-button>
                        </div>
                      </div>
                    </article>
                  </template>
                  <a-empty v-else description="暂无景点安排" />
                </section>

                <section class="day-section day-section--full day-section--divider">
                  <div class="section-heading compact-heading collab-meal-head">
                    <div>
                      <h3>🍽️ 餐厅推荐</h3>
                      <p>早餐、午餐、晚餐和加餐都可以在这里调整。</p>
                    </div>
                    <a-button v-if="canEdit" size="small" type="primary" @click="addMeal(day.day_index)">新增餐食</a-button>
                  </div>
                  <div v-if="day.meals.length" class="collab-meal-list">
                    <article v-for="(meal, mealIndex) in day.meals" :key="`${day.day_index}-${mealIndex}-${meal.name}`" class="entity-card entity-card--full collab-meal-card">
                      <template v-if="canEdit">
                        <div class="collab-meal-edit">
                          <a-select v-model:value="meal.type">
                            <a-select-option value="breakfast">早餐</a-select-option>
                            <a-select-option value="lunch">午餐</a-select-option>
                            <a-select-option value="dinner">晚餐</a-select-option>
                            <a-select-option value="snack">加餐</a-select-option>
                          </a-select>
                          <a-input v-model:value="meal.name" placeholder="餐厅或餐食名称" />
                          <a-input-number v-model:value="meal.estimated_cost" :min="0" addon-before="￥" />
                          <a-textarea v-model:value="meal.description" :rows="2" placeholder="推荐理由" />
                          <a-button danger @click="deleteMeal(day.day_index, mealIndex)">删除餐食</a-button>
                        </div>
                      </template>
                      <template v-else>
                        <strong>{{ mealLabel(meal.type) }} · {{ meal.name }}</strong>
                        <p><strong>💰 人均预算：</strong><span>{{ currency(meal.estimated_cost || 0) }}</span></p>
                        <p><strong>💡 推荐理由：</strong><span>{{ meal.description || '暂无说明' }}</span></p>
                      </template>
                    </article>
                  </div>
                  <a-empty v-else description="暂无餐食安排" />
                </section>
              </a-collapse-panel>
            </a-collapse>
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
  deleteCollabTrip,
  getCollabTrip,
  inviteCollabTripMember,
  resolveMediaUrl,
  updateCollabTripPlan,
  voteCollabTripItem,
} from '@/services/api'
import type { Attraction, CollabTripDetail, Meal, TripPlan } from '@/types'
import { useAuthState } from '@/utils/auth'

const route = useRoute()
const router = useRouter()
const authState = useAuthState()
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const inviting = ref(false)
const showInviteModal = ref(false)
const trip = ref<CollabTripDetail | null>(null)
const draftPlan = ref<TripPlan | null>(null)

const inviteForm = reactive({
  identifier: '',
  role: 'editor',
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

const addAttraction = (dayIndex: number) => {
  if (!draftPlan.value) return
  const day = draftPlan.value.days.find((item) => item.day_index === dayIndex)
  if (!day) return
  day.attractions.push({
    name: '新的景点',
    address: '',
    location: { longitude: 0, latitude: 0 },
    visit_duration: 60,
    description: '',
    ticket_price: 0,
  })
}

const deleteAttraction = (dayIndex: number, index: number) => {
  if (!draftPlan.value) return
  const day = draftPlan.value.days.find((item) => item.day_index === dayIndex)
  if (!day) return
  if (day.attractions.length <= 1) {
    message.warning('每天至少保留一个景点')
    return
  }
  day.attractions.splice(index, 1)
}

const addMeal = (dayIndex: number) => {
  if (!draftPlan.value) return
  const day = draftPlan.value.days.find((item) => item.day_index === dayIndex)
  if (!day) return
  const meal: Meal = {
    type: 'lunch',
    name: '新的餐食安排',
    description: '',
    estimated_cost: 0,
  }
  day.meals.push(meal)
}

const deleteMeal = (dayIndex: number, index: number) => {
  if (!draftPlan.value) return
  const day = draftPlan.value.days.find((item) => item.day_index === dayIndex)
  if (!day) return
  day.meals.splice(index, 1)
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

const currency = (value?: number) => `￥${Number(value || 0).toLocaleString('zh-CN')}`

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

.collab-result-toolbar {
  margin-bottom: 0;
}

.collab-result-hero,
.collab-result-panel {
  border: 0;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 24px 60px rgba(65, 110, 168, 0.14);
  backdrop-filter: blur(18px);
}

.collab-result-hero {
  display: grid;
  gap: 10px;
  padding: 42px;
  background: #eaf5ff;
}

.collab-result-title {
  margin-bottom: 0;
}

.collab-result-meta {
  margin: 0;
  color: var(--brand-muted);
  font-size: 17px;
  font-weight: 700;
}

.collab-result-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.collab-result-tags span {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(45, 134, 231, 0.12);
  color: #1d5d9b;
  font-size: 14px;
  font-weight: 800;
}

.collab-result-panel {
  padding: 26px;
}

.collab-budget-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.collab-result-panel .brand-stat,
.budget-total,
.entity-card,
.collab-advice-card,
.collab-hotel-card,
.collab-attraction-row,
.collab-meal-card {
  border: 0;
}

.collab-result-panel .brand-stat {
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 28px rgba(77, 122, 181, 0.09);
}

.budget-total {
  background: #eaf5ff !important;
}

.collab-day-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.72fr);
  gap: 16px;
  margin-bottom: 18px;
}

.entity-card {
  width: 100%;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 18px 38px rgba(77, 122, 181, 0.1);
}

.entity-card--full {
  margin-bottom: 14px;
}

.entity-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.entity-card__header strong {
  color: #111111;
  font-size: 20px;
  line-height: 1.35;
}

.collab-day-summary-card,
.collab-hotel-card {
  background: rgba(255, 255, 255, 0.82);
}

.collab-day-summary {
  display: grid;
  gap: 12px;
}

.collab-day-summary label {
  display: grid;
  gap: 8px;
}

.collab-day-summary strong {
  color: var(--brand-primary);
  font-size: 14px;
}

.collab-day-summary span {
  color: #2f4156;
  line-height: 1.7;
}

.collab-edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.collab-edit-grid :deep(.ant-input-number),
.collab-attraction-edit :deep(.ant-input-number),
.collab-meal-edit :deep(.ant-input-number) {
  width: 100%;
}

.day-section {
  margin-top: 18px;
}

.day-section--divider {
  padding-top: 18px;
}

.collab-meal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.collab-meal-head p {
  margin: 0;
  color: var(--brand-muted);
  line-height: 1.65;
}

.collab-meal-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.collab-meal-edit {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr) 150px;
  gap: 10px;
}

.collab-meal-edit :deep(.ant-input-textarea) {
  grid-column: 1 / -1;
}

.collab-meal-edit > .ant-btn {
  justify-self: start;
}

.collab-result-panel :deep(.ant-collapse) {
  border: 0;
  background: transparent;
}

.collab-result-panel :deep(.ant-collapse-item) {
  margin-bottom: 14px;
  overflow: hidden;
  border: 0;
  border-radius: 24px;
  background: rgba(234, 245, 255, 0.68);
  box-shadow: 0 18px 36px rgba(75, 126, 184, 0.1);
}

.collab-result-panel :deep(.ant-collapse-header) {
  align-items: center;
  padding: 18px 22px !important;
  color: #17324f !important;
  font-size: 18px;
  font-weight: 800;
}

.collab-result-panel :deep(.ant-collapse-content-box) {
  padding: 0 22px 22px !important;
}

@media (max-width: 1050px) {
  .collab-detail-grid {
    grid-template-columns: 1fr;
  }

  .collab-overview-grid,
  .collab-budget-grid,
  .collab-meal-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .collab-day-layout {
    grid-template-columns: 1fr;
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
  .collab-budget-grid,
  .collab-day-visual-grid,
  .collab-meal-list,
  .collab-attraction-edit,
  .collab-edit-grid,
  .collab-meal-edit {
    grid-template-columns: 1fr;
  }

  .collab-result-hero,
  .collab-result-panel {
    padding: 20px;
  }

  .collab-meal-head,
  .entity-card__header {
    display: grid;
  }
}
</style>
