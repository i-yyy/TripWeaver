<template>
  <div class="brand-page planner-page">
    <div class="brand-shell split-layout">
      <section class="glass-panel planner-main-panel">
        <div class="planner-hero">
          <div class="section-heading planner-heading">
            <span class="page-kicker">🧭 旅行规划</span>
            <h1 class="page-title planner-title">
              <span class="planner-title__lead">开始编织</span>
              <span class="planner-title__focus">一趟独属于你的旅行</span>
            </h1>
            <p class="page-subtitle">把想去的城市、想看的风景和想停留的节奏交给我们，系统会替你把旅途慢慢织成一张有画面的路线图</p>
          </div>
        </div>

        <div v-if="loading" class="planner-progress planner-progress--floating">
          <div class="planner-progress__content">
            <span class="planner-progress__label">智能进度</span>
            <strong>{{ loadingStatus }}</strong>
          </div>
          <span class="planner-progress__badge">进行中</span>
        </div>

        <a-form class="brand-form-grid" layout="vertical" @submit.prevent="handleSubmit">
          <section class="planner-form-section planner-form-section--primary">
            <div class="planner-section-head planner-section-head--primary">
              <div>
                <h3>核心信息</h3>
                <p>先把城市、日期和基础预算定下来，系统就能先搭好主骨架</p>
              </div>
            </div>

            <div class="planner-core-panel" :style="{ '--planner-card-photo': `url(${plannerCardPhoto})` }">
              <div class="planner-core-panel__summary">
                <article class="planner-core-panel__note">
                  <span>主线起笔</span>
                  <strong>{{ formData.city.trim() || '先写下想去的城市' }}</strong>
                  <p>把日期定下来，节奏和天气判断会更稳。</p>
                </article>
                <article class="planner-core-panel__note">
                  <span>行程骨架</span>
                  <strong>{{ formData.travel_days }} 天 · {{ formData.budget_level ? budgetOptions.find((item) => item.value === formData.budget_level)?.label : '预算待定' }}</strong>
                  <p>短途行程建议抓主线，把节奏做得更轻快。</p>
                </article>
              </div>

              <div class="planner-core-panel__fields">
                <a-row :gutter="16">
                  <a-col :xs="24" :md="8">
                    <a-form-item label="📍 目的地城市" required>
                      <a-input v-model:value="formData.city" placeholder="例如：北京、上海、杭州" />
                    </a-form-item>
                  </a-col>
                  <a-col :xs="24" :md="8">
                    <a-form-item label="📅 开始日期" required>
                      <a-date-picker v-model:value="formData.start_date" style="width: 100%" />
                    </a-form-item>
                  </a-col>
                  <a-col :xs="24" :md="8">
                    <a-form-item label="🗓️ 结束日期" required>
                      <a-date-picker v-model:value="formData.end_date" style="width: 100%" />
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-row :gutter="16">
                  <a-col :xs="24" :md="6">
                    <a-form-item label="⏳ 旅行天数">
                      <a-input-number :value="formData.travel_days" :min="1" :max="30" disabled />
                    </a-form-item>
                  </a-col>
                  <a-col :xs="24" :md="6">
                    <a-form-item label="🚇 交通方式">
                      <a-select v-model:value="formData.transportation">
                        <a-select-option v-for="item in transportOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                  <a-col :xs="24" :md="6">
                    <a-form-item label="🛏️ 住宿偏好">
                      <a-select v-model:value="formData.accommodation">
                        <a-select-option v-for="item in accommodationOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                  <a-col :xs="24" :md="6">
                    <a-form-item label="💰 预算等级">
                      <a-select v-model:value="formData.budget_level" allow-clear placeholder="请选择预算等级">
                        <a-select-option v-for="item in budgetOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>
              </div>
            </div>
          </section>

          <section class="planner-form-section">
            <div class="planner-section-head planner-section-head--preference">
              <div>
                <h3>偏好设置</h3>
                <p>这些信息会影响推荐方向，让行程更贴近你的出行节奏</p>
              </div>
            </div>

            <div
              class="planner-preference-panel"
              :style="{ '--planner-card-photo': `url(${plannerCardPhoto})` }"
            >
              <div class="planner-preference-panel__layout">
                <div class="planner-preference-panel__content">
                  <a-form-item label=" 兴趣偏好" class="planner-preference-panel__interest">
                    <a-checkbox-group v-model:value="formData.preferences">
                      <a-checkbox v-for="item in preferenceOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
                    </a-checkbox-group>
                  </a-form-item>

                  <a-form-item label=" 旅行风格">
                    <a-checkbox-group v-model:value="formData.travel_style">
                      <a-checkbox v-for="item in travelStyleOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
                    </a-checkbox-group>
                  </a-form-item>

                  <a-form-item label=" 同行人群">
                    <a-checkbox-group v-model:value="formData.companions">
                      <a-checkbox v-for="item in companionOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
                    </a-checkbox-group>
                  </a-form-item>

                  <a-form-item label=" 行动需求">
                    <a-checkbox-group v-model:value="formData.mobility_needs">
                      <a-checkbox v-for="item in mobilityOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
                    </a-checkbox-group>
                  </a-form-item>
                </div>

                <div class="planner-preference-panel__art" aria-hidden="true"></div>
              </div>
            </div>
          </section>

          <section class="planner-form-section planner-form-section--compact">
            <div class="planner-section-head planner-section-head--note">
              <div>
                <h3>补充说明</h3>
                <p>如果你有节奏、天气或路线上的特别要求，可以在这里补充</p>
              </div>
            </div>

            <a-form-item label="📝 补充要求">
                <a-textarea
                  v-model:value="formData.free_text_input"
                  :rows="4"
                  placeholder="例如：希望雨天也有备选方案，不要安排得太赶，想多一点城市漫游"
                />
            </a-form-item>

            <a-form-item class="planner-submit">
              <a-button type="primary" block size="large" :loading="loading" @click="handleSubmit">
                {{ loading ? loadingStatus : '✨ 生成我的行程' }}
              </a-button>
            </a-form-item>
          </section>
        </a-form>
      </section>

      <aside class="aside-stack">
        <section class="glass-panel glass-panel--soft planner-side-panel planner-side-panel--tips">
          <div class="section-heading">
            <h3>💡 今日建议卡</h3>
            <p>根据你当前填写的内容，给出几条轻量提醒</p>
          </div>
          <div class="planner-tip-grid">
            <article v-for="card in smartSuggestionCards" :key="card.title" class="planner-tip-card">
              <span class="planner-tip-card__tag">{{ card.tag }}</span>
              <strong>{{ card.title }}</strong>
              <p>{{ card.text }}</p>
            </article>
          </div>
        </section>

        <section class="glass-panel glass-panel--soft planner-side-panel planner-side-panel--checklist">
          <div class="section-heading">
            <h3>🧾 出发检查卡</h3>
            <p>开始规划前，快速看一眼还有哪些信息值得补充</p>
          </div>
          <div class="planner-check-summary">
            <strong>已完成 {{ completedChecklistCount }}/{{ plannerChecklist.length }}</strong>
            <span>{{ checklistSummary }}</span>
          </div>
          <div class="planner-checklist">
            <article
              v-for="item in plannerChecklist"
              :key="item.title"
              class="planner-check-item"
              :class="{ 'planner-check-item--done': item.done }"
            >
              <span class="planner-check-item__icon">{{ item.done ? '✓' : '○' }}</span>
              <div class="planner-check-item__content">
                <strong>{{ item.title }}</strong>
                <p>{{ item.text }}</p>
              </div>
            </article>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'

import { generateTripPlan } from '@/services/api'
import plannerCardPhoto from '@/assets/planner-card-bg.png'
import type { TripFormData } from '@/types'
import { useAuthState } from '@/utils/auth'

const router = useRouter()
const authState = useAuthState()
const loading = ref(false)
const loadingStatus = ref('等待开始')
const transportOptions = [
  { value: 'Public Transit', label: '公共交通' },
  { value: 'Drive', label: '自驾' },
  { value: 'Walk', label: '步行' },
]

const accommodationOptions = [
  { value: 'Budget Hotel', label: '经济酒店' },
  { value: 'Comfort Hotel', label: '舒适酒店' },
  { value: 'Luxury Hotel', label: '高端酒店' },
  { value: 'Homestay', label: '民宿' },
]

const budgetOptions = [
  { value: 'low', label: '低预算' },
  { value: 'medium', label: '中预算' },
  { value: 'high', label: '高预算' },
]

const preferenceOptions = [
  { value: 'history', label: '🏛️历史文化' },
  { value: 'nature', label: '🌿 自然风光' },
  { value: 'food', label: '🍜 美食' },
  { value: 'shopping', label: '🛍️ 购物' },
  { value: 'museum', label: '🖼️ 博物馆' },
]

const travelStyleOptions = [
  { value: 'slow', label: '🐢 慢节奏' },
  { value: 'citywalk', label: '🚶 城市漫游' },
  { value: 'checkin', label: '📸 经典打卡' },
  { value: 'local', label: '🏠 本地体验' },
]

const companionOptions = [
  { value: 'solo', label: '🧍 独行' },
  { value: 'couple', label: '💑 情侣' },
  { value: 'family', label: '👨‍👩‍👧‍👦 家庭' },
  { value: 'friends', label: '🫶 朋友' },
]

const mobilityOptions = [
  { value: 'less_walking', label: '🚶 尽量少走路' },
  { value: 'wheelchair', label: '♿ 无障碍优先' },
  { value: 'rest_friendly', label: '☕ 安排休息点' },
]

const preferenceLabelMap = Object.fromEntries(preferenceOptions.map((item) => [item.value, item.label.replace(/^[^\u4e00-\u9fa5A-Za-z]+/, '').trim()]))
const createSessionId = () => {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID()
  }
  return `session_${Date.now()}_${Math.random().toString(16).slice(2)}`
}

type LocalTripFormData = Omit<TripFormData, 'start_date' | 'end_date' | 'dietary_restrictions'> & {
  start_date: Dayjs | null
  end_date: Dayjs | null
}

const formData = reactive<LocalTripFormData>({
  user_id: authState.user?.id || '',
  session_id: createSessionId(),
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: 'Public Transit',
  accommodation: 'Budget Hotel',
  preferences: [],
  free_text_input: '',
  budget_level: null,
  travel_style: [],
  companions: [],
  mobility_needs: [],
})

onMounted(() => {
  const rawSeed = sessionStorage.getItem('communityPlannerSeed')
  if (!rawSeed) return

  try {
    const seed = JSON.parse(rawSeed) as {
      city?: string
      estimated_budget?: string
      tags?: string[]
      travel_style?: string[]
      companions?: string[]
      summary?: string
      title?: string
    }
    formData.city = seed.city || formData.city
    formData.budget_level = seed.estimated_budget || formData.budget_level
    formData.travel_style = Array.isArray(seed.travel_style) ? seed.travel_style : formData.travel_style
    formData.companions = Array.isArray(seed.companions) ? seed.companions : formData.companions
    formData.preferences = Array.isArray(seed.tags)
      ? seed.tags.filter((tag) => ['history', 'nature', 'food', 'shopping', 'museum'].includes(tag))
      : formData.preferences
    formData.free_text_input = seed.title
      ? `参考社区路线「${seed.title}」：${seed.summary || ''}`
      : formData.free_text_input
    sessionStorage.removeItem('communityPlannerSeed')
    message.success('已带入社区路线灵感，可以继续补充日期和偏好')
  } catch {
    sessionStorage.removeItem('communityPlannerSeed')
  }
})

const smartSuggestionCards = computed(() => {
  const city = formData.city.trim()
  const pickedPreference = formData.preferences[0]
  const preferenceLabel = pickedPreference ? preferenceLabelMap[pickedPreference] || '兴趣方向' : ''
  return [
    city
      ? {
          tag: '目的地',
          title: `${city} 适合先锁定 1-2 个核心片区`,
          text: '先定重点区域，再排景点和住宿，路线会更顺。',
        }
      : {
          tag: '起点',
          title: '先确定城市，建议会更快聚焦',
          text: '补上目的地后，系统能更准确地判断片区分布、交通方式和住宿落点。',
        },
    formData.travel_days >= 4
      ? {
          tag: '节奏',
          title: `这次有 ${formData.travel_days} 天，适合留白一点`,
          text: '可以把每天的点位放松一些，留出散步、吃饭和临时起意的小停留。',
        }
      : {
          tag: '节奏',
          title: '短途行程更适合抓主线玩法',
          text: '优先保留最想看的几处核心点，整体路线会更轻快，也更不容易赶。',
        },
    pickedPreference
      ? {
          tag: '偏好',
          title: `这次可以重点围绕“${preferenceLabel}”展开`,
          text: '系统会把相关景点和体验优先往前排，让整趟行程的风格更统一。',
        }
      : {
          tag: '偏好',
          title: '补一点偏好，推荐会更贴近你',
          text: '哪怕只选一个兴趣方向，推荐结果也会比默认方案更有个人节奏。',
        },
    
  ]
})

const plannerChecklist = computed(() => {
  const hasCity = Boolean(formData.city.trim())
  const hasDate = Boolean(formData.start_date && formData.end_date)
  const hasPreference = Boolean(formData.preferences.length || formData.travel_style.length)
  const hasBudgetOrNote = Boolean(formData.budget_level || formData.free_text_input.trim())

  return [
    {
      title: '目的地已明确',
      text: hasCity ? `当前目的地：${formData.city.trim()}` : '先填一个城市，系统才能开始聚焦推荐。',
      done: hasCity,
    },
    {
      title: '日期范围已确认',
      text: hasDate ? `当前行程 ${formData.travel_days} 天，可进入路线规划。` : '出行日期会直接影响天气和行程密度。',
      done: hasDate,
    },
    {
      title: '偏好方向已补充',
      text: hasPreference ? '兴趣或旅行风格已填写，推荐会更贴近你。' : '补一点偏好，推荐结果会更有个性。',
      done: hasPreference,
    },
    {
      title: '预算或补充要求已填写',
      text: hasBudgetOrNote ? '系统可以据此收紧价格和节奏范围。' : '如果你有预算或特殊要求，建议顺手补一句。',
      done: hasBudgetOrNote,
    },
  ]
})

const completedChecklistCount = computed(() => plannerChecklist.value.filter((item) => item.done).length)
const checklistSummary = computed(() => {
  if (completedChecklistCount.value === plannerChecklist.value.length) {
    return '信息已经很完整，可以直接开始规划。'
  }
  if (completedChecklistCount.value >= 2) {
    return '核心信息已经有了，再补一点细节会更好。'
  }
  return '先把基础信息补齐，后面的推荐会更稳定。'
})

watch([() => formData.start_date, () => formData.end_date], ([start, end]) => {
  if (!start || !end) return
  const days = end.diff(start, 'day') + 1
  if (days <= 0) {
    message.warning('结束日期必须晚于或等于开始日期')
    formData.end_date = null
    return
  }
  if (days > 30) {
    message.warning('行程天数不能超过 30 天')
    formData.end_date = null
    return
  }
  formData.travel_days = days
})

const handleSubmit = async () => {
  if (!authState.user) {
    message.error('登录状态已失效，请重新登录')
    router.push('/login')
    return
  }
  if (!formData.city.trim()) {
    message.error('请输入目的地城市')
    return
  }
  if (!formData.start_date || !formData.end_date) {
    message.error('请选择出行日期')
    return
  }

  formData.user_id = authState.user.id
  formData.session_id = createSessionId()
  loadingStatus.value = '正在提交规划请求'
  loading.value = true

  try {
    loadingStatus.value = '正在等待规划结果'
    const payload: TripFormData = {
      user_id: formData.user_id,
      session_id: formData.session_id,
      city: formData.city.trim(),
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: formData.end_date.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input,
      budget_level: formData.budget_level,
      travel_style: formData.travel_style.length ? formData.travel_style : [...formData.preferences],
      companions: formData.companions,
      dietary_restrictions: [],
      mobility_needs: formData.mobility_needs,
    }

    const response = await generateTripPlan(payload)
    if (!response.success || !response.data) {
      throw new Error(response.message || '行程生成失败')
    }

    loadingStatus.value = '正在保存结果'
    sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
    sessionStorage.setItem(
      'tripPlannerSummary',
      JSON.stringify({
        budget_level: payload.budget_level || null,
        travel_style: payload.travel_style,
        companions: payload.companions,
        mobility_needs: payload.mobility_needs,
        transportation: payload.transportation,
        free_text_input: payload.free_text_input,
      }),
    )
    sessionStorage.setItem('tripPlannerUserId', authState.user.id)
    sessionStorage.setItem('tripPlannerSessionId', formData.session_id)
    loadingStatus.value = '即将跳转到行程页'
    message.success('行程生成成功')
    router.push('/result')
  } catch (error: any) {
    loadingStatus.value = '规划失败'
    message.error(error.message || '行程生成失败')
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.planner-main-panel,
.planner-side-panel {
  padding: 28px;
}

.planner-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  margin-bottom: 22px;
}

.planner-heading {
  margin-bottom: 0;
}

.planner-hero-card {
  position: relative;
  padding: 22px 24px;
  border-radius: 28px;
  min-height: 280px;
  display: flex;
  align-items: flex-end;
  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;
  color: #183654;
  box-shadow: 0 24px 42px rgba(67, 112, 166, 0.22);
  overflow: hidden;
}

.planner-hero-card__overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(to top, rgba(255, 255, 255, 0.96) 0%, rgba(255, 255, 255, 0.88) 20%, rgba(255, 255, 255, 0.62) 42%, rgba(255, 255, 255, 0.2) 72%, rgba(255, 255, 255, 0.06) 100%),
    linear-gradient(180deg, rgba(18, 46, 79, 0.08), rgba(18, 46, 79, 0.18));
}

.planner-hero-card__content {
  position: relative;
  z-index: 1;
  display: grid;
}

.planner-hero-card__layout {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  align-items: start;
  gap: 18px;
  padding-left: 10px;
}

.planner-hero-card__eyebrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  min-height: 158px;
  padding: 12px 8px;
  color: #8f5c2f;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.04em;
  font-family: "STKaiti", "KaiTi", "Kaiti SC", "FZShuTi", serif;
  text-shadow: 0 4px 12px rgba(255, 255, 255, 0.24);
  writing-mode: vertical-rl;
  text-orientation: mixed;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.34);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.38),
    0 12px 24px rgba(112, 144, 184, 0.12);
}

.planner-hero-card strong {
  display: block;
  font-size: 24px;
  line-height: 1.52;
  max-width: 16em;
  font-family: "STKaiti", "KaiTi", "Kaiti SC", "FZShuTi", serif;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-shadow: 0 4px 12px rgba(255, 255, 255, 0.24);
  padding-top: 22px;
  padding-left: 6px;
}

.planner-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 22px;
  padding: 16px 18px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(231, 243, 255, 0.92), rgba(244, 249, 255, 0.94));
  border: 1px solid rgba(181, 211, 243, 0.82);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    0 14px 28px rgba(95, 143, 201, 0.12);
  backdrop-filter: blur(14px);
}

.planner-progress--floating {
  position: sticky;
  top: 84px;
  z-index: 18;
}

.planner-progress__content {
  display: grid;
  gap: 6px;
}

.planner-progress__label {
  color: #5f7f9e;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.planner-progress__content strong {
  color: #17324f;
  font-size: 22px;
  line-height: 1.3;
}

.planner-progress__badge {
  flex-shrink: 0;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.8);
  color: #2d86e7;
  font-size: 15px;
  font-weight: 800;
}

.planner-title {
  font-family: "Microsoft YaHei", "Microsoft YaHei UI", "PingFang SC", "Noto Sans SC", sans-serif;
  font-size: clamp(34px, 4.2vw, 54px);
  line-height: 1.04;
}

.planner-title__lead,
.planner-title__focus {
  display: inline-block;
}

.planner-title__lead {
  margin-right: 0.18em;
  font-family: "Microsoft YaHei", "Microsoft YaHei UI", "PingFang SC", "Noto Sans SC", sans-serif;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #244a73;
  text-shadow: 0 6px 22px rgba(101, 143, 190, 0.12);
}

.planner-title__focus {
  font-family: "Microsoft YaHei", "Microsoft YaHei UI", "PingFang SC", "Noto Sans SC", sans-serif;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.planner-form-section {
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.planner-form-section--primary {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.64), rgba(245, 249, 255, 0.5));
}

.planner-preference-panel {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  margin-top: 18px;
  padding: 22px;
  border-radius: 24px;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.66) 0%, rgba(255, 255, 255, 0.54) 52%, rgba(255, 255, 255, 0.22) 100%),
    var(--planner-card-photo) center center / cover no-repeat;
  border: 1px solid rgba(201, 221, 244, 0.82);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.88),
    0 18px 32px rgba(112, 154, 208, 0.08);
}

.planner-preference-panel__layout {
  position: relative;
  min-height: 100%;
}

.planner-preference-panel__content {
  display: grid;
  padding-right: 12px;
  position: relative;
  z-index: 2;
}

.planner-preference-panel__art {
  position: absolute;
  inset: -22px;
  border-radius: inherit;
  pointer-events: none;
  overflow: hidden;
  z-index: 1;
  background: transparent;
}

.planner-preference-panel__art::before,
.planner-preference-panel__art::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
}

.planner-preference-panel__art::before {
  background: rgba(255, 255, 255, 0.08);
  opacity: 0.36;
  filter: blur(18px);
}

.planner-preference-panel__art::after {
  background:
    linear-gradient(to right, rgba(244, 248, 255, 0.78) 0%, rgba(244, 248, 255, 0.58) 46%, rgba(250, 252, 255, 0.18) 100%),
    linear-gradient(to top, rgba(242, 247, 255, 0.24) 0%, rgba(247, 250, 255, 0.08) 44%, rgba(255, 255, 255, 0) 100%);
}

.planner-preference-panel__interest {
  position: relative;
  z-index: 3;
}

:deep(.planner-preference-panel__interest .ant-checkbox-group) {
  display: grid;
  grid-template-columns: repeat(5, max-content);
  justify-content: start;
  width: calc(100% + 220px);
  max-width: none;
  margin-right: -220px;
  padding-right: 220px;
  gap: 10px 12px;
}

:deep(.planner-preference-panel__interest .ant-checkbox-wrapper) {
  margin-inline-end: 0;
  white-space: nowrap;
}

.planner-preference-panel > * {
  position: relative;
  z-index: 1;
}

.planner-form-section--compact {
  background: rgba(241, 247, 255, 0.5);
}

.planner-core-panel {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  display: grid;
  gap: 18px;
  padding: 18px;
  border-radius: 26px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(240, 247, 255, 0.72));
  border: 1px solid rgba(191, 215, 242, 0.82);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.86),
    0 16px 30px rgba(119, 159, 208, 0.1);
}

.planner-core-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background-image: var(--planner-card-photo);
  background-repeat: no-repeat;
  background-position: center center;
  background-size: cover;
  opacity: 0.84;
  filter: saturate(1.08) brightness(1.02);
  pointer-events: none;
  z-index: 0;
}

.planner-core-panel::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.58) 0%, rgba(255, 255, 255, 0.36) 42%, rgba(255, 255, 255, 0.52) 100%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), rgba(245, 250, 255, 0.36));
  pointer-events: none;
  z-index: 0;
}

.planner-core-panel > * {
  position: relative;
  z-index: 1;
}

.planner-core-panel__summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.planner-core-panel__note {
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(213, 228, 245, 0.92);
  box-shadow: 0 10px 20px rgba(100, 142, 193, 0.08);
}

.planner-core-panel__note span {
  display: inline-flex;
  margin-bottom: 8px;
  color: #6b87a7;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.planner-core-panel__note strong {
  display: block;
  color: #17324f;
  font-size: 22px;
  line-height: 1.35;
}

.planner-core-panel__note p {
  margin: 8px 0 0;
  color: #6b839d;
  line-height: 1.72;
}

.planner-core-panel__fields {
  padding: 4px 2px 0;
}

.planner-core-panel__fields :deep(.ant-input),
.planner-core-panel__fields :deep(.ant-input-number),
.planner-core-panel__fields :deep(.ant-picker),
.planner-core-panel__fields :deep(.ant-select-selector) {
  border: 1px solid rgba(137, 170, 207, 0.72) !important;
  box-shadow: 0 8px 18px rgba(89, 126, 171, 0.08);
}

.planner-core-panel__fields :deep(.ant-input:hover),
.planner-core-panel__fields :deep(.ant-input:focus),
.planner-core-panel__fields :deep(.ant-input-number:hover),
.planner-core-panel__fields :deep(.ant-input-number-focused),
.planner-core-panel__fields :deep(.ant-picker:hover),
.planner-core-panel__fields :deep(.ant-picker-focused),
.planner-core-panel__fields :deep(.ant-select-focused .ant-select-selector),
.planner-core-panel__fields :deep(.ant-select-selector:hover) {
  border-color: rgba(65, 126, 197, 0.92) !important;
  box-shadow: 0 0 0 3px rgba(64, 140, 224, 0.12), 0 10px 20px rgba(89, 126, 171, 0.1);
}

.planner-section-head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(224, 239, 255, 0.86), rgba(241, 248, 255, 0.92));
  border: 1px solid rgba(176, 206, 241, 0.72);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.72),
    0 10px 18px rgba(127, 170, 223, 0.08);
}

.planner-section-head h3 {
  margin: 0 0 6px;
  color: #111111;
  font-size: 22px;
  font-weight: 800;
}

.planner-section-head p {
  margin: 0;
  color: var(--brand-muted);
  line-height: 1.7;
}

.planner-section-mark {
  display: inline-grid;
  place-items: center;
  min-width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
  font-size: 20px;
}

.planner-submit {
  margin-bottom: 0;
}

.planner-side-panel--tips,
.planner-side-panel--checklist {
  display: grid;
  gap: 16px;
}

.aside-stack {
  height: 100%;
  grid-template-rows: minmax(0, 0.94fr) minmax(0, 1.06fr);
}

.planner-side-panel--tips,
.planner-side-panel--checklist {
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 100%;
}

.planner-side-panel--checklist {
  grid-template-rows: auto auto minmax(0, 1fr);
}

.planner-tip-grid,
.planner-checklist {
  display: grid;
  gap: 14px;
}

.planner-tip-grid {
  min-height: 100%;
  grid-template-rows: repeat(3, minmax(0, 1fr));
}

.planner-checklist {
  min-height: 100%;
  grid-template-rows: repeat(4, minmax(0, 1fr));
}

.planner-tip-card,
.planner-check-item {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.56);
  border: 1px solid rgba(255, 255, 255, 0.58);
  box-shadow: 0 14px 28px rgba(84, 128, 184, 0.08);
}

.planner-tip-card {
  display: grid;
  align-content: start;
  gap: 6px;
  padding: 16px 18px;
  min-height: 0;
}

.planner-tip-card__tag {
  display: inline-flex;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(45, 134, 231, 0.12);
  color: #2a74c8;
  font-size: 13px;
  font-weight: 800;
}

.planner-tip-card strong,
.planner-check-summary strong,
.planner-check-item__content strong {
  color: #17324f;
}

.planner-tip-card strong {
  font-size: 17px;
  line-height: 1.35;
}

.planner-tip-card p,
.planner-check-summary span,
.planner-check-item__content p {
  margin: 0;
  color: #6b839d;
  line-height: 1.65;
}

.planner-check-summary {
  display: grid;
  gap: 4px;
  padding: 16px 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(240, 247, 255, 0.94), rgba(250, 252, 255, 0.92));
  border: 1px solid rgba(190, 215, 242, 0.75);
}

.planner-check-summary strong {
  font-size: 18px;
}

.planner-check-item {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  align-content: start;
  min-height: 0;
}

.planner-check-item--done {
  background: linear-gradient(135deg, rgba(233, 246, 255, 0.82), rgba(248, 252, 255, 0.88));
  border-color: rgba(173, 214, 243, 0.82);
}

.planner-check-item__icon {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(45, 134, 231, 0.12);
  color: #2d86e7;
  font-weight: 800;
}

.planner-check-item__content {
  display: grid;
  gap: 4px;
}

.planner-check-item__content strong {
  font-size: 17px;
  line-height: 1.4;
}

:deep(.planner-main-panel .ant-form-item-label > label) {
  font-size: 18px;
  font-weight: 700;
}

:deep(.planner-main-panel .ant-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
}

:deep(.planner-main-panel .ant-checkbox-wrapper) {
  font-size: 18px;
  line-height: 1.8;
}

:deep(.planner-main-panel .ant-checkbox + span) {
  font-size: 18px;
  line-height: 1.8;
}

@media (max-width: 960px) {
  .planner-main-panel,
  .planner-side-panel {
    padding: 22px;
  }

  .aside-stack {
    height: auto;
    grid-template-rows: none;
  }

  .planner-hero {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .planner-hero-card__layout {
    grid-template-columns: 46px minmax(0, 1fr);
    gap: 14px;
    padding-left: 0;
  }

  .planner-hero-card__eyebrow {
    width: 46px;
    min-height: 128px;
    font-size: 18px;
  }

  .planner-progress {
    flex-direction: column;
    align-items: flex-start;
  }

  .planner-form-section {
    padding: 18px;
  }

  .planner-section-head {
    flex-direction: column;
    gap: 10px;
  }

  .planner-side-panel--tips,
  .planner-side-panel--checklist {
    grid-template-rows: none;
    min-height: 0;
  }

  .planner-tip-grid,
  .planner-checklist {
    min-height: 0;
    grid-template-rows: none;
  }

  .planner-core-panel__summary {
    grid-template-columns: 1fr;
  }

  .planner-preference-panel__layout {
    min-height: auto;
  }

  .planner-preference-panel__content {
    padding-right: 0;
  }

  :deep(.planner-preference-panel__interest .ant-checkbox-group) {
    display: flex;
    flex-wrap: wrap;
    width: 100%;
    margin-right: 0;
    padding-right: 0;
  }

  .planner-preference-panel__art {
    inset: -18px;
    background-position: center right;
    background-size: auto 100%;
  }
}
</style>
