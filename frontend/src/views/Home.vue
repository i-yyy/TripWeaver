<template>
  <div class="brand-page planner-page">
    <div class="brand-shell split-layout">
      <section class="glass-panel planner-main-panel">
        <div class="section-heading planner-heading">
          <span class="page-kicker">🧭 旅行规划</span>
          <h1 class="page-title planner-title">把灵感整理成一份真的能出发的行程</h1>
          <p class="page-subtitle">
            目的地、时间、预算和偏好交给我们来一起梳理系统会结合你的画像、历史反馈和当前输入，生成更贴近你的旅行方案
          </p>
        </div>

        <a-form class="brand-form-grid" layout="vertical" @submit.prevent="handleSubmit">
          <section class="planner-form-section planner-form-section--primary">
            <div class="planner-section-head planner-section-head--primary">
              <span class="planner-section-mark">🧭</span>
              <div>
                <h3>核心信息</h3>
                <p>先把城市、日期和基础预算定下来，系统就能先搭好主骨架</p>
              </div>
            </div>

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
          </section>

          <section class="planner-form-section">
            <div class="planner-section-head planner-section-head--preference">
              <span class="planner-section-mark">🎒</span>
              <div>
                <h3>偏好设置</h3>
                <p>这些信息会影响推荐方向，让行程更贴近你的出行节奏</p>
              </div>
            </div>

            <a-form-item label="❤️ 兴趣偏好">
              <a-checkbox-group v-model:value="formData.preferences">
                <a-checkbox v-for="item in preferenceOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
              </a-checkbox-group>
            </a-form-item>

            <a-form-item label="🎒 旅行风格">
              <a-checkbox-group v-model:value="formData.travel_style">
                <a-checkbox v-for="item in travelStyleOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
              </a-checkbox-group>
            </a-form-item>

            <a-form-item label="👥 同行人群">
              <a-checkbox-group v-model:value="formData.companions">
                <a-checkbox v-for="item in companionOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
              </a-checkbox-group>
            </a-form-item>

            <a-form-item label="♿ 行动需求">
              <a-checkbox-group v-model:value="formData.mobility_needs">
                <a-checkbox v-for="item in mobilityOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
              </a-checkbox-group>
            </a-form-item>
          </section>

          <section class="planner-form-section planner-form-section--compact">
            <div class="planner-section-head planner-section-head--note">
              <span class="planner-section-mark">📝</span>
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
        <section class="glass-panel glass-panel--soft planner-side-panel">
          <div class="section-heading">
            <h3>🔍 这次会帮你关注什么</h3>
            <p>你填写的信息越具体，结果就越容易贴近你真正想要的旅行节奏</p>
          </div>
          <div class="info-list">
            <div class="info-item">
              <strong>📍 目的地与日期</strong>
              <span>决定每天能安排多少内容，也会影响天气与路线建议</span>
            </div>
            <div class="info-item">
              <strong>💰 预算与住宿</strong>
              <span>会一起影响酒店候选、餐饮估算和整体安排密度</span>
            </div>
            <div class="info-item">
              <strong>👥 偏好与同行人群</strong>
              <span>系统会更偏向你喜欢的景点类型，也会顾及出行氛围</span>
            </div>
          </div>
        </section>

        <section class="glass-panel glass-panel--soft planner-side-panel">
          <div class="section-heading">
            <h3>💡 小提示</h3>
            <p>如果你不确定怎么填，可以先从城市、日期和兴趣偏好开始，剩下的留给系统帮你补全</p>
          </div>
          <div class="brand-note">
            如果你希望轻松一点的行程，可以在补充要求里写上“不要太赶”如果你担心天气，也可以提前说明“下雨要有室内备选”
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'

import { generateTripPlan } from '@/services/api'
import type { TripFormData } from '@/types'
import { useAuthState } from '@/utils/auth'

const router = useRouter()
const authState = useAuthState()
const loading = ref(false)
const loadingStatus = ref('正在生成行程...')

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
  { value: 'history', label: '🏛️ 历史文化' },
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

const createSessionId = () => crypto.randomUUID()

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
  loading.value = true

  try {
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

    sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
    sessionStorage.setItem('tripPlannerUserId', authState.user.id)
    sessionStorage.setItem('tripPlannerSessionId', formData.session_id)
    message.success('行程生成成功')
    router.push('/result')
  } catch (error: any) {
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

.planner-heading {
  margin-bottom: 22px;
}

.planner-title {
  font-size: clamp(34px, 4.2vw, 54px);
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

.planner-form-section--compact {
  background: rgba(241, 247, 255, 0.5);
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

  .planner-form-section {
    padding: 18px;
  }

  .planner-section-head {
    flex-direction: column;
    gap: 10px;
  }
}
</style>

