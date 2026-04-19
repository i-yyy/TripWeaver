<template>
  <div class="auth-page">
    <div class="auth-stage">
      <button class="auth-back-button" type="button" aria-label="返回品牌页" @click="router.push('/')">
        &#8249;
      </button>

      <section class="auth-form-panel">
        <div class="auth-form-heading">
          <span>织途智能旅行助手</span>
          <h2>注册</h2>
        </div>

        <a-form class="auth-form" layout="vertical" @submit.prevent="handleRegister">
          <a-form-item>
            <a-input v-model:value="form.nickname" placeholder="请输入昵称" />
          </a-form-item>
          <a-form-item>
            <a-input v-model:value="form.email" placeholder="请输入邮箱" />
          </a-form-item>
          <a-form-item>
            <a-input-password v-model:value="form.password" placeholder="请输入密码" />
          </a-form-item>
          <a-form-item>
            <a-input-password v-model:value="confirmPassword" placeholder="请再次输入密码" />
          </a-form-item>
          <a-form-item class="auth-submit">
            <a-button type="primary" :loading="loading" @click="handleRegister">注册</a-button>
          </a-form-item>
        </a-form>

        <div class="auth-switch-row">
          <a-button type="link" @click="router.push('/login')">
            <span>已经有账号了？</span>
            <span class="auth-link-strong">去登录</span>
          </a-button>
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
.auth-form-panel :deep(.ant-form),
.auth-switch-row {
  position: relative;
  z-index: 1;
}

.auth-form-heading span {
  color: #5f6b7a;
}

.auth-form-heading h2 {
  margin: 60px 0 34px;
  color: #172033;
  font-family: "Microsoft YaHei", "Microsoft YaHei UI", "PingFang SC", "Noto Sans SC", sans-serif;
  font-size: 34px;
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: 0;
}

.auth-form-panel :deep(.ant-form) {
  width: 292px;
}

.auth-form-panel :deep(.ant-form-item) {
  margin-bottom: 18px;
}

.auth-form-panel :deep(.ant-input),
.auth-form-panel :deep(.ant-input-affix-wrapper) {
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

.auth-form-panel :deep(.ant-input-affix-wrapper .ant-input) {
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

.auth-form-panel :deep(.ant-input:hover),
.auth-form-panel :deep(.ant-input:focus),
.auth-form-panel :deep(.ant-input-affix-wrapper:hover),
.auth-form-panel :deep(.ant-input-affix-wrapper-focused) {
  border: none !important;
  background: #dce1e7 !important;
  background-color: #dce1e7 !important;
  box-shadow: none !important;
}

.auth-form-panel :deep(.ant-btn) {
  height: 38px;
  border-radius: 18px;
  font-weight: 700;
}

.auth-submit {
  margin-top: 6px;
}

.auth-submit :deep(.ant-btn) {
  width: 146px;
  min-width: 146px;
  background: #2f7edb;
  box-shadow: 0 6px 12px rgba(47, 126, 219, 0.22);
}

.auth-switch-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  margin-top: 18px;
  color: #53647a;
}

.auth-switch-row :deep(.ant-btn) {
  padding: 0;
  color: #53647a;
  font-weight: 600;
}

.auth-switch-row :deep(.ant-btn span:first-child) {
  color: #53647a;
}

.auth-switch-row :deep(.ant-btn span + span) {
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
