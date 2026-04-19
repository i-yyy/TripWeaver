<template>
  <div class="auth-page">
    <div class="auth-stage">
      <button class="auth-back-button" type="button" aria-label="返回品牌页" @click="router.push('/')">
        &#8249;
      </button>

      <section class="auth-form-panel">
        <div class="auth-form-heading">
          <span>织途智能旅行助手</span>
          <h2>登录</h2>
        </div>

        <a-form class="auth-form" layout="vertical" @submit.prevent="handleLogin">
          <a-form-item>
            <a-input v-model:value="form.email" placeholder="请输入邮箱" />
          </a-form-item>
          <a-form-item>
            <a-input-password v-model:value="form.password" placeholder="请输入密码" />
          </a-form-item>
          <div class="auth-options-row">
            <a-button type="primary" :loading="loading" @click="handleLogin">登录</a-button>
            <label class="remember-row" :class="{ 'remember-row--checked': rememberPassword }">
              <input v-model="rememberPassword" class="remember-input" type="checkbox" />
              <span class="remember-dot"></span>
              <span>记住密码</span>
            </label>
          </div>
          <a-form-item class="auth-submit">
            <a-button type="link" @click="router.push('/register')">
              <span>还没有账号？</span>
              <span class="auth-link-strong">去注册</span>
            </a-button>
          </a-form-item>
        </a-form>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { loginUser } from '@/services/api'
import { setAuthSession } from '@/utils/auth'

const router = useRouter()
const loading = ref(false)
const rememberPassword = ref(false)
const REMEMBER_PASSWORD_KEY = 'tripPlannerRememberedLogin'
const form = reactive({
  email: '',
  password: '',
})

onMounted(() => {
  const rememberedLogin = localStorage.getItem(REMEMBER_PASSWORD_KEY)
  if (!rememberedLogin) {
    return
  }

  try {
    const parsed = JSON.parse(rememberedLogin) as { email?: string; password?: string }
    form.email = parsed.email || ''
    form.password = parsed.password || ''
    rememberPassword.value = Boolean(parsed.email && parsed.password)
  } catch {
    localStorage.removeItem(REMEMBER_PASSWORD_KEY)
  }
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
    if (rememberPassword.value) {
      localStorage.setItem(
        REMEMBER_PASSWORD_KEY,
        JSON.stringify({ email: form.email.trim(), password: form.password }),
      )
    } else {
      localStorage.removeItem(REMEMBER_PASSWORD_KEY)
    }
    message.success('登录成功')
    router.push('/community')
  } catch (error: any) {
    message.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 18px 30px;
  background: #eef1f5;
}

.auth-stage {
  position: relative;
  width: min(1360px, calc(100vw - 60px));
  height: min(680px, calc(100vh - 36px));
  min-height: 560px;
  display: grid;
  grid-template-columns: 430px minmax(0, 1fr);
  align-items: stretch;
  overflow: hidden;
  border-radius: 24px;
  background: url('@/assets/auth-trip-bg.jpg') center center / cover no-repeat;
  box-shadow: none;
}

.auth-brand-copy {
  display: none;
}

.auth-form-heading span {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.auth-form-panel {
  position: relative;
  z-index: 1;
  grid-column: 1;
  grid-row: 1;
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 58px 76px 56px 88px;
  background: #ffffff;
}

.auth-form-panel::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  right: -214px;
  width: 280px;
  background: #ffffff;
  clip-path: path('M 0 0 H 258 C 194 46 136 86 146 154 C 156 222 244 232 218 304 C 188 386 72 372 74 456 C 76 530 190 542 166 614 C 158 640 144 662 138 680 H 0 Z');
  pointer-events: none;
}

.auth-back-button {
  position: absolute;
  top: 18px;
  left: 22px;
  z-index: 2;
  width: 34px;
  height: 34px;
  display: inline-grid;
  place-items: center;
  padding: 0;
  border: none;
  background: transparent;
  color: #53647a;
  font-size: 38px;
  font-weight: 300;
  line-height: 1;
  cursor: pointer;
  transition: color 0.2s ease, transform 0.2s ease;
}

.auth-back-button:hover {
  color: #2f7edb;
  transform: translateX(-2px);
}

.auth-form-heading,
.auth-form,
.auth-switch-row {
  position: relative;
  z-index: 1;
}

.auth-form-heading span {
  color: #5f6b7a;
}

.auth-form-heading h2 {
  margin: 74px 0 54px;
  color: #172033;
  font-family: "Microsoft YaHei", "Microsoft YaHei UI", "PingFang SC", "Noto Sans SC", sans-serif;
  font-size: 34px;
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: 0;
}

.auth-form {
  width: 292px;
}

.auth-form :deep(.ant-form-item) {
  margin-bottom: 24px;
}

.auth-submit {
  margin-top: 28px;
  margin-bottom: 0 !important;
  text-align: left;
}

.auth-form :deep(.ant-input),
.auth-form :deep(.ant-input-affix-wrapper) {
  width: 100%;
  height: 52px;
  min-height: 52px;
  border: none !important;
  border-radius: 999px;
  background: #e5e8ed !important;
  background-color: #e5e8ed !important;
  box-sizing: border-box;
  box-shadow: none !important;
  color: #27313f;
  overflow: hidden;
  padding-left: 24px;
  padding-right: 24px;
}

.auth-form :deep(.ant-input-affix-wrapper .ant-input) {
  width: 100%;
  height: 100%;
  min-height: 0;
  background: transparent !important;
  background-color: transparent !important;
  border-radius: 999px;
  box-sizing: border-box;
  box-shadow: none !important;
  padding-left: 0;
  padding-right: 0;
}

.auth-form :deep(.ant-input:hover),
.auth-form :deep(.ant-input:focus),
.auth-form :deep(.ant-input-affix-wrapper:hover),
.auth-form :deep(.ant-input-affix-wrapper-focused) {
  border: none !important;
  background: #dce1e7 !important;
  background-color: #dce1e7 !important;
  box-shadow: none !important;
}

.auth-form :deep(.ant-btn) {
  height: 38px;
  border-radius: 18px;
  font-weight: 700;
}

.auth-options-row {
  display: flex;
  align-items: center;
  gap: 28px;
  margin-top: 6px;
}

.auth-options-row :deep(.ant-btn) {
  width: 146px;
  min-width: 146px;
  background: #2f7edb;
  box-shadow: 0 6px 12px rgba(47, 126, 219, 0.22);
}

.remember-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #4f5d6f;
  font-size: 14px;
  white-space: nowrap;
  cursor: pointer;
}

.remember-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.remember-dot {
  position: relative;
  width: 18px;
  height: 18px;
  border: 2px solid #d6dce4;
  border-radius: 50%;
  background: #ffffff;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.remember-row--checked .remember-dot {
  border-color: #2f7edb;
  background: #2f7edb;
}

.remember-row--checked .remember-dot::after {
  content: '';
  position: absolute;
  top: 4px;
  left: 4px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ffffff;
}

.auth-switch-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-top: 22px;
  padding-top: 4px;
  color: #53647a;
}

.auth-switch-row :deep(.ant-btn),
.auth-submit :deep(.ant-btn) {
  padding: 0;
  color: #53647a;
  font-weight: 600;
}

.auth-submit :deep(.ant-btn span + span) {
  margin-left: 4px;
}

.auth-link-strong {
  color: #2f7edb;
  font-weight: 700;
}

@media (max-width: 960px) {
  .auth-page {
    padding: 0;
  }

  .auth-stage {
    grid-template-columns: 1fr;
    width: 100%;
    height: auto;
    min-height: 100vh;
    border-radius: 0;
  }

  .auth-form-panel {
    width: min(430px, 100%);
    min-height: 100vh;
    padding: 40px 28px;
    border-radius: 0;
  }

  .auth-form-panel::before {
    display: none;
  }

  .auth-brand-copy {
    display: none;
  }
}
</style>
