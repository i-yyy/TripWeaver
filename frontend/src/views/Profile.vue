<template>
  <div class="brand-page">
    <div class="brand-shell aside-stack">
      <section class="glass-panel profile-panel">
        <div class="section-heading">
          <span class="page-kicker">个人设置</span>
          <h1 class="page-title profile-title">维护你的账号信息，让之后的每次出发都更顺手</h1>
          <p class="page-subtitle">昵称、邮箱和密码都可以在这里调整。修改后会同步到当前登录状态里。</p>
        </div>

        <div class="brand-stat-grid">
          <div class="brand-stat">
            <span>当前昵称</span>
            <strong>{{ profileForm.nickname || '未设置' }}</strong>
          </div>
          <div class="brand-stat">
            <span>当前邮箱</span>
            <strong>{{ profileForm.email || '未设置' }}</strong>
          </div>
          <div class="brand-stat">
            <span>账号状态</span>
            <strong>{{ authState.user?.is_active ? '正常可用' : '待确认' }}</strong>
          </div>
        </div>
      </section>

      <section class="glass-panel glass-panel--soft profile-panel">
        <div class="section-heading">
          <h2>个人信息</h2>
          <p>更新昵称和邮箱后，页面上的登录信息也会一起刷新。</p>
        </div>

        <a-form layout="vertical">
          <a-row :gutter="16">
            <a-col :xs="24" :md="12">
              <a-form-item label="昵称">
                <a-input v-model:value="profileForm.nickname" placeholder="请输入昵称" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="邮箱">
                <a-input v-model:value="profileForm.email" placeholder="请输入邮箱" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item>
            <a-button type="primary" :loading="profileLoading" @click="saveProfile">保存个人信息</a-button>
          </a-form-item>
        </a-form>
      </section>

      <section class="glass-panel glass-panel--soft profile-panel">
        <div class="section-heading">
          <h2>修改密码</h2>
          <p>出于安全考虑，修改密码前需要先输入当前密码。</p>
        </div>

        <a-form layout="vertical">
          <a-row :gutter="16">
            <a-col :xs="24" :md="8">
              <a-form-item label="当前密码">
                <a-input-password v-model:value="passwordForm.current_password" placeholder="请输入当前密码" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="8">
              <a-form-item label="新密码">
                <a-input-password v-model:value="passwordForm.new_password" placeholder="请输入新密码" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="8">
              <a-form-item label="确认新密码">
                <a-input-password v-model:value="confirmNewPassword" placeholder="请再次输入新密码" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item>
            <a-button :loading="passwordLoading" @click="savePassword">更新密码</a-button>
          </a-form-item>
        </a-form>
      </section>

      <section class="glass-panel glass-panel--soft profile-panel">
        <div class="section-heading">
          <h2>账号管理</h2>
          <p>如果你决定不再使用当前账号，也可以在这里完成注销。</p>
        </div>
        <div class="brand-note danger-note">
          注销账号后，你的账号信息、旅行轨迹、反馈和记忆数据都会被永久删除，且无法恢复。请在确认不再需要这些数据时再继续。
        </div>
        <div class="toolbar-group" style="margin-top: 18px">
          <a-button danger :loading="deleteLoading" @click="deleteAccount">注销账号</a-button>
        </div>
      </section>
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
  const confirmed = window.confirm('注销账号后，账号信息、旅行轨迹、反馈和记忆数据都会永久删除。确定继续吗？')
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
.profile-panel {
  padding: 28px;
}

.profile-title {
  font-size: clamp(34px, 4.2vw, 52px);
}

@media (max-width: 960px) {
  .profile-panel {
    padding: 22px;
  }
}
</style>
