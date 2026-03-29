<template>
  <div class="planner-page">
    <div class="planner-shell">
      <a-card class="planner-card" :bordered="false">
        <div class="planner-head">
          <div>
            <p class="planner-kicker">旅行规划主页面</p>
            <h1>把灵感整理成一份真的能出发的行程</h1>
            <p class="planner-tip">我们会结合偏好、预算、同行人和已有画像，生成一份更贴近你的旅行建议。</p>
          </div>
          <a-space wrap>
            <a-button @click="goTracks">我的旅行轨迹</a-button>
            <a-button @click="goKBEval">RAG 评测</a-button>
          </a-space>
        </div>

        <a-form layout="vertical" @submit.prevent="handleSubmit">
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
                <a-input-number :value="formData.travel_days" :min="1" :max="30" disabled style="width: 100%" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="交通方式">
                <a-select v-model:value="formData.transportation">
                  <a-select-option value="Public Transit">公共交通</a-select-option>
                  <a-select-option value="Drive">自驾</a-select-option>
                  <a-select-option value="Walk">步行</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="住宿偏好">
                <a-select v-model:value="formData.accommodation">
                  <a-select-option value="Budget Hotel">经济酒店</a-select-option>
                  <a-select-option value="Comfort Hotel">舒适酒店</a-select-option>
                  <a-select-option value="Luxury Hotel">高端酒店</a-select-option>
                  <a-select-option value="Homestay">民宿</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="预算等级">
                <a-select v-model:value="formData.budget_level" allow-clear>
                  <a-select-option value="low">低预算</a-select-option>
                  <a-select-option value="medium">中预算</a-select-option>
                  <a-select-option value="high">高预算</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="兴趣偏好">
            <a-checkbox-group v-model:value="formData.preferences">
              <a-checkbox value="history">历史文化</a-checkbox>
              <a-checkbox value="nature">自然风光</a-checkbox>
              <a-checkbox value="food">美食</a-checkbox>
              <a-checkbox value="shopping">购物</a-checkbox>
              <a-checkbox value="museum">博物馆</a-checkbox>
            </a-checkbox-group>
          </a-form-item>

          <a-form-item label="同行人群">
            <a-checkbox-group v-model:value="formData.companions">
              <a-checkbox value="solo">独行</a-checkbox>
              <a-checkbox value="couple">情侣</a-checkbox>
              <a-checkbox value="family">家庭</a-checkbox>
              <a-checkbox value="friends">朋友</a-checkbox>
            </a-checkbox-group>
          </a-form-item>

          <a-form-item label="补充要求">
            <a-textarea
              v-model:value="formData.free_text_input"
              :rows="4"
              placeholder="例如：希望雨天也有备选方案；不要安排太赶；想多一点 citywalk。"
            />
          </a-form-item>

          <a-form-item>
            <a-button type="primary" block size="large" :loading="loading" @click="handleSubmit">
              {{ loading ? loadingStatus : '生成我的行程' }}
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
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
.planner-page {
  padding: 28px 18px 40px;
}

.planner-shell {
  max-width: 1180px;
  margin: 0 auto;
}

.planner-card {
  border-radius: 28px;
  box-shadow: 0 24px 50px rgba(31, 50, 81, 0.14);
}

.planner-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}

.planner-kicker {
  margin-bottom: 10px;
  color: #cb7a32;
  letter-spacing: 2px;
}

.planner-tip {
  max-width: 680px;
  color: #617086;
  line-height: 1.8;
}

@media (max-width: 900px) {
  .planner-head {
    flex-direction: column;
  }
}
</style>
