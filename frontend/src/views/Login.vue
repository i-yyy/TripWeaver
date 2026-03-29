<template>
  <div class="auth-page">
    <a-card class="auth-card" :bordered="false">
      <p class="auth-kicker">欢迎回来</p>
      <h1>登录你的旅行空间</h1>
      <p class="auth-tip">继续你的规划、偏好和旅行轨迹。</p>

      <a-form layout="vertical" @submit.prevent="handleLogin">
        <a-form-item label="邮箱">
          <a-input v-model:value="form.email" placeholder="you@example.com" />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password v-model:value="form.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" block size="large" :loading="loading" @click="handleLogin">登录</a-button>
        </a-form-item>
      </a-form>

      <div class="switch-row">
        还没有账号？
        <a-button type="link" @click="router.push('/register')">去注册</a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { loginUser } from '@/services/api'
import { setAuthSession } from '@/utils/auth'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  email: '',
  password: '',
})

const handleLogin = async () => {
  if (!form.email.trim() || !form.password.trim()) {
    message.error('请先填写邮箱和密码')
    return
  }

  loading.value = true
  try {
    const response = await loginUser({ email: form.email.trim(), password: form.password })
    if (!response.success || !response.data) {
      throw new Error(response.message || '登录失败')
    }
    setAuthSession(response.access_token, response.data)
    message.success('登录成功')
    router.push('/planner')
  } catch (error: any) {
    message.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 64px);
  display: grid;
  place-items: center;
  padding: 32px 16px;
}

.auth-card {
  width: min(100%, 460px);
  border-radius: 26px;
  box-shadow: 0 22px 48px rgba(26, 48, 82, 0.16);
}

.auth-kicker {
  margin-bottom: 8px;
  color: #cb7a32;
  letter-spacing: 2px;
}

h1 {
  margin-bottom: 8px;
}

.auth-tip {
  margin-bottom: 24px;
  color: #607086;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
