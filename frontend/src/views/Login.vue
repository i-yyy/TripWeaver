<template>
  <div class="brand-page auth-page">
    <div class="brand-shell auth-grid">
      <section class="glass-panel auth-copy-panel">
        <span class="page-kicker">欢迎回来</span>
        <h1 class="page-title auth-title">继续你的旅程，把每一次出发都安排得更顺一点</h1>
        <p class="page-subtitle">
          登录后，我们会接住你之前保存的偏好、旅行轨迹和规划记录。下一次想出发的时候，直接从熟悉的节奏开始。
        </p>

        <div class="info-list auth-highlights">
          <div class="info-item">
            <strong>继续上次规划</strong>
            <span>行程结果、反馈记录和路线调整都会留在你的账号里。</span>
          </div>
          <div class="info-item">
            <strong>查看旅行轨迹</strong>
            <span>搜索过的城市会在地图上留下足迹，回看也很方便。</span>
          </div>
          <div class="info-item">
            <strong>统一个人设置</strong>
            <span>昵称、邮箱和密码都可以在登录后继续调整。</span>
          </div>
        </div>
      </section>

      <section class="glass-panel glass-panel--soft auth-form-panel">
        <div class="section-heading">
          <h2>登录账号</h2>
          <p>输入邮箱和密码，回到你的智能旅行空间。</p>
        </div>

        <a-form layout="vertical" @submit.prevent="handleLogin">
          <a-form-item label="邮箱">
            <a-input v-model:value="form.email" placeholder="请输入注册邮箱" />
          </a-form-item>
          <a-form-item label="密码">
            <a-input-password v-model:value="form.password" placeholder="请输入密码" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" block size="large" :loading="loading" @click="handleLogin">登录</a-button>
          </a-form-item>
        </a-form>

        <div class="auth-switch-row">
          <span>还没有账号？</span>
          <a-button type="link" @click="router.push('/register')">去注册</a-button>
        </div>
      </section>
    </div>
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
    router.push('/')
  } catch (error: any) {
    message.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
}

.auth-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
  gap: 22px;
  align-items: stretch;
}

.auth-copy-panel,
.auth-form-panel {
  padding: 34px;
}

.auth-title {
  max-width: 620px;
  font-size: clamp(38px, 4.6vw, 62px);
}

.auth-highlights {
  margin-top: 28px;
}

.auth-form-panel {
  align-self: center;
}

.auth-switch-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 10px;
  color: var(--brand-muted);
}

@media (max-width: 960px) {
  .auth-grid {
    grid-template-columns: 1fr;
  }

  .auth-copy-panel,
  .auth-form-panel {
    padding: 24px;
  }
}
</style>
