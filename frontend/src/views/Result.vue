<template>
  <div class="result-page">
    <div class="header-row">
      <a-space wrap>
        <a-button size="large" @click="goBack">返回首页</a-button>
        <a-button @click="goKBEval">RAG 评测</a-button>
      </a-space>
      <a-space wrap>
        <a-button v-if="!editMode" @click="toggleEditMode">编辑行程</a-button>
        <a-button v-if="editMode" type="primary" @click="saveChanges">保存修改</a-button>
        <a-button v-if="editMode" @click="cancelEdit">取消</a-button>
        <a-button v-if="tripPlan" @click="submitPlanFeedback('satisfied')">满意</a-button>
        <a-button v-if="tripPlan" danger @click="submitPlanFeedback('unsatisfied')">不满意</a-button>
      </a-space>
    </div>

    <a-empty v-if="!tripPlan" description="没有找到行程数据">
      <a-button type="primary" @click="goBack">返回首页</a-button>
    </a-empty>

    <template v-else>
      <a-card :bordered="false" class="overview-card">
        <h2>{{ tripPlan.city }} 行程</h2>
        <p>{{ tripPlan.start_date }} - {{ tripPlan.end_date }}</p>
        <p>{{ tripPlan.overall_suggestions }}</p>
      </a-card>

      <a-card :bordered="false" class="reason-card" title="推荐依据">
        <a-empty v-if="!recommendationReasons.length" description="暂无结构化推荐依据" />
        <a-list v-else :data-source="recommendationReasons">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-card style="width: 100%">
                <template #title>
                  <a-space wrap>
                    <span>{{ item.title || sourceTypeLabel(item.source_type) }}</span>
                    <a-tag color="blue">{{ sourceTypeLabel(item.source_type) }}</a-tag>
                    <a-tag color="geekblue">评分 {{ formatScore(item.score) }}</a-tag>
                  </a-space>
                </template>
                <p><strong>原因：</strong>{{ item.reason || '与当前需求匹配' }}</p>
                <p v-if="item.snippet"><strong>命中片段：</strong>{{ item.snippet }}</p>
                <p v-if="item.source_doc"><strong>来源文档：</strong>{{ formatSourceDoc(item.source_doc) }}</p>
              </a-card>
            </a-list-item>
          </template>
        </a-list>
      </a-card>

      <a-card v-if="tripPlan.budget" :bordered="false" class="budget-card" title="预算汇总">
        <a-row :gutter="12">
          <a-col :span="6">景点：¥{{ tripPlan.budget.total_attractions }}</a-col>
          <a-col :span="6">酒店：¥{{ tripPlan.budget.total_hotels }}</a-col>
          <a-col :span="6">餐饮：¥{{ tripPlan.budget.total_meals }}</a-col>
          <a-col :span="6">交通：¥{{ tripPlan.budget.total_transportation }}</a-col>
        </a-row>
        <h3 style="margin-top: 12px">总计：¥{{ tripPlan.budget.total }}</h3>
      </a-card>

      <a-card :bordered="false" title="每日行程">
        <a-collapse>
          <a-collapse-panel
            v-for="(day, dayIndex) in tripPlan.days"
            :key="dayIndex"
            :header="`第${day.day_index + 1}天 - ${day.date}`"
          >
            <div class="day-section">
              <p><strong>当日概览：</strong>{{ day.description }}</p>
              <p><strong>交通方式：</strong>{{ day.transportation }}</p>
              <p v-if="day.transportation_detail"><strong>交通说明：</strong>{{ day.transportation_detail }}</p>
              <p><strong>交通费用：</strong>{{ currency(day.transportation_cost) }}</p>
              <p><strong>住宿安排：</strong>{{ day.accommodation }}</p>
            </div>

            <a-card v-if="day.hotel" size="small" class="sub-card" title="住宿推荐">
              <div class="entity-grid">
                <img
                  v-if="day.hotel.map_image_url"
                  class="map-image"
                  :src="day.hotel.map_image_url"
                  :alt="`${day.hotel.name}地图`"
                />
                <div>
                  <p><strong>酒店：</strong>{{ day.hotel.name }}</p>
                  <p><strong>地址：</strong>{{ day.hotel.address || '暂无' }}</p>
                  <p><strong>类型：</strong>{{ day.hotel.type || '暂无' }}</p>
                  <p><strong>价格区间：</strong>{{ day.hotel.price_range || '暂无' }}</p>
                  <p><strong>参考评分：</strong>{{ day.hotel.rating || '暂无' }}</p>
                  <p><strong>参考价格：</strong>{{ currency(day.hotel.estimated_cost) }}/晚</p>
                </div>
              </div>
            </a-card>

            <a-card
              v-if="day.route_summary || day.route_map_url"
              size="small"
              class="sub-card"
              title="路线与地图"
            >
              <div class="entity-grid">
                <img
                  v-if="day.route_map_url"
                  class="route-image"
                  :src="day.route_map_url"
                  :alt="`第${day.day_index + 1}天路线图`"
                />
                <div>
                  <p><strong>路线摘要：</strong>{{ day.route_summary || '暂无路线摘要' }}</p>
                </div>
              </div>
            </a-card>

            <a-divider orientation="left">景点</a-divider>
            <a-list :data-source="day.attractions">
              <template #renderItem="{ item, index }">
                <a-list-item>
                  <a-card style="width: 100%">
                    <template #title>{{ index + 1 }}. {{ item.name }}</template>
                    <template #extra v-if="editMode">
                      <a-space>
                        <a-button size="small" @click="moveAttraction(dayIndex, index, 'up')" :disabled="index === 0">上移</a-button>
                        <a-button
                          size="small"
                          @click="moveAttraction(dayIndex, index, 'down')"
                          :disabled="index === day.attractions.length - 1"
                        >
                          下移
                        </a-button>
                        <a-button size="small" danger @click="deleteAttraction(dayIndex, index)">删除</a-button>
                      </a-space>
                    </template>

                    <div v-if="editMode">
                      <a-input v-model:value="item.address" placeholder="地址" style="margin-bottom: 8px" />
                      <a-input-number
                        v-model:value="item.visit_duration"
                        :min="10"
                        :max="480"
                        style="width: 100%; margin-bottom: 8px"
                      />
                      <a-input-number
                        v-model:value="item.ticket_price"
                        :min="0"
                        style="width: 100%; margin-bottom: 8px"
                      />
                      <a-textarea v-model:value="item.description" :rows="5" />
                    </div>
                    <div v-else>
                      <div class="entity-grid">
                        <img
                          v-if="item.image_url"
                          class="entity-image"
                          :src="item.image_url"
                          :alt="item.name"
                        />
                        <img
                          v-if="item.map_image_url"
                          class="map-image"
                          :src="item.map_image_url"
                          :alt="`${item.name}地图`"
                        />
                      </div>
                      <p><strong>地址：</strong>{{ item.address }}</p>
                      <p><strong>建议停留：</strong>{{ item.visit_duration }} 分钟</p>
                      <p><strong>门票参考：</strong>{{ currency(item.ticket_price) }}</p>
                      <p><strong>景点描述：</strong>{{ item.description }}</p>
                      <a-space>
                        <a-button size="small" @click="submitAttractionFeedback(item.name, 'like')">喜欢</a-button>
                        <a-button size="small" danger @click="submitAttractionFeedback(item.name, 'dislike')">不喜欢</a-button>
                      </a-space>
                    </div>
                  </a-card>
                </a-list-item>
              </template>
            </a-list>

            <a-divider orientation="left">餐饮</a-divider>
            <a-list :data-source="day.meals">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-card style="width: 100%">
                    <template #title>{{ mealLabel(item.type) }}：{{ item.name }}</template>
                    <p><strong>人均预算：</strong>{{ currency(item.estimated_cost) }}</p>
                    <p><strong>推荐理由：</strong>{{ item.description || '暂无说明' }}</p>
                  </a-card>
                </a-list-item>
              </template>
            </a-list>
          </a-collapse-panel>
        </a-collapse>
      </a-card>

      <a-card v-if="tripPlan.weather_info.length" :bordered="false" title="天气">
        <a-list :data-source="tripPlan.weather_info">
          <template #renderItem="{ item }">
            <a-list-item>
              {{ item.date }} - 白天 {{ item.day_weather }} {{ item.day_temp }}°C / 夜间 {{ item.night_weather }}
              {{ item.night_temp }}°C
            </a-list-item>
          </template>
        </a-list>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { submitFeedback } from '@/services/api'
import type { FeedbackPayload, RecommendationReason, TripPlan } from '@/types'

const router = useRouter()
const tripPlan = ref<TripPlan | null>(null)
const originalPlan = ref<TripPlan | null>(null)
const editMode = ref(false)
const currentUserId = ref(sessionStorage.getItem('tripPlannerUserId') || localStorage.getItem('trip_planner_user_id') || '')
const currentSessionId = ref(sessionStorage.getItem('tripPlannerSessionId') || '')
const recommendationReasons = computed<RecommendationReason[]>(() => tripPlan.value?.recommendation_reasons || [])

onMounted(() => {
  const data = sessionStorage.getItem('tripPlan')
  if (data) {
    tripPlan.value = JSON.parse(data)
  }
})

const goBack = () => {
  router.push('/')
}

const goKBEval = () => {
  router.push('/kb-eval')
}

const toggleEditMode = () => {
  if (!tripPlan.value) return
  editMode.value = true
  originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
}

const saveChanges = () => {
  editMode.value = false
  if (!tripPlan.value) return
  sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan.value))
  message.success('已保存修改')
}

const cancelEdit = () => {
  if (!originalPlan.value) return
  tripPlan.value = JSON.parse(JSON.stringify(originalPlan.value))
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
.result-page {
  min-height: 100vh;
  background: linear-gradient(160deg, #f4f7ff 0%, #e8eef8 100%);
  padding: 24px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.overview-card,
.reason-card,
.budget-card {
  margin-bottom: 16px;
}

.day-section {
  margin-bottom: 12px;
}

.sub-card {
  margin-bottom: 16px;
}

.entity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.entity-image,
.map-image,
.route-image {
  width: 100%;
  border-radius: 12px;
  object-fit: cover;
  background: #eef2f8;
}

.entity-image {
  min-height: 180px;
  max-height: 240px;
}

.map-image,
.route-image {
  min-height: 160px;
}

@media (max-width: 900px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
