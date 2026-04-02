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
        <span class="page-kicker">新的故事，从这里开始</span>
        <h1 class="page-title auth-title">注册一个账号，让旅行偏好、轨迹和反馈都被好好记住</h1>
        <p class="page-subtitle">
          以后每次规划都不再从零开始 系统会慢慢懂你的旅行节奏，也会把每一次搜索留下来的线索整理成更贴近你的建议
        </p>

        <div class="info-list auth-highlights">
          <div class="info-item">
            <strong>保存旅行轨迹</strong>
            <span>搜索过的城市会自动收进你的个人地图里</span>
          </div>
          <div class="info-item">
            <strong>积累偏好画像</strong>
            <span>你喜欢的景点类型、住宿倾向和节奏都会持续沉淀</span>
          </div>
          <div class="info-item">
            <strong>统一账号管理</strong>
            <span>登录后就能在个人设置里维护昵称、邮箱和密码</span>
          </div>
        </div>
      </section>

      <section class="glass-panel glass-panel--soft auth-form-panel">
        <div class="section-heading">
          <h2>注册账号</h2>
          <p>只需要三步，就能拥有自己的智能旅行空间</p>
        </div>

        <a-form layout="vertical" @submit.prevent="handleRegister">
          <a-form-item label="昵称">
            <a-input v-model:value="form.nickname" placeholder="想让大家怎么称呼你" />
          </a-form-item>
          <a-form-item label="邮箱">
            <a-input v-model:value="form.email" placeholder="请输入常用邮箱" />
          </a-form-item>
          <a-form-item label="密码">
            <a-input-password v-model:value="form.password" placeholder="请输入至少 6 位密码" />
          </a-form-item>
          <a-form-item label="确认密码">
            <a-input-password v-model:value="confirmPassword" placeholder="请再输入一次密码" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" block size="large" :loading="loading" @click="handleRegister">注册</a-button>
          </a-form-item>
        </a-form>

        <div class="auth-switch-row">
          <span>已经有账号了？</span>
          <a-button type="link" @click="router.push('/login')">去登录</a-button>
        </div>
      </section>
    </div>
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
  display: flex;
  align-items: center;
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
