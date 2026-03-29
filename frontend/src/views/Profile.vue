<template>
  <div class="profile-page">
    <div class="profile-shell">
      <a-card class="profile-card" :bordered="false" title="个人信息">
        <a-form layout="vertical">
          <a-form-item label="昵称">
            <a-input v-model:value="profileForm.nickname" placeholder="请输入昵称" />
          </a-form-item>
          <a-form-item label="邮箱">
            <a-input v-model:value="profileForm.email" placeholder="请输入邮箱" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" :loading="profileLoading" @click="saveProfile">
              保存个人信息
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>

      <a-card class="profile-card" :bordered="false" title="修改密码">
        <a-form layout="vertical">
          <a-form-item label="当前密码">
            <a-input-password
              v-model:value="passwordForm.current_password"
              placeholder="请输入当前密码"
            />
          </a-form-item>
          <a-form-item label="新密码">
            <a-input-password
              v-model:value="passwordForm.new_password"
              placeholder="请输入新密码"
            />
          </a-form-item>
          <a-form-item label="确认新密码">
            <a-input-password
              v-model:value="confirmNewPassword"
              placeholder="请再次输入新密码"
            />
          </a-form-item>
          <a-form-item>
            <a-button :loading="passwordLoading" @click="savePassword">
              更新密码
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>

      <a-card class="profile-card danger-card" :bordered="false" title="账号管理">
        <p class="danger-text">
          注销账号后，你的账号信息、旅行轨迹、反馈和记忆数据都会被永久删除，且无法恢复。
        </p>
        <a-button danger :loading="deleteLoading" @click="deleteAccount">
          注销账号
        </a-button>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import {
  changeAccountPassword,
  deleteCurrentAccount,
  getCurrentUser,
  updateAccountProfile,
} from '@/services/api'
import { clearAuthSession, updateStoredUser, useAuthState } from '@/utils/auth'

const router = useRouter()
const authState = useAuthState()
const profileLoading = ref(false)
const passwordLoading = ref(false)
const deleteLoading = ref(false)
const confirmNewPassword = ref('')

const profileForm = reactive({
  nickname: '',
  email: '',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
})

onMounted(async () => {
  if (authState.user) {
    profileForm.nickname = authState.user.nickname
    profileForm.email = authState.user.email
    return
  }

  try {
    const response = await getCurrentUser()
    if (response.success && response.data) {
      updateStoredUser(response.data)
      profileForm.nickname = response.data.nickname
      profileForm.email = response.data.email
    }
  } catch (error: any) {
    message.error(error.message || '获取用户信息失败')
  }
})

const saveProfile = async () => {
  if (!profileForm.nickname.trim() || !profileForm.email.trim()) {
    message.error('请完整填写昵称和邮箱')
    return
  }

  profileLoading.value = true
  try {
    const response = await updateAccountProfile({
      nickname: profileForm.nickname.trim(),
      email: profileForm.email.trim(),
    })
    if (!response.success || !response.data) {
      throw new Error(response.message || '更新失败')
    }
    updateStoredUser(response.data)
    message.success('个人信息已更新')
  } catch (error: any) {
    message.error(error.message || '更新失败')
  } finally {
    profileLoading.value = false
  }
}

const savePassword = async () => {
  if (!passwordForm.current_password || !passwordForm.new_password) {
    message.error('请完整填写密码信息')
    return
  }
  if (passwordForm.new_password !== confirmNewPassword.value) {
    message.error('两次输入的新密码不一致')
    return
  }

  passwordLoading.value = true
  try {
    const response = await changeAccountPassword(passwordForm)
    if (!response.success) {
      throw new Error(response.message || '修改密码失败')
    }
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    confirmNewPassword.value = ''
    message.success('密码已更新')
  } catch (error: any) {
    message.error(error.message || '修改密码失败')
  } finally {
    passwordLoading.value = false
  }
}

const deleteAccount = async () => {
  const confirmed = window.confirm(
    '注销账号后，你的账号信息、旅行轨迹、反馈和记忆数据都会被永久删除。确定继续吗？',
  )
  if (!confirmed) {
    return
  }

  deleteLoading.value = true
  try {
    const response = await deleteCurrentAccount()
    if (!response.success) {
      throw new Error(response.message || '注销账号失败')
    }
    clearAuthSession()
    sessionStorage.removeItem('tripPlan')
    sessionStorage.removeItem('tripPlannerUserId')
    sessionStorage.removeItem('tripPlannerSessionId')
    message.success('账号已注销')
    router.replace('/register')
  } catch (error: any) {
    message.error(error.message || '注销账号失败')
  } finally {
    deleteLoading.value = false
  }
}
</script>

<style scoped>
.profile-page {
  padding: 32px 20px 48px;
}

.profile-shell {
  max-width: 860px;
  margin: 0 auto;
  display: grid;
  gap: 20px;
}

.profile-card {
  border-radius: 24px;
  box-shadow: 0 20px 45px rgba(31, 50, 81, 0.12);
}

.danger-card :deep(.ant-card-head-title) {
  color: #b42318;
}

.danger-text {
  margin-bottom: 16px;
  color: #6b7280;
  line-height: 1.7;
}
</style>
