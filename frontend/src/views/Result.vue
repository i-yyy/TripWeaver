<template>
  <div class="brand-page">
    <div class="brand-shell">
      <div class="glass-toolbar">
        <div class="toolbar-group">
          <a-button size="large" @click="goBack">↩️ 返回旅行规划</a-button>
          <a-button @click="goKBEval">🧪 RAG评测</a-button>
        </div>
        <div class="toolbar-group">
          <a-button v-if="!editMode" @click="toggleEditMode">✏️ 编辑行程</a-button>
          <a-button v-if="editMode" type="primary" @click="saveChanges">💾 保存修改</a-button>
          <a-button v-if="editMode" @click="cancelEdit">↩️ 取消</a-button>
          <a-button v-if="tripPlan" @click="submitPlanFeedback('satisfied')">👍 满意</a-button>
          <a-button v-if="tripPlan" danger @click="submitPlanFeedback('unsatisfied')">👎 不满意</a-button>
        </div>
      </div>

      <section v-if="!tripPlan" class="glass-panel glass-panel--soft empty-state">
        <div>
          <h2>没有找到行程数据</h2>
          <p>你可以先返回旅行规划页面重新生成一份行程</p>
          <a-button type="primary" @click="goBack">返回旅行规划</a-button>
        </div>
      </section>

      <template v-else>
        <div class="result-shell-with-nav">
          <aside class="glass-panel glass-panel--soft result-sidebar-nav">
            <div class="section-heading compact-heading">
              <h3>🧭 页面导航</h3>
              <p>快速跳到你想看的内容</p>
            </div>
            <div class="result-sidebar-nav__group">
              <button type="button" class="result-nav-button" @click="scrollToSection('result-hero')">🗓️ 行程总览</button>
              <button v-if="tripPlan.budget" type="button" class="result-nav-button" @click="scrollToSection('result-budget')">💰 预算汇总</button>
              <button type="button" class="result-nav-button" @click="scrollToSection('result-days')">📚 每日行程</button>
              <button v-if="travelWeatherInfo.length" type="button" class="result-nav-button" @click="scrollToSection('result-weather')">🌤️ 天气信息</button>
              <button
                v-if="profileRecommendation || memoryRecommendationTotal || memoryRecommendationItems.length"
                type="button"
                class="result-nav-button"
                @click="scrollToSection('result-reasons')"
              >
                📌 推荐依据
              </button>
              <button
                v-if="appliedSkills.length"
                type="button"
                class="result-nav-button"
                @click="scrollToSection('result-skills')"
              >
                🧩 已启用技能
              </button>
            </div>
          </aside>

          <div class="result-main-content">
        <section id="result-hero" class="glass-panel result-hero">
          <span class="page-kicker">🗓️ 行程结果</span>
          <h1 class="page-title result-title">{{ tripPlan.city }} · {{ tripPlan.start_date }} 至 {{ tripPlan.end_date }}</h1>
          <p class="page-subtitle">{{ tripPlan.overall_suggestions }}</p>
        </section>

        <section id="result-budget" v-if="tripPlan.budget" class="glass-panel glass-panel--soft result-panel">
          <div class="section-heading">
            <h2>💰 预算汇总</h2>
            <p>费用为参考估算，方便你快速判断本次行程的整体花费</p>
          </div>
          <div class="budget-grid">
            <div class="brand-stat">
              <span>📍 景点</span>
              <strong>{{ currency(tripPlan.budget.total_attractions) }}</strong>
            </div>
            <div class="brand-stat">
              <span>🏨 酒店</span>
              <strong>{{ currency(tripPlan.budget.total_hotels) }}</strong>
            </div>
            <div class="brand-stat">
              <span>🍽️ 餐饮</span>
              <strong>{{ currency(tripPlan.budget.total_meals) }}</strong>
            </div>
            <div class="brand-stat">
              <span>🚇 交通</span>
              <strong>{{ currency(tripPlan.budget.total_transportation) }}</strong>
            </div>
            <div class="brand-stat budget-total">
              <span>🧾 总计</span>
              <strong>{{ currency(tripPlan.budget.total) }}</strong>
            </div>
          </div>
        </section>

        <section id="result-days" class="glass-panel glass-panel--soft result-panel">
          <div class="section-heading">
            <h2>🗓️ 每日行程</h2>
            <p>你可以直接浏览安排，也可以进入编辑模式调换景点顺序、删除不想去的内容</p>
          </div>

          <a-collapse ghost @change="handleDayPanelsChange">
            <a-collapse-panel
              v-for="(day, dayIndex) in tripPlan.days"
              :key="String(dayIndex)"
              :id="getDaySectionId(dayIndex)"
              :header="`第 ${day.day_index + 1} 天 · ${day.date}`"
            >
              <div class="day-layout">
                <div class="entity-card day-map-card">
                  <div class="section-heading compact-heading">
                    <h3>🗺️ 地图路线</h3>
                    <p>查看当天点位和移动路线</p>
                  </div>
                  <DayRouteMap
                    :route="getRenderableDayRoute(dayIndex, day)"
                    :loading="Boolean(routeLoading[dayIndex])"
                    :error="routeErrors[dayIndex] || null"
                    :fallback-static-map-url="day.route_map_url || null"
                  />
                </div>

                <div class="entity-card day-content-card">
                  <div class="day-section">
                    <div class="section-heading compact-heading">
                      <h3>📝 每日行程</h3>
                    </div>
                    <div class="day-summary day-summary--embedded">
                      <p><strong>📝 当日概览：</strong>{{ day.description }}</p>
                      <p><strong>🚇 交通方式：</strong>{{ transportationLabel(day.transportation) }}</p>
                      <p><strong>💸 交通费用：</strong>{{ currency(day.transportation_cost) }}</p>
                      <p><strong>🛏️ 住宿安排：</strong>{{ accommodationLabel(day.accommodation) }}</p>
                      <p><strong>🗺️ 路线摘要：</strong>{{ getRenderableDayRoute(dayIndex, day)?.summary || day.route_summary || '暂无路线摘要' }}</p>
                      <p v-if="getRenderableDayRoute(dayIndex, day)">
                        <strong>📏 预计路程：</strong>{{ formatDistance(getRenderableDayRoute(dayIndex, day)?.distance) }} ·
                        {{ formatDuration(getRenderableDayRoute(dayIndex, day)?.duration) }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="day.hotel" class="day-section day-section--full day-section--divider">
                <div class="section-heading compact-heading">
                  <h3>🏨 酒店推荐</h3>
                </div>
                <div class="entity-card hotel-compact hotel-compact--panel" :class="{ 'hotel-compact--no-image': !day.hotel.map_image_url }">
                  <img
                    v-if="day.hotel.map_image_url"
                    class="entity-image hotel-compact__image"
                    :src="day.hotel.map_image_url"
                    :alt="`${day.hotel.name}地图`"
                  />
                  <div class="hotel-compact__content">
                    <strong class="hotel-compact__title">{{ day.hotel.name }}</strong>
                    <div class="hotel-meta-grid">
                      <div class="hotel-meta-card hotel-meta-card--wide">
                        <strong>📍 地址</strong>
                        <span>{{ day.hotel.address || '暂无' }}</span>
                      </div>
                      <div class="hotel-meta-card">
                        <strong>🏷️ 类型</strong>
                        <span>{{ hotelTypeLabel(day.hotel.type) }}</span>
                      </div>
                      <div class="hotel-meta-card">
                        <strong>💰 价格区间</strong>
                        <span>{{ priceRangeLabel(day.hotel.price_range) }}</span>
                      </div>
                      <div class="hotel-meta-card">
                        <strong>⭐ 参考评分</strong>
                        <span>{{ day.hotel.rating || '暂无' }}</span>
                      </div>
                      <div class="hotel-meta-card">
                        <strong>💴 参考价格</strong>
                        <span>{{ currency(day.hotel.estimated_cost) }}/晚</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="day-section day-section--full day-section--divider">
                <div class="section-heading compact-heading">
                  <h3>📍 景点安排</h3>
                </div>
                <a-list :data-source="day.attractions">
                  <template #renderItem="{ item, index }">
                    <a-list-item>
                      <div class="entity-card entity-card--full">
                        <div class="entity-card__header">
                          <strong>{{ index + 1 }}. {{ item.name }}</strong>
                          <a-space v-if="editMode">
                            <a-button size="small" @click="moveAttraction(dayIndex, index, 'up')" :disabled="index === 0">⬆️ 上移</a-button>
                            <a-button size="small" @click="moveAttraction(dayIndex, index, 'down')" :disabled="index === day.attractions.length - 1">⬇️ 下移</a-button>
                            <a-button size="small" danger @click="deleteAttraction(dayIndex, index)">🗑️ 删除</a-button>
                          </a-space>
                        </div>

                        <div v-if="editMode" class="brand-form-grid">
                          <a-input v-model:value="item.address" placeholder="地址" />
                          <a-input-number v-model:value="item.visit_duration" :min="10" :max="480" />
                          <a-input-number v-model:value="item.ticket_price" :min="0" />
                          <a-textarea v-model:value="item.description" :rows="4" />
                        </div>

                        <div v-else class="attraction-row">
                          <div class="attraction-row__media">
                            <img class="entity-image attraction-row__image" :src="resolveAttractionImage(item)" :alt="item.name" />
                          </div>
                          <div class="attraction-row__content">
                            <div class="attraction-meta-grid">
                              <div class="attraction-meta-card attraction-meta-card--wide">
                                <strong>📍 地址</strong>
                                <span>{{ item.address || '暂无' }}</span>
                              </div>
                              <div class="attraction-meta-card">
                                <strong>⏱️ 建议停留</strong>
                                <span>{{ item.visit_duration }} 分钟</span>
                              </div>
                              <div class="attraction-meta-card">
                                <strong>🎫 门票参考</strong>
                                <span>{{ currency(item.ticket_price) }}</span>
                              </div>
                            </div>
                            <div class="attraction-copy">
                              <strong>📝 景点描述</strong>
                              <p>{{ item.description || '暂无说明' }}</p>
                            </div>
                            <div class="toolbar-group">
                              <a-button size="small" @click="submitAttractionFeedback(item.name, 'like')">❤️ 喜欢</a-button>
                              <a-button size="small" danger @click="submitAttractionFeedback(item.name, 'dislike')">💔 不喜欢</a-button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </a-list-item>
                  </template>
                </a-list>
              </div>

              <div class="day-section day-section--full day-section--divider">
                <div class="section-heading compact-heading">
                  <h3>🍽️ 餐厅推荐</h3>
                </div>
                <a-list :data-source="day.meals">
                  <template #renderItem="{ item }">
                    <a-list-item>
                      <div class="entity-card entity-card--full meal-card">
                        <strong>{{ mealLabel(item.type) }} · {{ item.name }}</strong>
                        <p class="meal-card__budget"><strong> 💰 人均预算：</strong><span>{{ currency(item.estimated_cost) }}</span></p>
                        <p class="meal-card__reason"><strong> 💡 推荐理由：</strong><span>{{ item.description || '暂无说明' }}</span></p>
                      </div>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
            </a-collapse-panel>
          </a-collapse>
        </section>

        <section id="result-weather" v-if="travelWeatherInfo.length" class="glass-panel glass-panel--soft result-panel">
          <div class="section-heading">
            <h2>🌤️ 天气信息</h2>
            <p>出发前可以顺手再确认一次，方便调整穿搭和雨天备选方案</p>
          </div>
          <div class="weather-grid">
            <div v-for="item in travelWeatherInfo" :key="item.date" class="weather-card">
              <div class="weather-card__date">{{ item.date }}</div>
              <div class="weather-card__body">
                <div class="weather-card__period">
                  <div class="weather-card__icon" :class="weatherIcon(item.day_weather, 'day').className">
                    {{ weatherIcon(item.day_weather, 'day').symbol }}
                  </div>
                  <div>
                    <div class="weather-card__label">白天</div>
                    <div class="weather-card__value">{{ item.day_weather }} {{ item.day_temp }}°C</div>
                  </div>
                </div>
                <div class="weather-card__period">
                  <div class="weather-card__icon" :class="weatherIcon(item.night_weather, 'night').className">
                    {{ weatherIcon(item.night_weather, 'night').symbol }}
                  </div>
                  <div>
                    <div class="weather-card__label">夜间</div>
                    <div class="weather-card__value">{{ item.night_weather }} {{ item.night_temp }}°C</div>
                  </div>
                </div>
              </div>
              <div class="weather-card__footer">🍃 {{ item.wind_direction }}风 {{ item.wind_power }}</div>
            </div>
          </div>
        </section>

        <section
          id="result-reasons"
          class="glass-panel glass-panel--soft result-panel"
          v-if="profileRecommendation || memoryRecommendationTotal || memoryRecommendationItems.length"
        >
          <div class="section-heading">
            <h2>📌 推荐依据</h2>
            <p>这里展示本次行程生成时主要参考的画像与历史记忆</p>
          </div>
          <div class="recommendation-layout">
            <div class="recommendation-group">
              <div class="section-heading compact-heading recommendation-group__heading">
                <h3>👤 用户画像偏好</h3>
              </div>
              <div v-if="profileRecommendation" class="reason-card recommendation-main-card recommendation-main-card--profile">
                <div class="reason-card__head">
                  <strong>{{ formatRecommendationTitle(profileRecommendation) }}</strong>
                  <div class="toolbar-group">
                    <a-tag color="blue">用户画像</a-tag>
                    <a-tag color="geekblue">评分 {{ formatScore(profileRecommendation.score) }}</a-tag>
                  </div>
                </div>
                <div class="reason-score-hero">
                  <span>画像分数</span>
                  <strong>{{ formatScore(profileRecommendation.score) }}</strong>
                </div>
                <p><strong>摘要：</strong>{{ compactRecommendationText(profileRecommendation) }}</p>
              </div>
            </div>

            <div class="recommendation-group">
              <div class="section-heading compact-heading recommendation-group__heading">
                <h3>🧠 历史记忆</h3>
              </div>

              <div v-if="memoryRecommendationTotal" class="reason-card recommendation-main-card recommendation-main-card--memory">
                <div class="reason-card__head">
                  <strong>{{ formatRecommendationTitle(memoryRecommendationTotal) }}</strong>
                  <div class="toolbar-group">
                    <a-tag color="blue">历史记忆</a-tag>
                    <a-tag color="geekblue">评分 {{ formatScore(memoryRecommendationTotal.score) }}</a-tag>
                  </div>
                </div>
                <div class="reason-score-hero reason-score-hero--memory">
                  <span>记忆总分</span>
                  <strong>{{ formatScore(memoryRecommendationTotal.score) }}</strong>
                </div>
                <p v-if="memoryBreakdownText(memoryRecommendationTotal)"><strong>构成：</strong>{{ memoryBreakdownText(memoryRecommendationTotal) }}</p>
              </div>

              <div class="memory-reason-grid">
                <div v-for="item in memoryRecommendationItems" :key="formatRecommendationTitle(item)" class="reason-card memory-reason-card">
                  <div class="reason-card__head">
                    <strong>{{ formatRecommendationTitle(item) }}</strong>
                    <a-tag color="geekblue">评分 {{ formatScore(item.score) }}</a-tag>
                  </div>
                  <div class="memory-reason-card__score">
                    <span>子项分数</span>
                    <strong>{{ formatScore(item.score) }}</strong>
                  </div>
                  <p><strong>摘要：</strong>{{ compactRecommendationText(item) }}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="result-skills"
          v-if="appliedSkills.length"
          class="glass-panel glass-panel--soft result-panel"
        >
          <div class="section-heading">
            <h2>🧩 已启用技能</h2>
            <p>这里展示了本次行程实际生效的技能，以及命中的字段、关键词和触发原因</p>
          </div>
          <div class="skill-grid">
            <div v-for="skill in appliedSkills" :key="skill.key" class="reason-card skill-card">
              <div class="reason-card__head">
                <strong>{{ skill.name }}</strong>
                <div class="toolbar-group">
                  <a-tag color="blue">{{ skillLayerLabel(skill.layer) }}</a-tag>
                  <a-tag :color="skillCategoryColor(skill.category)">{{ skillCategoryLabel(skill.category) }}</a-tag>
                  <a-tag>{{ skillSourceLabel(skill.source) }}</a-tag>
                </div>
              </div>
              <p v-if="skill.description"><strong>说明：</strong>{{ skill.description }}</p>
              <p v-if="skill.matched_fields?.length"><strong>命中字段：</strong>{{ skill.matched_fields.join('、') }}</p>
              <p v-if="skill.matched_terms?.length"><strong>命中词：</strong>{{ skill.matched_terms.join('、') }}</p>
              <p v-if="skill.reasons?.length"><strong>触发原因：</strong>{{ skill.reasons.join('；') }}</p>
            </div>
          </div>
        </section>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import DayRouteMap from '@/components/DayRouteMap.vue'
import { getDayRouteDetail, submitFeedback } from '@/services/api'
import type {
  AppliedSkill,
  Attraction,
  DayPlan,
  DayRouteInfo,
  DayRouteMarker,
  DayRoutePayload,
  DayRouteSegment,
  FeedbackPayload,
  RecommendationReason,
  TripPlan,
} from '@/types'
import { useAuthState } from '@/utils/auth'

const router = useRouter()
const authState = useAuthState()
const tripPlan = ref<TripPlan | null>(null)
const originalPlan = ref<TripPlan | null>(null)
const editMode = ref(false)
const currentUserId = ref(authState.user?.id || sessionStorage.getItem('tripPlannerUserId') || '')
const currentSessionId = ref(sessionStorage.getItem('tripPlannerSessionId') || '')
const activeDayKeys = ref<string[]>([])
const routeDetails = ref<Record<number, DayRouteInfo>>({})
const routeLoading = ref<Record<number, boolean>>({})
const routeErrors = ref<Record<number, string>>({})

const getDaySectionId = (dayIndex: number) => `result-day-${dayIndex}`

const scrollToSection = (sectionId: string) => {
  if (typeof window === 'undefined') return
  const element = document.getElementById(sectionId)
  if (!element) return
  const top = element.getBoundingClientRect().top + window.scrollY - 112
  window.scrollTo({ top, behavior: 'smooth' })
}

const rawRecommendationReasons = computed<RecommendationReason[]>(() => tripPlan.value?.recommendation_reasons || [])
const travelWeatherInfo = computed(() => {
  if (!tripPlan.value) return []
  const travelDates = new Set((tripPlan.value.days || []).map((day) => day.date))
  const matched = (tripPlan.value.weather_info || []).filter((item) => travelDates.has(item.date))
  return matched.length ? matched : tripPlan.value.weather_info || []
})

const memoryTypeLabel = (memoryType?: string) => {
  const mapping: Record<string, string> = {
    session: '会话记忆',
    episodic: '行程记忆',
    semantic: '反馈记忆',
  }
  return mapping[String(memoryType || '').toLowerCase()] || String(memoryType || '其他记忆')
}

const normalizeChineseText = (value?: string) => {
  if (!value) return ''
  return String(value)
    .replace(/knowledge_base/gi, '知识库')
    .replace(/profile-context/gi, '画像上下文')
    .replace(/memory-summary/gi, '记忆总览')
    .replace(/memory-recall/gi, '记忆召回')
    .replace(/public transit/gi, '公共交通')
    .replace(/\btransit\b/gi, '公共交通')
    .replace(/\bsubway\b/gi, '地铁')
    .replace(/\bbus\b/gi, '公交')
    .replace(/\bdrive\b/gi, '自驾')
    .replace(/\bdriving\b/gi, '自驾')
    .replace(/\bwalk\b/gi, '步行')
    .replace(/\bwalking\b/gi, '步行')
    .replace(/\bbudget\b/gi, '预算')
    .replace(/\blow\b/gi, '低')
    .replace(/\bmedium\b/gi, '中')
    .replace(/\bhigh\b/gi, '高')
    .replace(/\bfamily\b/gi, '家庭')
    .replace(/\bcouple\b/gi, '情侣')
    .replace(/\bfriends\b/gi, '朋友')
    .replace(/\bmuseum\b/gi, '博物馆')
    .replace(/\bcitywalk\b/gi, '城市漫游')
    .replace(/\bfood\b/gi, '美食')
    .replace(/\brainy_day\b/gi, '雨天')
    .replace(/\bnight_view\b/gi, '夜景')
    .replace(/\bindoor\b/gi, '室内')
    .replace(/\boutdoor\b/gi, '户外')
    .replace(/\bsemantic\b/gi, '反馈记忆')
    .replace(/\bepisodic\b/gi, '行程记忆')
    .replace(/\bsession\b/gi, '会话记忆')
}

const normalizeMemoryType = (reason: RecommendationReason) => {
  const metadata = (reason.metadata || {}) as Record<string, unknown>
  const fromMetadata = String(metadata.memory_type || '').toLowerCase()
  if (fromMetadata) return fromMetadata
  const title = String(reason.title || '')
  if (title.includes('会话记忆')) return 'session'
  if (title.includes('行程记忆')) return 'episodic'
  if (title.includes('反馈记忆')) return 'semantic'
  return ''
}

const isMemoryTotalReason = (reason: RecommendationReason) => {
  const metadata = (reason.metadata || {}) as Record<string, unknown>
  return (
    reason.source_type === 'memory' &&
    (reason.rerank_mode === 'memory-summary' ||
      Boolean(metadata.memory_breakdown) ||
      String(reason.title || '').includes('总分'))
  )
}

const buildMemoryTotalReason = (items: RecommendationReason[]): RecommendationReason | null => {
  if (!items.length) return null
  const breakdown = ['session', 'episodic', 'semantic'].map((memoryType) => {
    const matched = items.find((item) => normalizeMemoryType(item) === memoryType)
    return {
      memory_type: memoryType,
      memory_label: memoryTypeLabel(memoryType),
      score: Number(matched?.score || 0),
    }
  })

  return {
    source_type: 'memory',
    title: '历史偏好记忆总分',
    reason: `当前共命中 ${breakdown.length} 类历史偏好记忆`,
    snippet: breakdown.map((item) => `${item.memory_label} ${item.score.toFixed(3)}`).join(' · '),
    score: breakdown.reduce((sum, item) => sum + item.score, 0),
    rerank_mode: 'memory-summary',
    metadata: {
      memory_breakdown: breakdown,
      memory_total_score: breakdown.reduce((sum, item) => sum + item.score, 0),
    },
  }
}

const buildMemoryPlaceholderReason = (memoryType: string): RecommendationReason => ({
  source_type: 'memory',
  title: `历史偏好记忆（${memoryTypeLabel(memoryType)}）`,
  reason: `当前还没有命中${memoryTypeLabel(memoryType)}`,
  snippet: `${memoryTypeLabel(memoryType)}分数暂为 0.000`,
  score: 0,
  rerank_mode: 'memory-recall',
  metadata: {
    memory_type: memoryType,
    memory_label: memoryTypeLabel(memoryType),
  },
})

const displayRecommendationReasons = computed<RecommendationReason[]>(() => {
  const profileReasons = rawRecommendationReasons.value.filter((item) => item.source_type === 'profile')
  const memoryReasons = rawRecommendationReasons.value.filter((item) => item.source_type === 'memory')
  const otherReasons = rawRecommendationReasons.value.filter((item) => !['profile', 'memory'].includes(item.source_type))
  if (!memoryReasons.length) {
    const emptyPartials = ['session', 'episodic', 'semantic'].map((memoryType) => buildMemoryPlaceholderReason(memoryType))
    const emptyTotal = buildMemoryTotalReason(emptyPartials)
    return [...profileReasons, ...(emptyTotal ? [emptyTotal] : []), ...emptyPartials, ...otherReasons]
  }

  const totalReason = memoryReasons.find((item) => isMemoryTotalReason(item)) || buildMemoryTotalReason(memoryReasons)
  const partialReasons = memoryReasons.filter((item) => !isMemoryTotalReason(item))
  const orderedPartials = ['session', 'episodic', 'semantic'].map(
    (memoryType) =>
      partialReasons.find((item) => normalizeMemoryType(item) === memoryType) || buildMemoryPlaceholderReason(memoryType),
  )
  const remainingPartials = partialReasons.filter((item) => !orderedPartials.includes(item))

  return [...profileReasons, ...(totalReason ? [totalReason] : []), ...orderedPartials, ...remainingPartials, ...otherReasons]
})

const profileRecommendation = computed<RecommendationReason | null>(() => {
  const matched = displayRecommendationReasons.value.find((item) => item.source_type === 'profile')
  if (matched) return matched
  return {
    source_type: 'profile',
    title: '用户画像偏好',
    reason: '当前还没有足够的长期画像分数，系统会先按本次输入进行规划',
    snippet: '后续多次规划和反馈后，这里的画像分数会更稳定',
    score: 0,
    rerank_mode: 'profile-context',
    metadata: {},
  }
})

const memoryRecommendationTotal = computed<RecommendationReason | null>(() => {
  const matched = displayRecommendationReasons.value.find((item) => item.source_type === 'memory' && isMemoryTotalReason(item))
  if (matched) return matched
  return buildMemoryTotalReason(['session', 'episodic', 'semantic'].map((memoryType) => buildMemoryPlaceholderReason(memoryType)))
})

const memoryRecommendationItems = computed<RecommendationReason[]>(() =>
  ['session', 'episodic', 'semantic'].map((memoryType) => {
    return (
      displayRecommendationReasons.value.find(
        (item) => item.source_type === 'memory' && !isMemoryTotalReason(item) && normalizeMemoryType(item) === memoryType,
      ) || buildMemoryPlaceholderReason(memoryType)
    )
  }),
)

const memoryBreakdownText = (reason: RecommendationReason) => {
  const metadata = (reason.metadata || {}) as Record<string, unknown>
  const breakdown = Array.isArray(metadata.memory_breakdown) ? metadata.memory_breakdown : []
  if (!breakdown.length) return ''

  return breakdown
    .map((item) => {
      const row = item as Record<string, unknown>
      const label = String(row.memory_label || memoryTypeLabel(String(row.memory_type || '')))
      const score = Number(row.score || 0).toFixed(3)
      return `${label} ${score}`
    })
    .join(' · ')
}

const formatRecommendationReason = (reason: RecommendationReason) => {
  if (reason.source_type === 'profile') {
    return normalizeChineseText(reason.reason || '本次行程会优先参考你的长期偏好画像')
  }
  if (reason.source_type === 'memory' && isMemoryTotalReason(reason)) {
    return normalizeChineseText(reason.reason || '系统综合了你的历史偏好记忆')
  }
  if (reason.source_type === 'memory') {
    const typeLabel = memoryTypeLabel(normalizeMemoryType(reason))
    return normalizeChineseText(reason.reason || `这一项来自${typeLabel}`)
  }
  return normalizeChineseText(reason.reason || '与当前需求匹配')
}

const formatRecommendationTitle = (reason: RecommendationReason) => {
  if (reason.source_type === 'profile') return '用户画像偏好'
  if (reason.source_type === 'memory' && isMemoryTotalReason(reason)) return '历史偏好记忆总分'
  if (reason.source_type === 'memory') {
    return `历史偏好记忆（${memoryTypeLabel(normalizeMemoryType(reason))}）`
  }
  return normalizeChineseText(reason.title || sourceTypeLabel(reason.source_type))
}

const formatRecommendationSnippet = (reason: RecommendationReason) => {
  if (reason.source_type === 'profile') {
    return normalizeChineseText(reason.snippet || '系统会结合你的交通、住宿、预算和兴趣偏好来生成行程')
  }
  if (reason.source_type === 'memory' && isMemoryTotalReason(reason)) {
    return normalizeChineseText(reason.snippet || memoryBreakdownText(reason))
  }
  if (reason.source_type === 'memory') {
    const typeLabel = memoryTypeLabel(normalizeMemoryType(reason))
    return normalizeChineseText(reason.snippet || `这部分主要体现你过往的${typeLabel}`)
  }
  return normalizeChineseText(reason.snippet || '')
}

const shortText = (value: string, limit = 34) => {
  const text = String(value || '').trim()
  if (text.length <= limit) return text
  return `${text.slice(0, limit)}…`
}

const compactRecommendationText = (reason: RecommendationReason) => {
  if (reason.source_type === 'memory' && isMemoryTotalReason(reason)) {
    return memoryBreakdownText(reason)
  }

  const baseText =
    reason.source_type === 'profile'
      ? formatRecommendationReason(reason) || formatRecommendationSnippet(reason)
      : formatRecommendationReason(reason) || formatRecommendationSnippet(reason)

  return shortText(baseText || '暂无说明')
}
const appliedSkills = computed<AppliedSkill[]>(() => tripPlan.value?.applied_skills || [])

onMounted(() => {
  const data = sessionStorage.getItem('tripPlan')
  if (data) {
    tripPlan.value = JSON.parse(data)
  }
})

const clonePlan = <T>(value: T): T => JSON.parse(JSON.stringify(value))
const buildPlaceholderImage = (name: string) =>
  `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="960" height="720" viewBox="0 0 960 720">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#f3f7fb"/>
          <stop offset="100%" stop-color="#d8e8f8"/>
        </linearGradient>
      </defs>
      <rect width="960" height="720" rx="36" fill="url(#bg)"/>
      <circle cx="210" cy="180" r="96" fill="rgba(36,81,132,0.14)"/>
      <circle cx="760" cy="148" r="72" fill="rgba(255,107,53,0.16)"/>
      <path d="M130 520c102-124 224-186 366-186s248 46 334 138v116H130z" fill="rgba(36,81,132,0.12)"/>
      <text x="72" y="610" fill="#17324f" font-size="52" font-family="Segoe UI, Microsoft YaHei, sans-serif" font-weight="700">${name}</text>
      <text x="72" y="664" fill="#5f7893" font-size="28" font-family="Segoe UI, Microsoft YaHei, sans-serif">等待补充景区图片</text>
    </svg>
  `)}`

const resolveAttractionImage = (item: Attraction) => item.image_url || item.photos?.[0] || buildPlaceholderImage(item.name)
const hasValidLocation = (location?: Attraction['location'] | null): location is Attraction['location'] =>
  Boolean(location && Number.isFinite(location.longitude) && Number.isFinite(location.latitude))

const isSuspiciousPlaceholderLocation = (location: Attraction['location'] | null | undefined, city: string) => {
  if (!hasValidLocation(location)) return true
  const normalizedCity = String(city || '').trim().toLowerCase()
  if (normalizedCity.includes('beijing') || normalizedCity.includes('北京')) {
    return false
  }
  return Math.abs(location.longitude - 116.4) <= 0.35 && Math.abs(location.latitude - 39.9) <= 0.35
}

const getSafeRouteLocation = (location: Attraction['location'] | null | undefined, city: string) =>
  hasValidLocation(location) && !isSuspiciousPlaceholderLocation(location, city) ? location : undefined

const normalizeRouteType = (transportation: string): 'walking' | 'driving' | 'transit' => {
  const text = String(transportation || '').toLowerCase()
  if (['metro', 'subway', 'bus', 'transit', '地铁', '公交'].some((token) => text.includes(token))) {
    return 'transit'
  }
  if (['taxi', 'car', 'drive', '打车', '驾车', '网约车'].some((token) => text.includes(token))) {
    return 'driving'
  }
  return 'walking'
}
const normalizeActiveKeys = (keys: string | number | Array<string | number>) => {
  if (Array.isArray(keys)) {
    return keys.map((item) => String(item))
  }
  if (keys == null || keys === '') {
    return []
  }
  return [String(keys)]
}
const resetDayRoute = (dayIndex?: number) => {
  if (dayIndex == null) {
    routeDetails.value = {}
    routeLoading.value = {}
    routeErrors.value = {}
    return
  }
  delete routeDetails.value[dayIndex]
  delete routeLoading.value[dayIndex]
  delete routeErrors.value[dayIndex]
}
const buildDayRoutePayload = (day: DayPlan): DayRoutePayload => ({
  city: tripPlan.value?.city || '',
  route_type: normalizeRouteType(day.transportation),
  hotel: null,
  attractions: day.attractions.map((item) => ({
    name: item.name,
    address: item.address,
    location: getSafeRouteLocation(item.location, tripPlan.value?.city || ''),
    image_url: resolveAttractionImage(item),
  })),
})
const buildLocalRouteMarkers = (day: DayPlan): DayRouteMarker[] =>
  day.attractions
    .map((item) => ({
      item,
      location: getSafeRouteLocation(item.location, tripPlan.value?.city || ''),
    }))
    .filter((entry) => Boolean(entry.location))
    .map(({ item, location }, index) => ({
      label: String(index + 1),
      title: item.name,
      kind: 'attraction',
      address: item.address || '',
      location: location!,
      image_url: resolveAttractionImage(item),
    }))

const buildStraightSegments = (markers: DayRouteMarker[], routeType: DayRoutePayload['route_type']): DayRouteSegment[] =>
  markers.slice(0, -1).map((marker, index) => ({
    start_label: marker.label,
    end_label: markers[index + 1].label,
    route_type: routeType,
    distance: 0,
    duration: 0,
    description: `${marker.title} → ${markers[index + 1].title}`,
    polyline: [marker.location, markers[index + 1].location],
  }))

const buildFallbackRouteInfo = (day: DayPlan): DayRouteInfo | null => {
  const markers = buildLocalRouteMarkers(day)
  if (!markers.length) return null
  const routeType = normalizeRouteType(day.transportation)
  return {
    route_type: routeType,
    summary: day.route_summary || `建议按 ${markers.map((item) => item.title).join(' → ')} 的顺序游览`,
    distance: 0,
    duration: 0,
    markers,
    segments: buildStraightSegments(markers, routeType),
    fallback_static_map_url: day.route_map_url || null,
  }
}

const getRenderableDayRoute = (dayIndex: number, day: DayPlan): DayRouteInfo | null => {
  const detail = routeDetails.value[dayIndex]
  const markers = buildLocalRouteMarkers(day)
  if (!detail) {
    return buildFallbackRouteInfo(day)
  }

  const resolvedMarkers = detail.markers?.length ? detail.markers : markers
  return {
    ...detail,
    markers: resolvedMarkers,
    segments: detail.segments?.length
      ? detail.segments
      : buildStraightSegments(resolvedMarkers, normalizeRouteType(day.transportation)),
    summary: detail.summary || day.route_summary || '',
    fallback_static_map_url: detail.fallback_static_map_url || day.route_map_url || null,
  }
}

const ensureDayRoute = async (dayIndex: number, force = false) => {
  if (!tripPlan.value) return
  if (!force && (routeDetails.value[dayIndex] || routeLoading.value[dayIndex])) return

  const day = tripPlan.value.days[dayIndex]
  if (!day) return

  routeLoading.value[dayIndex] = true
  delete routeErrors.value[dayIndex]
  try {
    const response = await getDayRouteDetail(buildDayRoutePayload(day))
    if (response.data) {
      routeDetails.value[dayIndex] = response.data
    }
  } catch (error: any) {
    routeErrors.value[dayIndex] = error.message || '加载每日路线失败，已回退到静态地图'
  } finally {
    routeLoading.value[dayIndex] = false
  }
}
const refreshActiveDayRoutes = () => {
  activeDayKeys.value.forEach((key) => {
    void ensureDayRoute(Number(key), true)
  })
}
const handleDayPanelsChange = (keys: string | number | Array<string | number>) => {
  activeDayKeys.value = normalizeActiveKeys(keys)
  activeDayKeys.value.forEach((key) => {
    void ensureDayRoute(Number(key))
  })
}

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
  resetDayRoute()
  refreshActiveDayRoutes()
  message.success('已保存修改')
}

const cancelEdit = () => {
  if (!originalPlan.value) return
  tripPlan.value = clonePlan(originalPlan.value)
  editMode.value = false
  resetDayRoute()
  refreshActiveDayRoutes()
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
  resetDayRoute(dayIndex)
  if (activeDayKeys.value.includes(String(dayIndex))) {
    void ensureDayRoute(dayIndex, true)
  }
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
  resetDayRoute(dayIndex)
  if (activeDayKeys.value.includes(String(dayIndex))) {
    void ensureDayRoute(dayIndex, true)
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

const transportationLabel = (value?: string) => {
  const text = String(value || '').toLowerCase()
  if (!text) return '待确认'
  if (text.includes('public transit') || text.includes('transit') || text.includes('bus') || text.includes('subway')) {
    return '公共交通'
  }
  if (text.includes('drive') || text.includes('driving') || text.includes('car')) {
    return '自驾或打车'
  }
  if (text.includes('walk') || text.includes('walking')) {
    return '步行'
  }
  return value || '待确认'
}

const accommodationLabel = (value?: string) => {
  const mapping: Record<string, string> = {
    'Budget Hotel': '经济酒店',
    'Comfort Hotel': '舒适酒店',
    'Luxury Hotel': '高端酒店',
    Homestay: '民宿',
  }
  return mapping[value || ''] || value || '待确认'
}

const hotelTypeLabel = (value?: string) => {
  if (!value) return '暂无'
  return accommodationLabel(value)
}

const priceRangeLabel = (value?: string) => {
  if (!value) return '暂无'
  return value
    .replace(/Budget/gi, '经济')
    .replace(/Comfort/gi, '舒适')
    .replace(/Luxury/gi, '高端')
}

const sourceTypeLabel = (sourceType: string) => {
  const mapping: Record<string, string> = {
    knowledge_base: '知识库',
    memory: '历史记忆',
    profile: '用户画像',
  }
  return mapping[sourceType] || sourceType
}

const skillLayerLabel = (layer?: string) => {
  const mapping: Record<string, string> = {
    static: '静态',
    dynamic: '动态',
  }
  return mapping[String(layer || '').toLowerCase()] || '技能'
}

const skillCategoryLabel = (category?: string) => {
  const mapping: Record<string, string> = {
    hard: '硬约束',
    'dynamic-hard': '动态约束',
    style: '偏好',
  }
  return mapping[String(category || '').toLowerCase()] || '通用'
}

const skillCategoryColor = (category?: string) => {
  const mapping: Record<string, string> = {
    hard: 'red',
    'dynamic-hard': 'orange',
    style: 'green',
  }
  return mapping[String(category || '').toLowerCase()] || 'default'
}

const skillSourceLabel = (source?: string) => {
  const mapping: Record<string, string> = {
    static: '静态命中',
    dynamic: '动态补充',
  }
  return mapping[String(source || '').toLowerCase()] || '已命中'
}

const formatScore = (value: number | undefined) => Number(value || 0).toFixed(3)

const formatDistance = (distance?: number) => {
  const value = Number(distance || 0)
  if (value <= 0) return '待确认'
  if (value >= 1000) return `${(value / 1000).toFixed(1)} 公里`
  return `${Math.round(value)} 米`
}

const formatDuration = (duration?: number) => {
  const value = Number(duration || 0)
  if (value <= 0) return '待确认'
  const totalMinutes = Math.max(1, Math.round(value / 60))
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours && minutes) return `${hours}小时${minutes}分钟`
  if (hours) return `${hours}小时`
  return `${minutes}分钟`
}

const currency = (value?: number) => {
  const amount = Number(value || 0)
  return amount > 0 ? `¥${amount}` : '待确认'
}

const weatherIcon = (weather?: string, period: 'day' | 'night' = 'day') => {
  const text = String(weather || '')
  if (text.includes('雷')) return { symbol: '⚡', className: 'weather-card__icon--storm' }
  if (text.includes('雪')) return { symbol: '❄', className: 'weather-card__icon--snow' }
  if (text.includes('雨')) return { symbol: '☂', className: 'weather-card__icon--rain' }
  if (text.includes('阴')) return { symbol: '☁', className: 'weather-card__icon--cloudy' }
  if (text.includes('多云')) return period === 'day'
    ? { symbol: '⛅', className: 'weather-card__icon--partly' }
    : { symbol: '☁', className: 'weather-card__icon--cloudy' }
  if (text.includes('晴')) return period === 'day'
    ? { symbol: '☀', className: 'weather-card__icon--sunny' }
    : { symbol: '☾', className: 'weather-card__icon--night' }
  if (text.includes('雾') || text.includes('霾')) return { symbol: '〰', className: 'weather-card__icon--fog' }
  return period === 'day'
    ? { symbol: '☀', className: 'weather-card__icon--sunny' }
    : { symbol: '☾', className: 'weather-card__icon--night' }
}
</script>

<style scoped>
.result-shell-with-nav {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

.result-main-content {
  min-width: 0;
}

.result-sidebar-nav {
  position: sticky;
  top: 102px;
  padding: 22px 18px;
  display: grid;
  gap: 16px;
}

.result-sidebar-nav__group {
  display: grid;
  gap: 10px;
}

.result-sidebar-nav__divider {
  height: 1px;
  background: linear-gradient(90deg, rgba(134, 171, 215, 0.12), rgba(134, 171, 215, 0.5), rgba(134, 171, 215, 0.12));
}

.result-sidebar-nav__label {
  color: #41586f;
  font-size: 16px;
  font-weight: 700;
}

.result-nav-button {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid rgba(160, 195, 235, 0.4);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.56);
  color: #17324f;
  font-size: 16px;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.result-nav-button:hover {
  transform: translateY(-1px);
  background: rgba(231, 243, 255, 0.86);
  border-color: rgba(127, 177, 234, 0.7);
  box-shadow: 0 10px 18px rgba(118, 164, 217, 0.12);
}

.result-nav-button--day {
  font-size: 16px;
  color: #35526d;
}

#result-hero,
#result-budget,
#result-days,
#result-weather,
#result-reasons {
  scroll-margin-top: 112px;
}

.result-hero,
.result-panel {
  padding: 28px;
  margin-bottom: 18px;
}

.result-title {
  font-size: clamp(36px, 4vw, 54px);
  color: #111111;
  font-weight: 800;
}

.result-hero .page-kicker {
  font-size: 17px;
}

.section-heading h2,
.section-heading h3,
.route-copy h3,
.empty-state h2 {
  color: #111111;
  font-weight: 800;
}

.reason-card,
.entity-card {
  width: 100%;
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.recommendation-layout {
  display: grid;
  gap: 22px;
}

.recommendation-group {
  display: grid;
  gap: 16px;
  padding: 20px;
  border-radius: 24px;
  border: 1px solid rgba(201, 220, 242, 0.72);
  background: linear-gradient(135deg, rgba(249, 252, 255, 0.84), rgba(235, 244, 255, 0.82));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.58);
}

.recommendation-group__heading {
  margin-bottom: 0;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(132, 173, 220, 0.28);
}

.recommendation-main-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.82), rgba(236, 244, 255, 0.94));
  border: 1px solid rgba(172, 203, 240, 0.82);
  box-shadow: 0 12px 24px rgba(122, 166, 217, 0.1);
}

.reason-score-hero {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
}

.reason-score-hero span {
  color: var(--brand-muted);
  font-size: 17px;
  font-weight: 600;
}

.reason-score-hero strong {
  color: #17324f;
  font-size: 26px;
  font-weight: 800;
}

.recommendation-main-card--profile .reason-score-hero {
  background: linear-gradient(135deg, rgba(224, 239, 255, 0.9), rgba(245, 249, 255, 0.96));
  border: 1px solid rgba(184, 210, 243, 0.72);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.recommendation-main-card--memory .reason-score-hero,
.reason-score-hero--memory {
  background: linear-gradient(135deg, rgba(227, 240, 255, 0.9), rgba(246, 250, 255, 0.96));
  border: 1px solid rgba(188, 213, 243, 0.72);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.memory-reason-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.memory-reason-card {
  min-height: 100%;
  background: rgba(255, 255, 255, 0.72);
  border-color: rgba(196, 217, 243, 0.78);
}

.memory-reason-card:nth-child(1) .memory-reason-card__score {
  background: rgba(231, 242, 255, 0.82);
}

.memory-reason-card:nth-child(2) .memory-reason-card__score {
  background: rgba(237, 246, 255, 0.82);
}

.memory-reason-card:nth-child(3) .memory-reason-card__score {
  background: linear-gradient(135deg, rgba(229, 240, 255, 0.9), rgba(244, 249, 255, 0.92));
}

.memory-reason-card__score {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(234, 242, 255, 0.7);
}

.memory-reason-card__score span {
  color: var(--brand-muted);
  font-size: 17px;
  font-weight: 600;
}

.memory-reason-card__score strong {
  color: #245184;
  font-size: 21px;
  font-weight: 800;
}

.reason-card__head,
.entity-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.entity-card__header strong {
  font-size: 23px;
  line-height: 1.35;
}

.reason-card p,
.entity-card p,
.day-summary p,
.brand-stat p {
  margin: 0 0 8px;
  color: var(--brand-muted);
  font-size: 17px;
  line-height: 1.75;
}

.budget-grid,
.weather-grid,
.skill-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}

.weather-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 280px));
  justify-content: start;
}

.skill-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.budget-total {
  background: linear-gradient(135deg, rgba(255,255,255,0.72), rgba(231,240,255,0.86));
}

.day-summary {
  margin-bottom: 18px;
  padding: 18px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(214, 228, 244, 0.75);
}

.day-summary--embedded {
  margin-bottom: 0;
}

.day-layout {
  display: grid;
  grid-template-columns: minmax(360px, 0.92fr) minmax(0, 1.08fr);
  gap: 20px;
  align-items: start;
}

.day-map-card,
.day-content-card {
  margin-bottom: 0;
}

.day-content-card {
  display: grid;
  gap: 18px;
}

.day-section {
  display: grid;
  gap: 12px;
}

.day-section--full {
  width: 100%;
}

.day-section--divider {
  padding-top: 18px;
  border-top: 1px solid rgba(208, 223, 240, 0.82);
}

.section-split {
  margin-top: 18px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(247, 251, 255, 0.72);
  border: 1px solid rgba(219, 232, 247, 0.84);
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

.route-card {
  display: grid;
  gap: 16px;
}

.route-copy h3 {
  margin: 0 0 10px;
  font-size: 22px;
}

.compact-heading h3 {
  font-size: 22px;
}

.entity-card--full {
  margin-bottom: 0;
}

.hotel-compact {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.hotel-compact--panel {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(214, 228, 244, 0.8);
}

.hotel-compact__image {
  height: 220px;
  min-height: 220px;
}

.hotel-compact__content {
  display: grid;
  gap: 14px;
}

.hotel-compact__content p,
.route-copy p,
.meal-card p {
  font-size: 17px;
  line-height: 1.8;
}

.meal-card p {
  font-size: 17px;
  line-height: 1.8;
}

.meal-card__budget {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.meal-card__budget span {
  white-space: nowrap;
}

.meal-card__reason {
  display: block;
  white-space: normal;
}

.meal-card__reason span {
  white-space: normal;
}

.hotel-compact--no-image {
  grid-template-columns: 1fr;
}

.hotel-compact__title {
  color: #17324f;
  font-size: 22px;
  font-weight: 800;
}

.hotel-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.hotel-meta-card {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(217, 230, 245, 0.82);
}

.hotel-meta-card--wide {
  grid-column: 1 / -1;
}

.hotel-meta-card strong {
  color: #17324f;
  font-size: 16px;
  font-weight: 700;
}

.hotel-meta-card span {
  color: var(--brand-muted);
  font-size: 17px;
  line-height: 1.7;
}

.entity-media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 12px;
}

.attraction-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  align-items: stretch;
}

.attraction-row__media {
  width: 100%;
  height: 100%;
}

.attraction-row__image {
  height: 300px;
  min-height: 300px;
}

.attraction-row__content {
  display: grid;
  gap: 14px;
}

.attraction-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.attraction-meta-card {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(217, 230, 245, 0.82);
}

.attraction-meta-card--wide {
  grid-column: 1 / -1;
}

.attraction-meta-card strong,
.attraction-copy strong {
  color: #17324f;
  font-size: 16px;
  font-weight: 700;
}

.attraction-meta-card span {
  color: var(--brand-muted);
  font-size: 17px;
  line-height: 1.7;
}

.attraction-copy {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(217, 230, 245, 0.76);
}

.attraction-copy p {
  margin: 8px 0 0;
  color: var(--brand-muted);
  font-size: 17px;
  line-height: 1.8;
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

.meal-card > strong {
  display: block;
  margin-bottom: 10px;
  font-size: 19px;
  line-height: 1.35;
}

.meal-card p strong {
  font-size: 17px;
  line-height: 1.8;
}

.weather-card {
  padding: 20px 22px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(188, 233, 244, 0.88), rgba(174, 225, 238, 0.92));
  border: 1px solid rgba(148, 210, 228, 0.9);
  box-shadow: 0 16px 30px rgba(114, 177, 201, 0.16);
}

.weather-card__date {
  margin-bottom: 18px;
  text-align: center;
  color: #007a78;
  font-size: 28px;
  font-weight: 800;
}

.weather-card__body {
  display: grid;
  gap: 18px;
}

.weather-card__period {
  display: flex;
  align-items: center;
  gap: 16px;
}

.weather-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  text-align: center;
  font-size: 28px;
  line-height: 1;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.weather-card__icon--sunny {
  color: #f4a300;
}

.weather-card__icon--night {
  color: #5a6ff0;
}

.weather-card__icon--partly {
  color: #e3a122;
}

.weather-card__icon--cloudy {
  color: #7f93aa;
}

.weather-card__icon--rain {
  color: #2d86de;
}

.weather-card__icon--snow {
  color: #5cb4d6;
}

.weather-card__icon--storm {
  color: #f29b1f;
}

.weather-card__icon--fog {
  color: #87a0b5;
}

.weather-card__label {
  color: #355f6e;
  font-size: 16px;
}

.weather-card__value {
  color: #007a78;
  font-size: 18px;
  font-weight: 800;
}

.weather-card__footer {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid rgba(84, 160, 182, 0.35);
  color: #0f6676;
  font-size: 16px;
  text-align: center;
}

.skill-card {
  margin-bottom: 0;
}

@media (max-width: 960px) {
  .result-shell-with-nav {
    grid-template-columns: 1fr;
  }

  .result-sidebar-nav {
    position: static;
    top: auto;
  }

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

  .day-layout {
    grid-template-columns: 1fr;
  }

  .hotel-compact {
    grid-template-columns: 1fr;
  }

  .hotel-compact__image {
    height: 220px;
    min-height: 220px;
  }

  .hotel-meta-grid {
    grid-template-columns: 1fr;
  }

  .section-split {
    padding: 16px;
  }

  .attraction-row {
    grid-template-columns: 1fr;
  }

  .attraction-row__image {
    height: 260px;
    min-height: 260px;
  }

  .attraction-meta-grid {
    grid-template-columns: 1fr;
  }

  .memory-reason-grid {
    grid-template-columns: 1fr;
  }

  .recommendation-group {
    padding: 16px;
  }

  .weather-card__date {
    font-size: 24px;
  }
}
</style>
