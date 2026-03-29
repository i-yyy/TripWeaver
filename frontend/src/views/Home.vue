<template>
  <div class="brand-page planner-page">
    <div class="brand-shell split-layout">
      <section class="glass-panel planner-main-panel">
        <div class="section-heading planner-heading">
          <span class="page-kicker">旅行规划主页面</span>
          <h1 class="page-title planner-title">把灵感整理成一份真的能出发的行程</h1>
          <p class="page-subtitle">
            目的地、时间、预算和偏好交给我们来一起梳理。系统会结合你的画像、历史反馈和当前输入，生成更贴近你的旅行方案。
          </p>
        </div>

        <div class="toolbar-group planner-top-actions">
          <span class="brand-chip">已登录账号：{{ authState.user?.nickname || '旅行者' }}</span>
          <a-button @click="goTracks">我的旅行轨迹</a-button>
          <a-button @click="goKBEval">RAG 评测</a-button>
        </div>

        <a-form class="brand-form-grid" layout="vertical" @submit.prevent="handleSubmit">
          <a-row :gutter="16">
            <a-col :xs="24" :md="8">
              <a-form-item label="目的地城市" required>
                <a-input v-model:value="formData.city" placeholder="例如：北京、上海、杭州" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="8">
              <a-form-item label="开始日期" required>
                <a-date-picker v-model:value="formData.start_date" style="width: 100%" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="8">
              <a-form-item label="结束日期" required>
                <a-date-picker v-model:value="formData.end_date" style="width: 100%" />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :xs="24" :md="6">
              <a-form-item label="旅行天数">
                <a-input-number :value="formData.travel_days" :min="1" :max="30" disabled />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="交通方式">
                <a-select v-model:value="formData.transportation">
                  <a-select-option v-for="item in transportOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="住宿偏好">
                <a-select v-model:value="formData.accommodation">
                  <a-select-option v-for="item in accommodationOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="预算等级">
                <a-select v-model:value="formData.budget_level" allow-clear placeholder="请选择预算等级">
                  <a-select-option v-for="item in budgetOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="兴趣偏好">
            <a-checkbox-group v-model:value="formData.preferences">
              <a-checkbox v-for="item in preferenceOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>

          <a-form-item label="旅行风格">
            <a-checkbox-group v-model:value="formData.travel_style">
              <a-checkbox v-for="item in travelStyleOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>

          <a-form-item label="同行人群">
            <a-checkbox-group v-model:value="formData.companions">
              <a-checkbox v-for="item in companionOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>

          <a-row :gutter="16">
            <a-col :xs="24" :md="12">
              <a-form-item label="饮食限制">
                <a-checkbox-group v-model:value="formData.dietary_restrictions">
                  <a-checkbox v-for="item in dietaryOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="行动需求">
                <a-checkbox-group v-model:value="formData.mobility_needs">
                  <a-checkbox v-for="item in mobilityOptions" :key="item.value" :value="item.value">{{ item.label }}</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="补充要求">
            <a-textarea
              v-model:value="formData.free_text_input"
              :rows="4"
              placeholder="例如：希望雨天也有备选方案，不要安排得太赶，想多一点 citywalk。"
            />
          </a-form-item>

          <a-form-item>
            <a-button type="primary" block size="large" :loading="loading" @click="handleSubmit">
              {{ loading ? loadingStatus : '生成我的行程' }}
            </a-button>
          </a-form-item>
        </a-form>
      </section>

      <aside class="aside-stack">
        <section class="glass-panel glass-panel--soft planner-side-panel">
          <div class="section-heading">
            <h3>这次会帮你关注什么</h3>
            <p>你填写的信息越具体，结果就越容易贴近你真正想要的旅行节奏。</p>
          </div>
          <div class="info-list">
            <div class="info-item">
              <strong>目的地与日期</strong>
              <span>决定每天能安排多少内容，也会影响天气与路线建议。</span>
            </div>
            <div class="info-item">
              <strong>预算与住宿</strong>
              <span>会一起影响酒店候选、餐饮估算和整体安排密度。</span>
            </div>
            <div class="info-item">
              <strong>偏好与同行人群</strong>
              <span>系统会更偏向你喜欢的景点类型，也会顾及出行氛围。</span>
            </div>
          </div>
        </section>

        <section class="glass-panel glass-panel--soft planner-side-panel">
          <div class="section-heading">
            <h3>小提示</h3>
            <p>如果你不确定怎么填，可以先从城市、日期和兴趣偏好开始，剩下的留给系统帮你补全。</p>
          </div>
          <div class="brand-note">
            如果你希望轻松一点的行程，可以在补充要求里写上“不要太赶”。如果你担心天气，也可以提前说明“下雨要有室内备选”。
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
  { value: 'history', label: '历史文化' },
  { value: 'nature', label: '自然风光' },
  { value: 'food', label: '美食' },
  { value: 'shopping', label: '购物' },
  { value: 'museum', label: '博物馆' },
]

const travelStyleOptions = [
  { value: 'slow', label: '慢节奏' },
  { value: 'citywalk', label: '城市漫游' },
  { value: 'checkin', label: '经典打卡' },
  { value: 'local', label: '本地体验' },
]

const companionOptions = [
  { value: 'solo', label: '独行' },
  { value: 'couple', label: '情侣' },
  { value: 'family', label: '家庭' },
  { value: 'friends', label: '朋友' },
]

const dietaryOptions = [
  { value: 'vegetarian', label: '素食' },
  { value: 'no_spicy', label: '少辣或不辣' },
  { value: 'halal', label: '清真' },
]

const mobilityOptions = [
  { value: 'less_walking', label: '尽量少走路' },
  { value: 'wheelchair', label: '无障碍优先' },
  { value: 'rest_friendly', label: '安排休息点' },
]

const createSessionId = () => crypto.randomUUID()

type LocalTripFormData = Omit<TripFormData, 'start_date' | 'end_date'> & {
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
  dietary_restrictions: [],
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
      dietary_restrictions: formData.dietary_restrictions,
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

const goKBEval = () => router.push('/kb-eval')
const goTracks = () => router.push('/tracks')
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

.planner-top-actions {
  margin-bottom: 22px;
}

@media (max-width: 960px) {
  .planner-main-panel,
  .planner-side-panel {
    padding: 22px;
  }
}
</style>
