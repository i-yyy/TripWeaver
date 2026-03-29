<template>
  <div class="auth-page">
    <a-card class="auth-card" :bordered="false">
      <p class="auth-kicker">新的旅程，从这里开始</p>
      <h1>注册账号</h1>
      <p class="auth-tip">创建你的专属旅行身份，把偏好、反馈和轨迹都沉淀下来。</p>

      <a-form layout="vertical" @submit.prevent="handleRegister">
        <a-form-item label="昵称">
          <a-input v-model:value="form.nickname" placeholder="想让大家怎么称呼你" />
        </a-form-item>
        <a-form-item label="邮箱">
          <a-input v-model:value="form.email" placeholder="you@example.com" />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password v-model:value="form.password" placeholder="至少 6 位密码" />
        </a-form-item>
        <a-form-item label="确认密码">
          <a-input-password v-model:value="confirmPassword" placeholder="再输一次，确认没手滑" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" block size="large" :loading="loading" @click="handleRegister">注册</a-button>
        </a-form-item>
      </a-form>

      <div class="switch-row">
        已经有账号？
        <a-button type="link" @click="router.push('/login')">去登录</a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { registerUser } from '@/services/api'

const router = useRouter()
const loading = ref(false)
const confirmPassword = ref('')
const form = reactive({
  nickname: '',
  email: '',
  password: '',
})

const handleRegister = async () => {
  if (!form.nickname.trim() || !form.email.trim() || !form.password.trim()) {
    message.error('请完整填写注册信息')
    return
  }
  if (form.password !== confirmPassword.value) {
    message.error('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    const response = await registerUser({
      nickname: form.nickname.trim(),
      email: form.email.trim(),
      password: form.password,
    })
    if (!response.success) {
      throw new Error(response.message || '注册失败')
    }
    message.success('注册成功，请登录')
    router.push('/login')
  } catch (error: any) {
    message.error(error.message || '注册失败')
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
  width: min(100%, 500px);
  border-radius: 26px;
  box-shadow: 0 22px 48px rgba(26, 48, 82, 0.16);
}

.auth-kicker {
  margin-bottom: 8px;
  color: #2d78b8;
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
