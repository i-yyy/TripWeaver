<template>
  <div class="brand-page auth-page">
    <div class="auth-decor auth-decor--top-left">✈️</div>
    <div class="auth-decor auth-decor--top-right">🧳</div>
    <div class="auth-decor auth-decor--mid-left">🗺️</div>
    <div class="auth-decor auth-decor--mid-right">📷</div>
    <div class="auth-decor auth-decor--bottom-left">🎫</div>
    <div class="auth-decor auth-decor--bottom-right">☁️</div>

    <div class="brand-shell auth-grid">
      <section class="glass-panel auth-copy-panel">
        <span class="page-kicker">欢迎回来</span>
        <h1 class="page-title auth-title">继续你的旅程，把每一次出发都安排得更顺一点</h1>
        <p class="page-subtitle">
          登录后，我们会接住你之前保存的偏好、旅行轨迹和规划记录 下一次想出发的时候，直接从熟悉的节奏开始
        </p>

        <div class="info-list auth-highlights">
          <div class="info-item">
            <strong>继续上次规划</strong>
            <span>行程结果、反馈记录和路线调整都会留在你的账号里</span>
          </div>
          <div class="info-item">
            <strong>查看旅行轨迹</strong>
            <span>搜索过的城市会在地图上留下足迹，回看也很方便</span>
          </div>
          <div class="info-item">
            <strong>统一个人设置</strong>
            <span>昵称、邮箱和密码都可以在登录后继续调整</span>
          </div>
        </div>
      </section>

      <section class="glass-panel glass-panel--soft auth-form-panel">
        <div class="auth-form-shell">
          <div class="section-heading auth-form-heading">
            <span class="auth-form-badge">账号登录</span>
            <h2>登录账号</h2>
            <p>输入邮箱和密码，回到你的智能旅行空间</p>
          </div>

          <div class="auth-form-card">
            <a-form class="auth-form" layout="vertical" @submit.prevent="handleLogin">
              <a-form-item label="邮箱">
                <a-input v-model:value="form.email" placeholder="请输入注册邮箱" />
              </a-form-item>
              <a-form-item label="密码">
                <a-input-password v-model:value="form.password" placeholder="请输入密码" />
              </a-form-item>
              <a-form-item class="auth-submit">
                <a-button type="primary" block size="large" :loading="loading" @click="handleLogin">登录</a-button>
              </a-form-item>
            </a-form>

            <div class="auth-switch-row">
              <span>还没有账号？</span>
              <a-button type="link" @click="router.push('/register')">去注册</a-button>
            </div>
          </div>

          <div class="auth-support-grid">
            <div class="auth-support-card">
              <strong>继续你的旅行记录</strong>
              <span>登录后可以直接查看旅行轨迹、历史规划和反馈记录</span>
            </div>
            <div class="auth-support-card">
              <strong>账号信息随时可改</strong>
              <span>进入个人设置后，可以继续调整昵称、邮箱和密码</span>
            </div>
          </div>
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
  display: grid;
  place-items: center;
  min-height: calc(100vh - 96px);
  padding-top: 44px;
  padding-bottom: 58px;
}

.auth-decor {
  position: absolute;
  display: grid;
  place-items: center;
  width: 68px;
  height: 68px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.52);
  box-shadow: 0 18px 34px rgba(76, 116, 170, 0.1);
  backdrop-filter: blur(10px);
  font-size: 28px;
  animation: float-soft 5.4s ease-in-out infinite;
  pointer-events: none;
}

.auth-decor--top-left {
  top: 40px;
  left: clamp(22px, 5vw, 72px);
}

.auth-decor--top-right {
  top: 58px;
  right: clamp(18px, 5vw, 64px);
  animation-delay: 0.5s;
}

.auth-decor--mid-left {
  top: 38%;
  left: clamp(8px, 3vw, 30px);
  animation-delay: 1.1s;
}

.auth-decor--mid-right {
  top: 42%;
  right: clamp(10px, 3vw, 34px);
  animation-delay: 1.6s;
}

.auth-decor--bottom-left {
  bottom: 56px;
  left: clamp(28px, 7vw, 118px);
  animation-delay: 0.8s;
}

.auth-decor--bottom-right {
  bottom: 42px;
  right: clamp(36px, 8vw, 132px);
  animation-delay: 1.9s;
}

.auth-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  width: min(1160px, 100%);
  gap: 22px;
  align-items: stretch;
}

.auth-copy-panel,
.auth-form-panel {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 34px;
}

.auth-title {
  max-width: 620px;
  font-size: clamp(38px, 4.6vw, 62px);
}

.auth-highlights {
  margin-top: 28px;
}

.auth-form-shell {
  width: 100%;
  max-width: 560px;
  margin: auto 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 18px;
}

.auth-form-heading {
  margin-bottom: 4px;
}

.auth-form-heading h2 {
  margin: 10px 0 8px;
  font-size: 30px;
  color: var(--brand-text);
}

.auth-form-badge {
  display: inline-flex;
  align-items: center;
  padding: 7px 14px;
  border-radius: 999px;
  background: rgba(45, 134, 231, 0.12);
  color: var(--brand-primary-deep);
  font-size: 16px;
  font-weight: 700;
}

.auth-form-card {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.54);
  box-shadow: 0 18px 34px rgba(76, 116, 170, 0.08);
}

.auth-form :deep(.ant-form-item) {
  margin-bottom: 18px;
}

.auth-submit {
  margin-top: 8px;
  margin-bottom: 0 !important;
}

.auth-switch-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 10px;
  padding-top: 4px;
  color: var(--brand-muted);
}

.auth-support-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.auth-support-card {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.46);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.auth-support-card strong {
  display: block;
  margin-bottom: 6px;
  color: var(--brand-text);
}

.auth-support-card span {
  color: var(--brand-muted);
  line-height: 1.7;
}

@media (max-width: 960px) {
  .auth-page {
    padding-top: 24px;
    padding-bottom: 30px;
  }

  .auth-grid {
    grid-template-columns: 1fr;
  }

  .auth-copy-panel,
  .auth-form-panel {
    padding: 24px;
  }

  .auth-form-shell {
    max-width: none;
  }

  .auth-support-grid {
    grid-template-columns: 1fr;
  }

  .auth-decor {
    width: 54px;
    height: 54px;
    border-radius: 18px;
    font-size: 22px;
  }

  .auth-decor--mid-left,
  .auth-decor--mid-right {
    display: none;
  }
}
</style>
