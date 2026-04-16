<template>
  <div class="brand-page">
    <div class="brand-shell">
        <div class="glass-toolbar">
          <div class="toolbar-group">
            <a-button size="large" @click="goBack">↩️ 返回旅行规划</a-button>
          </div>
        <div class="toolbar-group">
          <a-button v-if="tripPlan" :loading="exportingPdf" @click="exportTripPlan">📄 导出 PDF</a-button>
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
              <button v-if="displayBudget" type="button" class="result-nav-button" @click="scrollToSection('result-budget')">💰 预算汇总</button>
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
                v-if="isDeveloperUser && appliedSkills.length"
                type="button"
                class="result-nav-button"
                @click="scrollToSection('result-skills')"
              >
                🧩 已启用技能
              </button>
              <button v-if="decisionScoreView" type="button" class="result-nav-button result-nav-button--accent" @click="scrollToSection('result-score')">📊 最终评分</button>
            </div>
          </aside>

          <div class="result-main-content">
        <section id="result-hero" class="glass-panel result-hero">
          <span class="page-kicker">🗓️ 行程结果</span>
          <h1 class="page-title result-title">{{ tripPlan.city }}</h1>
          <p class="result-meta-line">{{ resultMetaLine }}</p>
          <div class="result-hero-tags">
            <span v-for="tag in resultHeroTags" :key="tag" class="result-hero-tag">{{ tag }}</span>
          </div>
        </section>

        <section id="result-budget" v-if="displayBudget" class="glass-panel glass-panel--soft result-panel">
          <div class="section-heading">
            <h2>💰 预算汇总</h2>
            <p>费用为参考估算，方便你快速判断本次行程的整体花费</p>
          </div>
          <div class="budget-grid">
            <div class="brand-stat">
              <span>📍 景点</span>
              <strong>{{ currency(displayBudget.total_attractions) }}</strong>
            </div>
            <div class="brand-stat">
              <span>🏨 酒店</span>
              <strong>{{ currency(displayBudget.total_hotels) }}</strong>
            </div>
            <div class="brand-stat">
              <span>🍽️ 餐饮</span>
              <strong>{{ currency(displayBudget.total_meals) }}</strong>
            </div>
            <div class="brand-stat">
              <span>🚇 交通</span>
              <strong>{{ currency(displayBudget.total_transportation) }}</strong>
            </div>
            <div class="brand-stat budget-total">
              <span>🧾 总计</span>
              <strong>{{ currency(displayBudget.total) }}</strong>
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
                <div class="entity-card hotel-compact hotel-compact--panel">
                  <div class="hotel-compact__map">
                    <DayRouteMap
                      class="hotel-location-map"
                      :route="buildHotelLocationRoute(day)"
                      :loading="false"
                      :error="null"
                      :fallback-static-map-url="day.hotel.map_image_url || null"
                    />
                  </div>
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
          <div class="recommendation-simple">
            <article v-if="profileRecommendation" class="recommendation-strip">
              <div class="recommendation-strip__top">
                <div>
                  <span class="recommendation-strip__label">👤 用户画像</span>
                  <strong>{{ formatRecommendationTitle(profileRecommendation) }}</strong>
                </div>
                <span class="recommendation-strip__score">评分 {{ formatScore(profileRecommendation.score) }}</span>
              </div>
              <p>{{ compactRecommendationText(profileRecommendation) }}</p>
            </article>

            <article v-if="memoryRecommendationTotal" class="recommendation-strip recommendation-strip--memory">
              <div class="recommendation-strip__top">
                <div>
                  <span class="recommendation-strip__label">🧠 历史记忆</span>
                  <strong>{{ formatRecommendationTitle(memoryRecommendationTotal) }}</strong>
                </div>
                <span class="recommendation-strip__score">评分 {{ formatScore(memoryRecommendationTotal.score) }}</span>
              </div>
              <p>{{ compactRecommendationText(memoryRecommendationTotal) }}</p>
              <div class="memory-inline-list">
                <div
                  v-for="item in memoryRecommendationItems"
                  :key="formatRecommendationTitle(item)"
                  class="memory-inline-item"
                >
                  <span>{{ memoryTypeLabel(normalizeMemoryType(item)) }}</span>
                  <strong>{{ formatScore(item.score) }}</strong>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section
          id="result-skills"
          v-if="isDeveloperUser && appliedSkills.length"
          class="glass-panel glass-panel--soft result-panel"
        >
          <div class="section-heading">
            <h2>🧩 已启用技能</h2>
            <p>这里展示了本次行程实际生效的技能，以及命中的字段、关键词和触发原因</p>
          </div>
          <div class="skill-grid">
            <div v-for="skill in appliedSkills" :key="skill.key" class="reason-card skill-card">
              <div class="reason-card__head skill-card__head">
                <strong class="skill-card__title">{{ skill.name }}</strong>
                <div class="toolbar-group skill-card__tags">
                  <a-tag color="blue">{{ skillLayerLabel(skill.layer) }}</a-tag>
                  <a-tag :color="skillCategoryColor(skill.category)">{{ skillCategoryLabel(skill.category) }}</a-tag>
                  <a-tag>{{ skillSourceLabel(skill.source) }}</a-tag>
                </div>
              </div>
              <p v-if="skill.description"><strong>说明：</strong>{{ skill.description }}</p>
              <p v-if="skill.matched_fields?.length"><strong>命中字段：</strong>{{ formatMatchedFields(skill.matched_fields).join('、') }}</p>
              <p v-if="skill.matched_terms?.length"><strong>命中词：</strong>{{ skill.matched_terms.join('、') }}</p>
              <p v-if="skill.reasons?.length"><strong>触发原因：</strong>{{ skill.reasons.join('；') }}</p>
            </div>
          </div>
        </section>

        <section id="result-score" v-if="decisionScoreView" class="glass-panel glass-panel--soft result-panel result-panel--decision">
          <div class="score-hero">
            <div class="section-heading">
              <h2>📊 最终方案评分</h2>
              <p>{{ scoreLiveStatusText }}</p>
            </div>
            <div class="score-hero__meta">
              <span class="score-hero__eyebrow">当前方案画像</span>
              <strong>{{ decisionScoreView.summary }}</strong>
              <p>{{ decisionScoreView.story || '这里会根据当前行程内容、预算、路线和执行弹性，给出这一版方案的立体判断。' }}</p>
            </div>
          </div>

          <div class="score-overview score-overview--final">
            <article class="score-overview-card score-overview-card--primary">
              <span class="score-overview-card__label">当前综合分</span>
              <strong>{{ decisionScoreView.overall }}</strong>
              <p>当前预算 {{ currency(decisionScoreView.budget.total) }}</p>
            </article>

            <article class="score-overview-card score-overview-card--mood">
              <span class="score-overview-card__label">当前旅行气质</span>
              <strong>{{ scoreMood.label }}</strong>
              <p>{{ scoreMood.description }}</p>
            </article>

            <article class="score-overview-card">
              <span class="score-overview-card__label">路线与舒适度</span>
              <strong>{{ decisionScoreView.estimated_distance_text }}</strong>
              <p>{{ decisionScoreView.comfort_text }}</p>
            </article>
          </div>

          <div class="score-badge-row" v-if="decisionScoreView.highlights.length || decisionScoreView.risks.length">
            <span
              v-for="item in decisionScoreView.highlights"
              :key="item"
              class="score-badge score-badge--good"
            >
              {{ item }}
            </span>
            <span
              v-for="item in decisionScoreView.risks"
              :key="item"
              class="score-badge score-badge--risk"
            >
              {{ item }}
            </span>
          </div>

          <div class="score-grid">
            <article
              v-for="dimension in decisionScoreView.dimensions"
              :key="dimension.key"
              class="score-card"
            >
              <div class="score-card__head">
                <div>
                  <span class="score-card__eyebrow">当前方案维度</span>
                  <strong>{{ dimension.label }}</strong>
                  <p>{{ dimension.description }}</p>
                </div>
                <div class="score-card__scorebox">
                  <span class="score-card__score">{{ dimension.score }}</span>
                  <span class="score-card__status" :class="scoreStatusClass(dimension.score)">
                    {{ scoreStatusLabel(dimension.score) }}
                  </span>
                </div>
              </div>

              <div class="score-card__meter">
                <div class="score-card__meter-track">
                  <div class="score-card__meter-fill" :style="{ width: `${dimension.score}%` }"></div>
                </div>
                <span>{{ dimension.score }}/100</span>
              </div>

              <p class="score-card__detail">{{ dimension.detail }}</p>
              <p v-if="dimension.narrative" class="score-card__narrative">{{ dimension.narrative }}</p>

              <button type="button" class="score-card__toggle" @click="toggleScoreDimension(dimension.key)">
                {{ isScoreDimensionExpanded(dimension.key) ? '收起打分过程' : '查看这个分数怎么来的' }}
              </button>

              <div v-if="isScoreDimensionExpanded(dimension.key)" class="score-card__recipe">
                <div class="score-card__recipe-title">分数生成过程</div>
                <div class="score-factor-list">
                  <article
                    v-for="(factor, index) in dimension.factors || []"
                    :key="`${dimension.key}-${index}-${factor.label}`"
                    class="score-factor"
                  >
                    <div class="score-factor__head">
                      <strong>{{ factor.label }}</strong>
                      <span class="score-factor__impact" :class="scoreFactorClass(factor.impact)">
                        {{ formatFactorImpact(factor.impact) }}
                      </span>
                    </div>
                    <p>{{ factor.reason }}</p>
                    <span v-if="factor.value" class="score-factor__value">{{ factor.value }}</span>
                  </article>
                </div>
              </div>
            </article>
          </div>
        </section>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

import DayRouteMap from '@/components/DayRouteMap.vue'
import {
  evaluateTripDecisionScore,
  getCommunityPostPlan,
  getDayRouteDetail,
  getTravelTrackPlan,
  submitFeedback,
} from '@/services/api'
import type {
  Budget,
  AppliedSkill,
  Attraction,
  DayPlan,
  DayRouteInfo,
  DayRouteMarker,
  DayRoutePayload,
  DayRouteSegment,
  DecisionScoreSnapshot,
  FeedbackPayload,
  RecommendationReason,
  TripPlan,
  TripScoreSummary,
} from '@/types'
import { useAuthState } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const authState = useAuthState()
const isDeveloperUser = computed(() => authState.user?.is_developer === true)
const tripPlan = ref<TripPlan | null>(null)
const originalPlan = ref<TripPlan | null>(null)
const decisionScore = ref<DecisionScoreSnapshot | null>(null)
const scoreLoading = ref(false)
const scoreError = ref('')
const editMode = ref(false)
const currentUserId = ref(authState.user?.id || sessionStorage.getItem('tripPlannerUserId') || '')
const currentSessionId = ref(sessionStorage.getItem('tripPlannerSessionId') || '')
const tripPlannerSummary = ref<TripScoreSummary | null>(null)
const activeDayKeys = ref<string[]>([])
const routeDetails = ref<Record<number, DayRouteInfo>>({})
const routeLoading = ref<Record<number, boolean>>({})
const routeErrors = ref<Record<number, string>>({})
const exportingPdf = ref(false)
const expandedScoreDimensionKeys = ref<string[]>([])

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

const MEMORY_SCORE_WEIGHTS: Record<string, number> = {
  session: 1,
  episodic: 1,
  semantic: 1,
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
      weight: MEMORY_SCORE_WEIGHTS[memoryType] || 1,
    }
  })

  const totalWeight = breakdown.reduce((sum, item) => sum + item.weight, 0) || 1
  const weightedAverageScore = breakdown.reduce((sum, item) => sum + item.score * item.weight, 0) / totalWeight

  return {
    source_type: 'memory',
    title: '历史偏好记忆总分',
    reason: `当前共命中 ${breakdown.length} 类历史偏好记忆`,
    snippet: breakdown.map((item) => `${item.memory_label} ${item.score.toFixed(3)}`).join(' · '),
    score: weightedAverageScore,
    rerank_mode: 'memory-summary',
    metadata: {
      memory_breakdown: breakdown,
      memory_total_score: weightedAverageScore,
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

  const partialReasons = memoryReasons.filter((item) => !isMemoryTotalReason(item))
  const orderedPartials = ['session', 'episodic', 'semantic'].map(
    (memoryType) =>
      partialReasons.find((item) => normalizeMemoryType(item) === memoryType) || buildMemoryPlaceholderReason(memoryType),
  )
  const remainingPartials = partialReasons.filter((item) => !orderedPartials.includes(item))
  const totalReason = buildMemoryTotalReason([...orderedPartials, ...remainingPartials])

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

const buildPlanBudget = (plan: TripPlan): Budget => {
  const totals = plan.days.reduce(
    (acc, day) => {
      acc.total_attractions += day.attractions.reduce((sum, item) => sum + Number(item.ticket_price || 0), 0)
      acc.total_hotels += Number(day.hotel?.estimated_cost || 0)
      acc.total_meals += day.meals.reduce((sum, item) => sum + Number(item.estimated_cost || 0), 0)
      acc.total_transportation += Number(day.transportation_cost || 0)
      return acc
    },
    {
      total_attractions: 0,
      total_hotels: 0,
      total_meals: 0,
      total_transportation: 0,
    },
  )

  return {
    ...totals,
    total: totals.total_attractions + totals.total_hotels + totals.total_meals + totals.total_transportation,
  }
}
const displayBudget = computed<Budget | null>(() => (tripPlan.value ? buildPlanBudget(tripPlan.value) : null))
const decisionScoreView = computed(() => decisionScore.value)
const scoreMood = computed(() => {
  const overall = decisionScoreView.value?.overall || 0
  if (overall >= 90) {
    return {
      label: '顺手发光型',
      description: '主线清楚、转场流畅，像已经热好身就能直接出发的一版。',
    }
  }
  if (overall >= 80) {
    return {
      label: '稳稳出发型',
      description: '整体已经能打，少数细节再收一收，体验会更丝滑。',
    }
  }
  if (overall >= 70) {
    return {
      label: '可玩待抛光',
      description: '骨架不错，但个别环节还会决定你是顺着玩，还是边玩边修。',
    }
  }
  return {
    label: '继续打磨型',
    description: '核心内容已经有了，不过还需要再把节奏、预算或路线拧紧一点。',
  }
})
const scoreLiveStatusText = computed(() =>
  scoreLoading.value
    ? '系统正在根据你刚刚的修改重算这版方案的实时评分'
    : scoreError.value
    ? `评分暂未刷新：${scoreError.value}`
    : editMode.value
    ? '你正在编辑行程，系统现在只看这版方案本身，景点增删和顺序变化都会立刻反映到各维得分里'
    : '以下为当前方案的各维度分数，可通过点开维度卡片来查看打分过程',
)
const scoreStatusLabel = (value: number) => {
  if (value >= 85) return '状态很稳'
  if (value >= 75) return '基本顺手'
  if (value >= 65) return '还能再抛光'
  return '建议再调整'
}
const scoreStatusClass = (value: number) => ({
  'score-status--good': value >= 85,
  'score-status--mid': value >= 75 && value < 85,
  'score-status--warn': value < 75,
})
const formatFactorImpact = (value: number) => {
  const rounded = Math.abs(value - Math.round(value)) < 0.05 ? Math.round(value) : Number(value).toFixed(1)
  if (value > 0) return `+${rounded}`
  if (value < 0) return `${rounded}`
  return '±0'
}
const scoreFactorClass = (value: number) => ({
  'score-factor__impact--positive': value > 0,
  'score-factor__impact--negative': value < 0,
  'score-factor__impact--neutral': value === 0,
})
const toggleScoreDimension = (key: string) => {
  expandedScoreDimensionKeys.value = expandedScoreDimensionKeys.value.includes(key)
    ? expandedScoreDimensionKeys.value.filter((item) => item !== key)
    : [...expandedScoreDimensionKeys.value, key]
}
const isScoreDimensionExpanded = (key: string) => expandedScoreDimensionKeys.value.includes(key)

let scoreRefreshTimer: number | null = null

const refreshDecisionScore = async (options?: { silent?: boolean }) => {
  if (!tripPlan.value) return
  scoreLoading.value = true
  scoreError.value = ''
  try {
    const response = await evaluateTripDecisionScore({
      plan: tripPlan.value,
      summary: tripPlannerSummary.value,
    })
    if (!response.data) {
      throw new Error('评分结果为空')
    }
    decisionScore.value = response.data
    if (!editMode.value) {
      tripPlan.value.decision_score = response.data
    }
  } catch (error: any) {
    scoreError.value = error.message || '评分计算失败'
    if (!options?.silent) {
      message.warning(scoreError.value)
    }
  } finally {
    scoreLoading.value = false
  }
}

const scheduleDecisionScoreRefresh = () => {
  if (!editMode.value || !tripPlan.value) return
  if (scoreRefreshTimer) {
    clearTimeout(scoreRefreshTimer)
  }
  scoreRefreshTimer = window.setTimeout(() => {
    void refreshDecisionScore({ silent: true })
  }, 360)
}

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
const resultDateText = computed(() => {
  if (!tripPlan.value) return ''
  return `${tripPlan.value.start_date.replace(/-/g, '.')} - ${tripPlan.value.end_date.replace(/-/g, '.')}`
})
const resultDurationText = computed(() => {
  if (!tripPlan.value) return ''
  const dayCount = tripPlan.value.days.length || 1
  const nightCount = Math.max(0, dayCount - 1)
  return `${dayCount}天${nightCount}晚`
})
const resultBudgetText = computed(() => {
  const mapping: Record<string, string> = {
    low: '低预算',
    medium: '中预算',
    high: '高预算',
  }
  return mapping[String(tripPlannerSummary.value?.budget_level || '').toLowerCase()] || '预算待定'
})
const resultPaceText = computed(() => {
  const styles = tripPlannerSummary.value?.travel_style || []
  if (styles.includes('slow')) return '轻松节奏'
  if (styles.includes('citywalk')) return '城市漫游'
  if (styles.includes('checkin')) return '经典打卡'
  if (styles.includes('local')) return '本地体验'
  return '灵活节奏'
})
const resultMetaLine = computed(() =>
  [resultDateText.value, resultDurationText.value, resultBudgetText.value, resultPaceText.value].filter(Boolean).join('｜'),
)
const resultHeroTags = computed(() => {
  const summary = tripPlannerSummary.value
  const tags: string[] = []
  const weatherHasRain = travelWeatherInfo.value.some((item) => String(item.day_weather || '').includes('雨') || String(item.night_weather || '').includes('雨'))
  const freeText = String(summary?.free_text_input || '')

  if (summary?.companions?.includes('family')) tags.push('亲子友好')
  if (summary?.mobility_needs?.some((item) => ['less_walking', 'wheelchair', 'rest_friendly'].includes(item))) tags.push('少步行')
  if (freeText.includes('雨') || freeText.includes('下雨') || weatherHasRain) tags.push('雨天可调整')
  if (String(summary?.transportation || '').toLowerCase().includes('public transit')) tags.push('地铁优先')

  if (!tags.length) {
    tags.push('灵活安排行程', '重点景点优先', '路线更顺路', '预算更清晰')
  }

  return tags.slice(0, 4)
})

watch(
  tripPlan,
  () => {
    scheduleDecisionScoreRefresh()
  },
  { deep: true },
)
onMounted(async () => {
  const data = sessionStorage.getItem('tripPlan')
  if (data) {
    tripPlan.value = JSON.parse(data)
    decisionScore.value = tripPlan.value?.decision_score || null
  }
  const summary = sessionStorage.getItem('tripPlannerSummary')
  if (summary) {
    tripPlannerSummary.value = JSON.parse(summary)
  }
  if (!tripPlan.value) {
    const postId = String(route.query.postId || '')
    const trackId = String(route.query.trackId || '')
    try {
      const response = postId ? await getCommunityPostPlan(postId) : trackId ? await getTravelTrackPlan(trackId) : null
      if (response?.success && response.data) {
        tripPlan.value = response.data
        decisionScore.value = response.data.decision_score || null
        sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      }
    } catch (error: any) {
      message.error(error.message || '加载旅行规划失败')
    }
  }
  if (tripPlan.value && !decisionScore.value) {
    await refreshDecisionScore({ silent: true })
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

const isMapImageUrl = (url?: string | null) => {
  const text = String(url || '').trim().toLowerCase()
  if (!text) return false
  return (
    text.startsWith('map:') ||
    text.includes('/v3/staticmap') ||
    text.includes('restapi.amap.com/v3/staticmap') ||
    text.includes('webapi.amap.com/maps/staticmap')
  )
}

const resolveAttractionImage = (item: Attraction) => {
  const candidates = [item.image_url, ...(item.photos || [])]
    .map((url) => String(url || '').trim())
    .filter((url) => Boolean(url) && !isMapImageUrl(url))
  return candidates[0] || buildPlaceholderImage(item.name)
}

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

const buildHotelLocationRoute = (day: DayPlan): DayRouteInfo | null => {
  if (!day.hotel) return null
  const city = tripPlan.value?.city || ''
  const location = getSafeRouteLocation(day.hotel.location, city)
  if (!location) return null
  const marker: DayRouteMarker = {
    label: 'H',
    title: day.hotel.name || '酒店',
    kind: 'hotel',
    address: day.hotel.address || '',
    location,
    image_url: null,
  }
  return {
    route_type: 'walking',
    summary: `酒店位置：${marker.title}`,
    distance: 0,
    duration: 0,
    markers: [marker],
    segments: [],
    fallback_static_map_url: day.hotel.map_image_url || null,
  }
}

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
const toggleEditMode = () => {
  if (!tripPlan.value) return
  editMode.value = true
  originalPlan.value = clonePlan(tripPlan.value)
}

const saveChanges = async () => {
  if (!tripPlan.value) return
  if (scoreRefreshTimer) {
    clearTimeout(scoreRefreshTimer)
    scoreRefreshTimer = null
  }
  if (displayBudget.value) {
    tripPlan.value.budget = displayBudget.value
  }
  await refreshDecisionScore({ silent: true })
  if (decisionScore.value) {
    tripPlan.value.decision_score = decisionScore.value
  }
  editMode.value = false
  sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan.value))
  resetDayRoute()
  refreshActiveDayRoutes()
  message.success('已保存修改')
}

const cancelEdit = () => {
  if (!originalPlan.value) return
  if (scoreRefreshTimer) {
    clearTimeout(scoreRefreshTimer)
    scoreRefreshTimer = null
  }
  tripPlan.value = clonePlan(originalPlan.value)
  decisionScore.value = tripPlan.value.decision_score || null
  scoreError.value = ''
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

const sanitizeFileName = (value: string) =>
  String(value || 'trip-plan')
    .trim()
    .replace(/[\\/:*?"<>|]/g, '-')
    .replace(/\s+/g, '-')

const escapeHtml = (value?: string | number | null) =>
  String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

const exportTripPlan = async () => {
  if (!tripPlan.value || exportingPdf.value) return

  exportingPdf.value = true
  try {
    const plan = tripPlan.value
    const budget = displayBudget.value
    const tagHtml = resultHeroTags.value.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join('')

    const budgetHtml = budget
      ? `
        <section class="section">
          <h2>预算汇总</h2>
          <div class="grid grid-5">
            <div class="stat"><span>景点</span><strong>${escapeHtml(currency(budget.total_attractions))}</strong></div>
            <div class="stat"><span>酒店</span><strong>${escapeHtml(currency(budget.total_hotels))}</strong></div>
            <div class="stat"><span>餐饮</span><strong>${escapeHtml(currency(budget.total_meals))}</strong></div>
            <div class="stat"><span>交通</span><strong>${escapeHtml(currency(budget.total_transportation))}</strong></div>
            <div class="stat"><span>总计</span><strong>${escapeHtml(currency(budget.total))}</strong></div>
          </div>
        </section>
      `
      : ''

    const daysHtml = plan.days
      .map((day) => {
        const hotelHtml = day.hotel
          ? `
            <div class="subsection">
              <h4>酒店推荐</h4>
              <div class="list-card">
                <strong>${escapeHtml(day.hotel.name || '暂无')}</strong>
                <p>地址：${escapeHtml(day.hotel.address || '暂无')}</p>
                <p>类型：${escapeHtml(hotelTypeLabel(day.hotel.type))}</p>
                <p>价格区间：${escapeHtml(priceRangeLabel(day.hotel.price_range))}</p>
                <p>参考价格：${escapeHtml(currency(day.hotel.estimated_cost))}/晚</p>
              </div>
            </div>
          `
          : ''

        const attractionsHtml = day.attractions.length
          ? `
            <div class="subsection">
              <h4>景点安排</h4>
              ${day.attractions
                .map(
                  (item, index) => `
                    <div class="list-card">
                      <strong>${index + 1}. ${escapeHtml(item.name)}</strong>
                      <p>地址：${escapeHtml(item.address || '暂无')}</p>
                      <p>建议停留：${escapeHtml(item.visit_duration)} 分钟</p>
                      <p>门票参考：${escapeHtml(currency(item.ticket_price))}</p>
                      <p>描述：${escapeHtml(item.description || '暂无说明')}</p>
                    </div>
                  `,
                )
                .join('')}
            </div>
          `
          : ''

        const mealsHtml = day.meals.length
          ? `
            <div class="subsection">
              <h4>餐厅推荐</h4>
              ${day.meals
                .map(
                  (item) => `
                    <div class="list-card">
                      <strong>${escapeHtml(mealLabel(item.type))} · ${escapeHtml(item.name)}</strong>
                      <p>人均预算：${escapeHtml(currency(item.estimated_cost))}</p>
                      <p>推荐理由：${escapeHtml(item.description || '暂无说明')}</p>
                    </div>
                  `,
                )
                .join('')}
            </div>
          `
          : ''

        return `
          <section class="section">
            <h2>第 ${escapeHtml(day.day_index + 1)} 天 · ${escapeHtml(day.date)}</h2>
            <div class="summary">
              <p>当日概览：${escapeHtml(day.description || '暂无')}</p>
              <p>交通方式：${escapeHtml(transportationLabel(day.transportation))}</p>
              <p>交通费用：${escapeHtml(currency(day.transportation_cost))}</p>
              <p>住宿安排：${escapeHtml(accommodationLabel(day.accommodation))}</p>
              <p>路线摘要：${escapeHtml(day.route_summary || '暂无路线摘要')}</p>
            </div>
            ${hotelHtml}
            ${attractionsHtml}
            ${mealsHtml}
          </section>
        `
      })
      .join('')

    const weatherHtml = travelWeatherInfo.value.length
      ? `
        <section class="section">
          <h2>天气信息</h2>
          ${travelWeatherInfo.value
            .map(
              (item) => `
                <div class="list-card">
                  <strong>${escapeHtml(item.date)}</strong>
                  <p>白天：${escapeHtml(item.day_weather)} ${escapeHtml(item.day_temp)}°C</p>
                  <p>夜间：${escapeHtml(item.night_weather)} ${escapeHtml(item.night_temp)}°C</p>
                  <p>风向风力：${escapeHtml(item.wind_direction)}风 ${escapeHtml(item.wind_power)}</p>
                </div>
              `,
            )
            .join('')}
        </section>
      `
      : ''

    const container = document.createElement('div')
    container.style.position = 'fixed'
    container.style.left = '-100000px'
    container.style.top = '0'
    container.style.width = '900px'
    container.style.background = '#ffffff'
    container.innerHTML = `
      <div style="font-family:'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif;color:#17324f;padding:32px;background:#ffffff;">
        <style>
          .hero { padding: 24px 28px; border-radius: 24px; background: linear-gradient(135deg, #eef6ff, #dfeeff); border: 1px solid #d3e6fb; }
          .hero h1 { margin: 0; font-size: 40px; line-height: 1.2; color: #17324f; }
          .hero .meta { margin: 12px 0 0; color: #5f7893; font-size: 18px; font-weight: 600; }
          .tags { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
          .tag { padding: 9px 14px; border-radius: 999px; background: #ffffff; border: 1px solid #cfe1f5; color: #2a74c8; font-size: 14px; font-weight: 800; }
          .section { margin-top: 24px; }
          .section h2 { margin: 0 0 14px; font-size: 24px; color: #17324f; }
          .subsection { margin-top: 14px; }
          .subsection h4 { margin: 0 0 10px; font-size: 18px; color: #17324f; }
          .grid { display: grid; gap: 12px; }
          .grid-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
          .stat, .summary, .list-card { padding: 14px 16px; border-radius: 18px; background: #f8fbff; border: 1px solid #dceaf8; }
          .stat span { display: block; color: #64819d; font-size: 14px; font-weight: 700; }
          .stat strong { display: block; margin-top: 6px; font-size: 20px; color: #17324f; }
          .summary p, .list-card p { margin: 6px 0 0; color: #4f6781; font-size: 15px; line-height: 1.65; }
          .list-card { margin-top: 10px; }
          .list-card strong { display: block; color: #17324f; font-size: 17px; line-height: 1.45; }
        </style>
        <section class="hero">
          <h1>${escapeHtml(plan.city)}</h1>
          <p class="meta">${escapeHtml(resultMetaLine.value)}</p>
          <div class="tags">${tagHtml}</div>
        </section>
        ${budgetHtml}
        ${daysHtml}
        ${weatherHtml}
      </div>
    `

    document.body.appendChild(container)
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))

    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
    })

    document.body.removeChild(container)

    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const margin = 8
    const renderWidth = pageWidth - margin * 2
    const renderHeight = (canvas.height * renderWidth) / canvas.width
    const imageData = canvas.toDataURL('image/png')

    let heightLeft = renderHeight
    let position = margin
    pdf.addImage(imageData, 'PNG', margin, position, renderWidth, renderHeight, undefined, 'FAST')
    heightLeft -= pageHeight - margin * 2

    while (heightLeft > 0) {
      pdf.addPage()
      position = margin - (renderHeight - heightLeft)
      pdf.addImage(imageData, 'PNG', margin, position, renderWidth, renderHeight, undefined, 'FAST')
      heightLeft -= pageHeight - margin * 2
    }

    pdf.save(`${sanitizeFileName(plan.city)}-${plan.start_date}-旅行规划.pdf`)
    message.success('已导出 PDF')
  } catch (error) {
    console.error(error)
    message.error('导出 PDF 失败')
  } finally {
    exportingPdf.value = false
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

const skillFieldLabel = (field?: string) => {
  const mapping: Record<string, string> = {
    tags: '兴趣标签',
    keywords: '关键词',
    budget_level: '预算等级',
    transportation: '交通方式',
    companions: '同行人群',
    dietary: '饮食限制',
    mobility: '行动需求',
    date: '出行日期',
    weather: '天气条件',
  }
  return mapping[String(field || '').trim().toLowerCase()] || String(field || '')
}

const formatMatchedFields = (fields?: string[]) => (fields || []).map((item) => skillFieldLabel(item))

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

.result-nav-button--accent {
  background: linear-gradient(135deg, rgba(236, 245, 255, 0.92), rgba(255, 255, 255, 0.94));
  border-color: rgba(160, 195, 235, 0.56);
  box-shadow: 0 12px 22px rgba(118, 164, 217, 0.16);
}

.result-nav-button--day {
  font-size: 16px;
  color: #35526d;
}

#result-hero,
#result-score,
#result-budget,
#result-days,
#result-weather,
#result-reasons,
#result-skills {
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

.result-meta-line {
  margin: 0;
  color: #5f7893;
  font-size: 20px;
  line-height: 1.7;
  font-weight: 600;
}

.result-hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}

.result-hero-tag {
  display: inline-flex;
  align-items: center;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(187, 214, 243, 0.82);
  color: #2a74c8;
  font-size: 16px;
  font-weight: 800;
  box-shadow: 0 8px 18px rgba(99, 144, 199, 0.08);
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

.recommendation-simple {
  display: grid;
  gap: 14px;
}

.recommendation-strip {
  display: grid;
  gap: 10px;
  padding: 18px 20px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(252, 254, 255, 0.92), rgba(236, 245, 255, 0.88));
  border: 1px solid rgba(188, 213, 243, 0.76);
}

.recommendation-strip--memory {
  background: linear-gradient(135deg, rgba(248, 252, 255, 0.94), rgba(232, 242, 255, 0.9));
}

.recommendation-strip__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.recommendation-strip__top strong {
  display: block;
  color: #17324f;
  font-size: 20px;
  line-height: 1.35;
}

.recommendation-strip__label {
  display: inline-flex;
  margin-bottom: 6px;
  color: #5f7f9e;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.recommendation-strip__score {
  flex-shrink: 0;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  color: #2a74c8;
  font-size: 15px;
  font-weight: 800;
}

.memory-inline-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.memory-inline-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(201, 220, 242, 0.72);
}

.memory-inline-item span {
  color: #637d99;
  font-size: 15px;
  font-weight: 700;
}

.memory-inline-item strong {
  color: #245184;
  font-size: 18px;
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

.score-overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.result-panel--decision {
  position: relative;
  background:
    radial-gradient(circle at top right, rgba(255, 193, 108, 0.16), transparent 28%),
    radial-gradient(circle at 12% 18%, rgba(148, 215, 255, 0.18), transparent 20%),
    rgba(248, 251, 255, 0.8);
}

.score-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.9fr);
  gap: 18px;
  margin-bottom: 18px;
}

.score-hero__meta {
  padding: 20px 22px;
  border-radius: 24px;
  background: linear-gradient(145deg, rgba(31, 91, 150, 0.96), rgba(59, 123, 189, 0.9));
  color: #f8fbff;
  box-shadow: 0 18px 30px rgba(83, 132, 194, 0.22);
}

.score-hero__eyebrow,
.score-card__eyebrow {
  display: inline-flex;
  margin-bottom: 8px;
  color: rgba(245, 249, 255, 0.76);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.score-card__eyebrow {
  color: #7291b2;
}

.score-hero__meta strong {
  display: block;
  font-size: 28px;
  line-height: 1.25;
}

.score-hero__meta p {
  margin: 10px 0 0;
  color: rgba(238, 246, 255, 0.8);
  line-height: 1.75;
}

.score-overview-card,
.score-card {
  padding: 18px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(206, 224, 245, 0.82);
  box-shadow: 0 12px 24px rgba(111, 151, 204, 0.08);
}

.score-overview-card--primary {
  background: linear-gradient(135deg, rgba(234, 244, 255, 0.96), rgba(255, 255, 255, 0.96));
}

.score-overview-card--mood {
  background: linear-gradient(135deg, rgba(255, 245, 226, 0.96), rgba(255, 255, 255, 0.96));
}

.score-overview-card__label {
  display: inline-flex;
  margin-bottom: 8px;
  color: #5f7f9e;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.score-overview-card strong {
  display: block;
  color: #17324f;
  font-size: 40px;
  line-height: 1.1;
}

.score-overview-card strong.score-delta--up,
.score-overview-card strong.score-delta--down,
.score-overview-card strong.score-delta--flat {
  padding: 0;
  background: transparent;
}

.score-overview-card p,
.score-card__head p,
.score-card__detail {
  margin: 8px 0 0;
  color: #6a819a;
  line-height: 1.7;
}

.score-badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.score-badge {
  display: inline-flex;
  align-items: center;
  padding: 9px 14px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 800;
}

.score-badge--good {
  background: rgba(66, 184, 131, 0.14);
  color: #1d7b55;
}

.score-badge--risk {
  background: rgba(255, 173, 96, 0.16);
  color: #9b5f19;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.score-card {
  display: grid;
  gap: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.84), rgba(242, 248, 255, 0.9));
}

.score-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.score-card__head strong {
  color: #17324f;
  font-size: 20px;
  line-height: 1.3;
}

.score-card__scorebox {
  display: grid;
  justify-items: end;
  gap: 8px;
  flex-shrink: 0;
}

.score-card__score {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  min-height: 64px;
  padding: 10px 14px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(45, 134, 231, 0.14), rgba(255, 255, 255, 0.92));
  color: #2a74c8;
  font-size: 28px;
  font-weight: 900;
  box-shadow: inset 0 0 0 1px rgba(172, 206, 242, 0.3);
}

.score-card__status {
  flex-shrink: 0;
  min-width: 84px;
  padding: 6px 10px;
  border-radius: 999px;
  text-align: center;
  font-size: 13px;
  font-weight: 800;
}

.score-status--good {
  background: rgba(66, 184, 131, 0.14);
  color: #1d7b55;
}

.score-status--mid {
  background: rgba(170, 198, 228, 0.18);
  color: #597da4;
}

.score-status--warn {
  background: rgba(255, 173, 96, 0.16);
  color: #9b5f19;
}

.score-card__meter {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-card__meter span {
  color: #597590;
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
}

.score-card__meter-track {
  position: relative;
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: rgba(219, 231, 245, 0.84);
  overflow: hidden;
}

.score-card__meter-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: linear-gradient(90deg, #2d86e7, #69aef3);
}

.score-card__narrative {
  margin: -4px 0 0;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(238, 245, 255, 0.88);
  color: #35526d;
  line-height: 1.75;
}

.score-card__toggle {
  width: 100%;
  border: 0;
  border-radius: 16px;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(32, 113, 207, 0.1), rgba(98, 167, 239, 0.12));
  color: #2469b8;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.score-card__toggle:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(84, 132, 190, 0.12);
}

.score-card__recipe {
  display: grid;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(247, 250, 255, 0.96);
  border: 1px solid rgba(206, 224, 245, 0.9);
}

.score-card__recipe-title {
  color: #35526d;
  font-size: 14px;
  font-weight: 800;
}

.score-factor-list {
  display: grid;
  gap: 10px;
}

.score-factor {
  padding: 12px 14px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid rgba(222, 233, 246, 0.9);
}

.score-factor__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.score-factor__head strong {
  color: #183654;
  font-size: 15px;
}

.score-factor p {
  margin: 8px 0 0;
  color: #66809a;
  line-height: 1.7;
}

.score-factor__impact {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 58px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 800;
}

.score-factor__impact--positive {
  background: rgba(66, 184, 131, 0.14);
  color: #1d7b55;
}

.score-factor__impact--negative {
  background: rgba(255, 173, 96, 0.16);
  color: #9b5f19;
}

.score-factor__impact--neutral {
  background: rgba(170, 198, 228, 0.18);
  color: #597da4;
}

.score-factor__value {
  display: inline-flex;
  margin-top: 8px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(236, 243, 251, 0.96);
  color: #507095;
  font-size: 12px;
  font-weight: 700;
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

.hotel-compact__map {
  width: 100%;
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

.hotel-compact__title {
  color: #17324f;
  font-size: 22px;
  font-weight: 800;
}

:deep(.hotel-location-map .day-route-map__stage),
:deep(.hotel-location-map .day-route-map__canvas),
:deep(.hotel-location-map .day-route-map__placeholder) {
  min-height: 260px;
  border-radius: 16px;
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
  position: relative;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.88), rgba(241, 247, 255, 0.94));
  border: 1px solid rgba(191, 214, 240, 0.82);
  box-shadow:
    0 12px 24px rgba(110, 153, 208, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.skill-card__head {
  align-items: center;
  flex-wrap: nowrap;
}

.skill-card__title {
  flex: 0 1 auto;
  min-width: 0;
  white-space: nowrap;
  line-height: 1.35;
}

.skill-card__tags {
  flex: 0 0 auto;
  flex-wrap: nowrap;
  gap: 6px;
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

  .score-overview {
    grid-template-columns: 1fr;
  }

  .score-hero {
    grid-template-columns: 1fr;
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

  :deep(.hotel-location-map .day-route-map__stage),
  :deep(.hotel-location-map .day-route-map__canvas),
  :deep(.hotel-location-map .day-route-map__placeholder) {
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

  .memory-inline-list {
    grid-template-columns: 1fr;
  }

  .weather-card__date {
    font-size: 24px;
  }
}
</style>
