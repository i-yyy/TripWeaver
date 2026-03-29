<template>
  <div class="brand-page">
    <div class="brand-shell">
      <div class="glass-toolbar">
        <div class="toolbar-group">
          <a-button size="large" @click="goBack">返回旅行规划</a-button>
          <a-button @click="goKBEval">RAG 评测</a-button>
        </div>
        <div class="toolbar-group">
          <a-button v-if="!editMode" @click="toggleEditMode">编辑行程</a-button>
          <a-button v-if="editMode" type="primary" @click="saveChanges">保存修改</a-button>
          <a-button v-if="editMode" @click="cancelEdit">取消</a-button>
          <a-button v-if="tripPlan" @click="submitPlanFeedback('satisfied')">满意</a-button>
          <a-button v-if="tripPlan" danger @click="submitPlanFeedback('unsatisfied')">不满意</a-button>
        </div>
      </div>

      <section v-if="!tripPlan" class="glass-panel glass-panel--soft empty-state">
        <div>
          <h2>没有找到行程数据</h2>
          <p>你可以先返回旅行规划页面重新生成一份行程。</p>
          <a-button type="primary" @click="goBack">返回旅行规划</a-button>
        </div>
      </section>

      <template v-else>
        <section class="glass-panel result-hero">
          <span class="page-kicker">行程结果</span>
          <h1 class="page-title result-title">{{ tripPlan.city }} · {{ tripPlan.start_date }} 至 {{ tripPlan.end_date }}</h1>
          <p class="page-subtitle">{{ tripPlan.overall_suggestions }}</p>
        </section>

        <section class="glass-panel glass-panel--soft result-panel" v-if="recommendationReasons.length">
          <div class="section-heading">
            <h2>推荐依据</h2>
            <p>这里展示了本次生成行程时参考到的知识库、画像和记忆信息。</p>
          </div>
          <a-list :data-source="recommendationReasons">
            <template #renderItem="{ item }">
              <a-list-item>
                <div class="reason-card">
                  <div class="reason-card__head">
                    <strong>{{ item.title || sourceTypeLabel(item.source_type) }}</strong>
                    <div class="toolbar-group">
                      <a-tag color="blue">{{ sourceTypeLabel(item.source_type) }}</a-tag>
                      <a-tag color="geekblue">评分 {{ formatScore(item.score) }}</a-tag>
                    </div>
                  </div>
                  <p><strong>原因：</strong>{{ item.reason || '与当前需求匹配' }}</p>
                  <p v-if="item.snippet"><strong>命中片段：</strong>{{ item.snippet }}</p>
                  <p v-if="item.source_doc"><strong>来源文档：</strong>{{ formatSourceDoc(item.source_doc) }}</p>
                </div>
              </a-list-item>
            </template>
          </a-list>
        </section>

        <section v-if="tripPlan.budget" class="glass-panel glass-panel--soft result-panel">
          <div class="section-heading">
            <h2>预算汇总</h2>
            <p>费用为参考估算，方便你快速判断本次行程的整体花费。</p>
          </div>
          <div class="budget-grid">
            <div class="brand-stat">
              <span>景点</span>
              <strong>{{ currency(tripPlan.budget.total_attractions) }}</strong>
            </div>
            <div class="brand-stat">
              <span>酒店</span>
              <strong>{{ currency(tripPlan.budget.total_hotels) }}</strong>
            </div>
            <div class="brand-stat">
              <span>餐饮</span>
              <strong>{{ currency(tripPlan.budget.total_meals) }}</strong>
            </div>
            <div class="brand-stat">
              <span>交通</span>
              <strong>{{ currency(tripPlan.budget.total_transportation) }}</strong>
            </div>
            <div class="brand-stat budget-total">
              <span>总计</span>
              <strong>{{ currency(tripPlan.budget.total) }}</strong>
            </div>
          </div>
        </section>

        <section class="glass-panel glass-panel--soft result-panel">
          <div class="section-heading">
            <h2>每日行程</h2>
            <p>你可以直接浏览安排，也可以进入编辑模式调换景点顺序、删除不想去的内容。</p>
          </div>

          <a-collapse ghost>
            <a-collapse-panel
              v-for="(day, dayIndex) in tripPlan.days"
              :key="dayIndex"
              :header="`第 ${day.day_index + 1} 天 · ${day.date}`"
            >
              <div class="day-summary">
                <p><strong>当日概览：</strong>{{ day.description }}</p>
                <p><strong>交通方式：</strong>{{ day.transportation }}</p>
                <p v-if="day.transportation_detail"><strong>交通说明：</strong>{{ day.transportation_detail }}</p>
                <p><strong>交通费用：</strong>{{ currency(day.transportation_cost) }}</p>
                <p><strong>住宿安排：</strong>{{ day.accommodation }}</p>
              </div>

              <div v-if="day.hotel" class="entity-card">
                <div class="entity-card__body">
                  <img
                    v-if="day.hotel.map_image_url"
                    class="entity-image entity-image--map"
                    :src="day.hotel.map_image_url"
                    :alt="`${day.hotel.name}地图`"
                  />
                  <div>
                    <h3>住宿推荐 · {{ day.hotel.name }}</h3>
                    <p><strong>地址：</strong>{{ day.hotel.address || '暂无' }}</p>
                    <p><strong>类型：</strong>{{ day.hotel.type || '暂无' }}</p>
                    <p><strong>价格区间：</strong>{{ day.hotel.price_range || '暂无' }}</p>
                    <p><strong>参考评分：</strong>{{ day.hotel.rating || '暂无' }}</p>
                    <p><strong>参考价格：</strong>{{ currency(day.hotel.estimated_cost) }}/晚</p>
                  </div>
                </div>
              </div>

              <div v-if="day.route_summary || day.route_map_url" class="entity-card">
                <div class="entity-card__body">
                  <img
                    v-if="day.route_map_url"
                    class="entity-image entity-image--map"
                    :src="day.route_map_url"
                    :alt="`第 ${day.day_index + 1} 天路线图`"
                  />
                  <div>
                    <h3>路线与地图</h3>
                    <p><strong>路线摘要：</strong>{{ day.route_summary || '暂无路线摘要' }}</p>
                  </div>
                </div>
              </div>

              <div class="section-split">
                <div class="section-heading compact-heading">
                  <h3>景点安排</h3>
                </div>
                <a-list :data-source="day.attractions">
                  <template #renderItem="{ item, index }">
                    <a-list-item>
                      <div class="entity-card entity-card--full">
                        <div class="entity-card__header">
                          <strong>{{ index + 1 }}. {{ item.name }}</strong>
                          <a-space v-if="editMode">
                            <a-button size="small" @click="moveAttraction(dayIndex, index, 'up')" :disabled="index === 0">上移</a-button>
                            <a-button size="small" @click="moveAttraction(dayIndex, index, 'down')" :disabled="index === day.attractions.length - 1">下移</a-button>
                            <a-button size="small" danger @click="deleteAttraction(dayIndex, index)">删除</a-button>
                          </a-space>
                        </div>

                        <div v-if="editMode" class="brand-form-grid">
                          <a-input v-model:value="item.address" placeholder="地址" />
                          <a-input-number v-model:value="item.visit_duration" :min="10" :max="480" />
                          <a-input-number v-model:value="item.ticket_price" :min="0" />
                          <a-textarea v-model:value="item.description" :rows="4" />
                        </div>

                        <div v-else>
                          <div class="entity-media-grid">
                            <img v-if="item.image_url" class="entity-image" :src="item.image_url" :alt="item.name" />
                            <img
                              v-if="item.map_image_url"
                              class="entity-image entity-image--map"
                              :src="item.map_image_url"
                              :alt="`${item.name}地图`"
                            />
                          </div>
                          <p><strong>地址：</strong>{{ item.address || '暂无' }}</p>
                          <p><strong>建议停留：</strong>{{ item.visit_duration }} 分钟</p>
                          <p><strong>门票参考：</strong>{{ currency(item.ticket_price) }}</p>
                          <p><strong>景点描述：</strong>{{ item.description || '暂无说明' }}</p>
                          <div class="toolbar-group">
                            <a-button size="small" @click="submitAttractionFeedback(item.name, 'like')">喜欢</a-button>
                            <a-button size="small" danger @click="submitAttractionFeedback(item.name, 'dislike')">不喜欢</a-button>
                          </div>
                        </div>
                      </div>
                    </a-list-item>
                  </template>
                </a-list>
              </div>

              <div class="section-split">
                <div class="section-heading compact-heading">
                  <h3>餐饮安排</h3>
                </div>
                <a-list :data-source="day.meals">
                  <template #renderItem="{ item }">
                    <a-list-item>
                      <div class="entity-card entity-card--full meal-card">
                        <strong>{{ mealLabel(item.type) }} · {{ item.name }}</strong>
                        <p><strong>人均预算：</strong>{{ currency(item.estimated_cost) }}</p>
                        <p><strong>推荐理由：</strong>{{ item.description || '暂无说明' }}</p>
                      </div>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
            </a-collapse-panel>
          </a-collapse>
        </section>

        <section v-if="tripPlan.weather_info.length" class="glass-panel glass-panel--soft result-panel">
          <div class="section-heading">
            <h2>天气信息</h2>
            <p>出发前可以顺手再确认一次，方便调整穿搭和雨天备选方案。</p>
          </div>
          <div class="weather-grid">
            <div v-for="item in tripPlan.weather_info" :key="item.date" class="brand-stat">
              <span>{{ item.date }}</span>
              <strong>{{ item.day_weather }}</strong>
              <p>白天 {{ item.day_temp }}°C / 夜间 {{ item.night_temp }}°C</p>
              <p>{{ item.night_weather }} · {{ item.wind_direction }}风 {{ item.wind_power }}</p>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { submitFeedback } from '@/services/api'
import type { FeedbackPayload, RecommendationReason, TripPlan } from '@/types'
import { useAuthState } from '@/utils/auth'

const router = useRouter()
const authState = useAuthState()
const tripPlan = ref<TripPlan | null>(null)
const originalPlan = ref<TripPlan | null>(null)
const editMode = ref(false)
const currentUserId = ref(authState.user?.id || sessionStorage.getItem('tripPlannerUserId') || '')
const currentSessionId = ref(sessionStorage.getItem('tripPlannerSessionId') || '')

const recommendationReasons = computed<RecommendationReason[]>(() => tripPlan.value?.recommendation_reasons || [])

onMounted(() => {
  const data = sessionStorage.getItem('tripPlan')
  if (data) {
    tripPlan.value = JSON.parse(data)
  }
})

const clonePlan = <T>(value: T): T => JSON.parse(JSON.stringify(value))

const goBack = () => router.push('/planner')
const goKBEval = () => router.push('/kb-eval')

const toggleEditMode = () => {
  if (!tripPlan.value) return
  editMode.value = true
  originalPlan.value = clonePlan(tripPlan.value)
}

const saveChanges = () => {
  if (!tripPlan.value) return
  editMode.value = false
  sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan.value))
  message.success('已保存修改')
}

const cancelEdit = () => {
  if (!originalPlan.value) return
  tripPlan.value = clonePlan(originalPlan.value)
  editMode.value = false
  message.info('已取消编辑')
}

const deleteAttraction = (dayIndex: number, attractionIndex: number) => {
  if (!tripPlan.value) return
  const day = tripPlan.value.days[dayIndex]
  if (day.attractions.length <= 1) {
    message.warning('每天至少保留一个景点')
    return
  }
  day.attractions.splice(attractionIndex, 1)
}

const moveAttraction = (dayIndex: number, attractionIndex: number, direction: 'up' | 'down') => {
  if (!tripPlan.value) return
  const attractions = tripPlan.value.days[dayIndex].attractions
  if (direction === 'up' && attractionIndex > 0) {
    ;[attractions[attractionIndex - 1], attractions[attractionIndex]] = [
      attractions[attractionIndex],
      attractions[attractionIndex - 1],
    ]
  }
  if (direction === 'down' && attractionIndex < attractions.length - 1) {
    ;[attractions[attractionIndex + 1], attractions[attractionIndex]] = [
      attractions[attractionIndex],
      attractions[attractionIndex + 1],
    ]
  }
}

const submitAttractionFeedback = async (attractionName: string, feedbackType: 'like' | 'dislike') => {
  if (!currentUserId.value || !currentSessionId.value || !tripPlan.value) return
  const payload: FeedbackPayload = {
    user_id: currentUserId.value,
    session_id: currentSessionId.value,
    target_type: 'attraction',
    target_name: attractionName,
    feedback_type: feedbackType,
    metadata: { city: tripPlan.value.city },
  }

  try {
    await submitFeedback(payload)
    message.success(feedbackType === 'like' ? '已记录喜欢' : '已记录不喜欢')
  } catch (error: any) {
    message.error(error.message || '提交反馈失败')
  }
}

const submitPlanFeedback = async (feedbackType: 'satisfied' | 'unsatisfied') => {
  if (!currentUserId.value || !currentSessionId.value || !tripPlan.value) return
  const payload: FeedbackPayload = {
    user_id: currentUserId.value,
    session_id: currentSessionId.value,
    target_type: 'plan',
    target_name: tripPlan.value.city,
    feedback_type: feedbackType,
    metadata: {
      city: tripPlan.value.city,
      start_date: tripPlan.value.start_date,
      end_date: tripPlan.value.end_date,
    },
  }

  try {
    await submitFeedback(payload)
    message.success(feedbackType === 'satisfied' ? '已记录满意反馈' : '已记录不满意反馈')
  } catch (error: any) {
    message.error(error.message || '提交反馈失败')
  }
}

const mealLabel = (type: string) => {
  const mapping: Record<string, string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '小吃',
  }
  return mapping[type] || type
}

const sourceTypeLabel = (sourceType: string) => {
  const mapping: Record<string, string> = {
    knowledge_base: '知识库',
    memory: '记忆',
    profile: '画像',
  }
  return mapping[sourceType] || sourceType
}

const formatScore = (value: number | undefined) => Number(value || 0).toFixed(3)

const formatSourceDoc = (docPath: string) => {
  const normalized = docPath.replace(/\\/g, '/')
  const segments = normalized.split('/')
  return segments[segments.length - 1] || docPath
}

const currency = (value?: number) => {
  const amount = Number(value || 0)
  return amount > 0 ? `¥${amount}` : '待确认'
}
</script>

<style scoped>
.result-hero,
.result-panel {
  padding: 28px;
  margin-bottom: 18px;
}

.result-title {
  font-size: clamp(36px, 4vw, 54px);
}

.reason-card,
.entity-card {
  width: 100%;
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.reason-card__head,
.entity-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.reason-card p,
.entity-card p,
.day-summary p,
.brand-stat p {
  margin: 0 0 8px;
  color: var(--brand-muted);
  line-height: 1.75;
}

.budget-grid,
.weather-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}

.budget-total {
  background: linear-gradient(135deg, rgba(255,255,255,0.72), rgba(231,240,255,0.86));
}

.day-summary {
  margin-bottom: 18px;
}

.section-split {
  margin-top: 18px;
}

.compact-heading {
  margin-bottom: 10px;
}

.entity-card {
  margin-bottom: 18px;
}

.entity-card__body {
  display: grid;
  grid-template-columns: minmax(220px, 320px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.entity-card--full {
  margin-bottom: 0;
}

.entity-media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 12px;
}

.entity-image {
  width: 100%;
  min-height: 180px;
  border-radius: 16px;
  object-fit: cover;
  background: rgba(225, 235, 247, 0.8);
}

.entity-image--map {
  min-height: 200px;
}

.meal-card strong {
  display: block;
  margin-bottom: 10px;
}

@media (max-width: 960px) {
  .result-hero,
  .result-panel {
    padding: 22px;
  }

  .entity-card__body {
    grid-template-columns: 1fr;
  }

  .reason-card__head,
  .entity-card__header {
    flex-direction: column;
  }
}
</style>
