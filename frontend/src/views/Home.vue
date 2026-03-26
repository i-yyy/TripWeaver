<template>
  <div class="home-page">
    <a-card class="planner-card" :bordered="false">
      <h1 class="title">智能旅行规划助手</h1>
      <p class="subtitle">输入基础需求后，系统会结合多智能体生成个性化行程。</p>

      <a-form layout="vertical" @finish="handleSubmit">
        <a-row :gutter="12">
          <a-col :span="8">
            <a-form-item label="目的地城市" required>
              <a-input v-model:value="formData.city" placeholder="例如：北京" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="开始日期" required>
              <a-date-picker v-model:value="formData.start_date" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="结束日期" required>
              <a-date-picker v-model:value="formData.end_date" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="12">
          <a-col :span="6">
            <a-form-item label="天数">
              <a-input-number :value="formData.travel_days" :min="1" :max="30" style="width: 100%" disabled />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="交通偏好">
              <a-select v-model:value="formData.transportation">
                <a-select-option value="Public Transit">公共交通</a-select-option>
                <a-select-option value="Drive">自驾</a-select-option>
                <a-select-option value="Walk">步行</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="住宿偏好">
              <a-select v-model:value="formData.accommodation">
                <a-select-option value="Budget Hotel">经济酒店</a-select-option>
                <a-select-option value="Comfort Hotel">舒适酒店</a-select-option>
                <a-select-option value="Luxury Hotel">高端酒店</a-select-option>
                <a-select-option value="Homestay">民宿</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
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

        <a-form-item label="额外要求">
          <a-textarea
            v-model:value="formData.free_text_input"
            :rows="3"
            placeholder="例如：希望雨天也有可替代方案，行程不要太赶。"
          />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="loading" block size="large">
            {{ loading ? loadingStatus : '生成我的行程' }}
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'
import { generateTripPlan } from '@/services/api'
import type { TripFormData } from '@/types'

const router = useRouter()
const loading = ref(false)
const loadingStatus = ref('生成中...')

const LOCAL_USER_ID_KEY = 'trip_planner_user_id'

const getOrCreateUserId = () => {
  const cached = localStorage.getItem(LOCAL_USER_ID_KEY)
  if (cached) return cached
  const nextId = crypto.randomUUID()
  localStorage.setItem(LOCAL_USER_ID_KEY, nextId)
  return nextId
}

const createSessionId = () => crypto.randomUUID()

type LocalTripFormData = Omit<TripFormData, 'start_date' | 'end_date'> & {
  start_date: Dayjs | null
  end_date: Dayjs | null
}

const formData = reactive<LocalTripFormData>({
  user_id: getOrCreateUserId(),
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
    message.warning('结束日期必须晚于开始日期')
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
  if (!formData.city.trim()) {
    message.error('请输入目的地城市')
    return
  }
  if (!formData.start_date || !formData.end_date) {
    message.error('请选择出行日期')
    return
  }

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
      throw new Error(response.message || '生成失败')
    }

    sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
    sessionStorage.setItem('tripPlannerUserId', formData.user_id)
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
.home-page {
  min-height: 100vh;
  padding: 24px;
  background: radial-gradient(circle at top left, #c7def9 0%, #f4f8ff 45%, #eef2f8 100%);
}

.planner-card {
  max-width: 1100px;
  margin: 0 auto;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(31, 50, 81, 0.14);
}

.title {
  margin-bottom: 8px;
}

.subtitle {
  margin-bottom: 20px;
  color: #5f6b7d;
}
</style>
