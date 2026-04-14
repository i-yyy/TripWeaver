<template>
  <div class="brand-page">
    <div class="brand-shell profile-home">
      <section class="profile-cover">
        <div class="profile-cover__identity">
          <img v-if="resolvedAvatarUrl" class="profile-cover__avatar" :src="resolvedAvatarUrl" alt="当前头像" />
          <div v-else class="profile-cover__avatar profile-avatar-fallback" :style="avatarStyle(profileForm.nickname)">
            {{ avatarText(profileForm.nickname) }}
          </div>
          <div class="profile-cover__copy">
            <span class="page-kicker">个人主页</span>
            <h1>{{ profileForm.nickname || '未设置昵称' }}</h1>
            <p>{{ profileForm.email || '未设置邮箱' }}</p>
            <div class="profile-cover__badges">
              <span>{{ genderLabel(profileForm.gender) }}</span>
              <span>{{ authState.user?.is_active ? '账号正常' : '待确认' }}</span>
              <span v-if="authState.user?.created_at">加入于 {{ formatDate(authState.user.created_at) }}</span>
            </div>
          </div>
        </div>

        <button class="profile-edit-entry" type="button" @click="showEditModal = true">编辑账号信息</button>
      </section>

      <section class="profile-stats-row" :aria-busy="homeLoading">
        <button class="profile-stat-tile" type="button" @click="activeRelationTab = 'followers'">
          <span>粉丝</span>
          <strong>{{ profileHome?.follower_count ?? 0 }}</strong>
        </button>
        <button class="profile-stat-tile" type="button" @click="activeRelationTab = 'following'">
          <span>关注</span>
          <strong>{{ profileHome?.following_count ?? 0 }}</strong>
        </button>
        <div class="profile-stat-tile">
          <span>发布动态</span>
          <strong>{{ profileHome?.post_count ?? 0 }}</strong>
        </div>
      </section>

      <section class="profile-home-grid">
        <div class="profile-main-column">
          <div class="profile-section-head">
            <div>
              <h2>我的旅行动态</h2>
              <p>以第一张图片和正文摘要展示，适合快速回看自己的分享。</p>
            </div>
            <a-button :loading="homeLoading" @click="loadProfileHome">刷新主页</a-button>
          </div>

          <a-spin :spinning="homeLoading">
            <a-empty v-if="!profilePosts.length" description="你还没有发布旅行动态" />
            <div v-else class="profile-post-grid">
              <article v-for="post in profilePosts" :key="post.id" class="profile-post-card">
                <div class="profile-post-card__image">
                  <img v-if="post.image_urls.length" :src="resolveMediaUrl(post.image_urls[0])" :alt="`${post.author_name} 的旅行动态图片`" />
                  <div v-else class="profile-post-card__placeholder">{{ post.city || '旅行动态' }}</div>
                </div>
                <div class="profile-post-card__body">
                  <div class="profile-post-card__meta">
                    <span>{{ formatDate(post.created_at) }}</span>
                    <span v-if="post.city">{{ post.city }}</span>
                  </div>
                  <p>{{ post.content }}</p>
                  <div class="profile-post-card__footer">
                    <span>喜欢 {{ post.like_count }}</span>
                    <span>评论 {{ post.comment_count }}</span>
                  </div>
                  <div v-if="post.tags.length" class="profile-post-card__tags">
                    <span v-for="tag in post.tags.slice(0, 3)" :key="`${post.id}-${tag}`">{{ tag }}</span>
                  </div>
                </div>
              </article>
            </div>
          </a-spin>
        </div>

        <aside class="profile-side-column">
          <div class="profile-section-head profile-section-head--compact">
            <div>
              <h2>社交关系</h2>
              <p>查看关注你的人和你关注的作者。</p>
            </div>
          </div>

          <a-tabs v-model:activeKey="activeRelationTab">
            <a-tab-pane key="followers" tab="关注我的人">
              <div v-if="followers.length" class="profile-user-list">
                <article v-for="user in followers" :key="`follower-${user.id}`" class="profile-user-row">
                  <img v-if="user.avatar_url" :src="resolveMediaUrl(user.avatar_url)" :alt="`${user.nickname} 的头像`" />
                  <div v-else class="profile-user-row__avatar" :style="avatarStyle(user.nickname)">{{ avatarText(user.nickname) }}</div>
                  <div>
                    <strong>{{ user.nickname }}</strong>
                    <p>{{ genderLabel(user.gender) }}</p>
                  </div>
                </article>
              </div>
              <a-empty v-else description="暂时还没有粉丝" />
            </a-tab-pane>
            <a-tab-pane key="following" tab="我关注的人">
              <div v-if="following.length" class="profile-user-list">
                <article v-for="user in following" :key="`following-${user.id}`" class="profile-user-row">
                  <img v-if="user.avatar_url" :src="resolveMediaUrl(user.avatar_url)" :alt="`${user.nickname} 的头像`" />
                  <div v-else class="profile-user-row__avatar" :style="avatarStyle(user.nickname)">{{ avatarText(user.nickname) }}</div>
                  <div>
                    <strong>{{ user.nickname }}</strong>
                    <p>{{ genderLabel(user.gender) }}</p>
                  </div>
                </article>
              </div>
              <a-empty v-else description="你还没有关注其他作者" />
            </a-tab-pane>
          </a-tabs>
        </aside>
      </section>

      <a-modal
        v-model:open="showEditModal"
        title="编辑账号信息"
        width="760px"
        :footer="null"
      >
        <div class="profile-edit-panel">
          <section>
            <h3>基础信息</h3>
            <a-form layout="vertical">
              <a-form-item label="头像">
                <div class="profile-avatar-editor">
                  <img v-if="resolvedAvatarUrl" class="profile-avatar-preview" :src="resolvedAvatarUrl" alt="头像预览" />
                  <div v-else class="profile-avatar-preview profile-avatar-fallback" :style="avatarStyle(profileForm.nickname)">
                    {{ avatarText(profileForm.nickname) }}
                  </div>
                  <div class="profile-avatar-actions">
                    <p>上传本地图片后，社区动态和评论里会同步展示。</p>
                    <input
                      ref="avatarInputRef"
                      class="profile-avatar-input"
                      type="file"
                      accept="image/*"
                      @change="handleAvatarFile"
                    />
                    <a-button :loading="avatarLoading" @click="openAvatarPicker">选择头像图片</a-button>
                  </div>
                </div>
              </a-form-item>
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
              <a-form-item label="性别">
                <a-select v-model:value="profileForm.gender" placeholder="请选择性别" allow-clear>
                  <a-select-option value="female">女</a-select-option>
                  <a-select-option value="male">男</a-select-option>
                  <a-select-option value="other">其他</a-select-option>
                  <a-select-option value="private">不展示</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item>
                <a-button type="primary" :loading="profileLoading" @click="saveProfile">保存个人信息</a-button>
              </a-form-item>
            </a-form>
          </section>

          <section>
            <h3>修改密码</h3>
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

          <section class="profile-danger-zone">
            <h3>账号管理</h3>
            <p>注销后，账号信息、旅行轨迹、反馈和记忆数据都会被永久删除。</p>
            <a-button danger :loading="deleteLoading" @click="deleteAccount">注销账号</a-button>
          </section>
        </div>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import {
  changeAccountPassword,
  deleteCurrentAccount,
  getCurrentUser,
  getMyCommunityProfile,
  resolveMediaUrl,
  updateAccountProfile,
  uploadAccountAvatar,
} from '@/services/api'
import type { CommunityPost, CommunityProfileHomeData, CommunityUserSummary } from '@/types'
import { clearAuthSession, updateStoredUser, useAuthState } from '@/utils/auth'
import { avatarStyle, avatarText } from '@/utils/avatar'

const router = useRouter()
const authState = useAuthState()
const profileLoading = ref(false)
const avatarLoading = ref(false)
const passwordLoading = ref(false)
const deleteLoading = ref(false)
const homeLoading = ref(false)
const showEditModal = ref(false)
const activeRelationTab = ref('followers')
const confirmNewPassword = ref('')
const avatarInputRef = ref<HTMLInputElement | null>(null)
const profileHome = ref<CommunityProfileHomeData | null>(null)

const profileForm = reactive({
  nickname: '',
  email: '',
  avatarUrl: '',
  gender: '',
})

const resolvedAvatarUrl = computed(() => resolveMediaUrl(profileForm.avatarUrl))
const profilePosts = computed<CommunityPost[]>(() => profileHome.value?.posts || [])
const followers = computed<CommunityUserSummary[]>(() => profileHome.value?.followers || [])
const following = computed<CommunityUserSummary[]>(() => profileHome.value?.following || [])

const passwordForm = reactive({
  current_password: '',
  new_password: '',
})

const hydrateFromUser = (user: NonNullable<typeof authState.user>) => {
  profileForm.nickname = user.nickname
  profileForm.email = user.email
  profileForm.avatarUrl = user.avatar_url || ''
  profileForm.gender = user.gender || ''
}

onMounted(async () => {
  if (authState.user) {
    hydrateFromUser(authState.user)
  } else {
    await loadCurrentUser()
  }
  await loadProfileHome()
})

const loadCurrentUser = async () => {
  try {
    const response = await getCurrentUser()
    if (response.success && response.data) {
      updateStoredUser(response.data)
      hydrateFromUser(response.data)
    }
  } catch (error: any) {
    message.error(error.message || '获取用户信息失败')
  }
}

const loadProfileHome = async () => {
  homeLoading.value = true
  try {
    const response = await getMyCommunityProfile()
    if (!response.success || !response.data) {
      throw new Error(response.message || '获取个人主页失败')
    }
    profileHome.value = response.data
  } catch (error: any) {
    message.error(error.message || '获取个人主页失败')
  } finally {
    homeLoading.value = false
  }
}

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
      gender: profileForm.gender || '',
    })
    if (!response.success || !response.data) {
      throw new Error(response.message || '更新失败')
    }
    updateStoredUser(response.data)
    hydrateFromUser(response.data)
    await loadProfileHome()
    message.success('个人信息已更新')
  } catch (error: any) {
    message.error(error.message || '更新失败')
  } finally {
    profileLoading.value = false
  }
}

const openAvatarPicker = () => {
  avatarInputRef.value?.click()
}

const handleAvatarFile = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const [file] = Array.from(target.files || [])
  target.value = ''
  if (!file) return

  avatarLoading.value = true
  try {
    const response = await uploadAccountAvatar(file)
    if (!response.success || !response.data) {
      throw new Error(response.message || '上传头像失败')
    }
    updateStoredUser(response.data)
    hydrateFromUser(response.data)
    await loadProfileHome()
    message.success('头像已更新')
  } catch (error: any) {
    message.error(error.message || '上传头像失败')
  } finally {
    avatarLoading.value = false
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

const genderLabel = (value?: string) => {
  const labels: Record<string, string> = {
    female: '女',
    male: '男',
    other: '其他',
    private: '不展示性别',
  }
  return labels[value || ''] || '未设置性别'
}

const formatDate = (value?: string) => {
  if (!value) return '未知时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}
</script>

<style scoped>
.profile-home {
  display: grid;
  gap: 22px;
}

.profile-cover {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding: 34px;
  border: 1px solid rgba(71, 153, 136, 0.24);
  border-radius: 8px;
  background:
    linear-gradient(120deg, rgba(242, 250, 247, 0.96), rgba(232, 244, 255, 0.9)),
    #f7fbff;
  box-shadow: 0 22px 52px rgba(61, 118, 139, 0.14);
}

.profile-cover__identity {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 20px;
}

.profile-cover__avatar,
.profile-avatar-fallback {
  width: 112px;
  height: 112px;
  flex: 0 0 auto;
  border-radius: 8px;
}

.profile-cover__avatar {
  object-fit: cover;
  display: block;
  border: 4px solid #ffffff;
}

.profile-avatar-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 34px;
  font-weight: 800;
}

.profile-cover__copy {
  min-width: 0;
  display: grid;
  gap: 8px;
}

.profile-cover__copy h1 {
  margin: 0;
  overflow-wrap: anywhere;
  color: #17324f;
  font-size: 38px;
  line-height: 1.15;
}

.profile-cover__copy p {
  margin: 0;
  color: #64748b;
  font-size: 16px;
}

.profile-cover__badges,
.profile-post-card__tags,
.profile-post-card__footer,
.profile-post-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.profile-cover__badges span,
.profile-post-card__tags span {
  padding: 5px 9px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  color: #315067;
  font-size: 13px;
  font-weight: 700;
}

.profile-edit-entry {
  min-height: 42px;
  padding: 0 18px;
  border: 0;
  border-radius: 8px;
  background: #21756b;
  color: #ffffff;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(33, 117, 107, 0.22);
}

.profile-edit-entry:hover {
  background: #185f58;
}

.profile-stats-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.profile-stat-tile {
  min-height: 108px;
  display: grid;
  align-content: center;
  gap: 8px;
  padding: 18px;
  border: 1px solid rgba(82, 138, 208, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  color: #17324f;
  text-align: left;
  box-shadow: 0 16px 36px rgba(82, 138, 208, 0.12);
}

button.profile-stat-tile {
  cursor: pointer;
}

.profile-stat-tile span {
  color: #64748b;
  font-weight: 700;
}

.profile-stat-tile strong {
  font-size: 34px;
  line-height: 1;
}

.profile-home-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 22px;
  align-items: start;
}

.profile-main-column,
.profile-side-column,
.profile-edit-panel {
  display: grid;
  gap: 18px;
}

.profile-main-column,
.profile-side-column {
  padding: 24px;
  border: 1px solid rgba(82, 138, 208, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 16px 36px rgba(82, 138, 208, 0.12);
}

.profile-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.profile-section-head--compact {
  display: block;
}

.profile-section-head h2,
.profile-edit-panel h3 {
  margin: 0;
  color: #17324f;
}

.profile-section-head p,
.profile-edit-panel p,
.profile-user-row p {
  margin: 6px 0 0;
  color: #64748b;
  line-height: 1.6;
}

.profile-post-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.profile-post-card {
  overflow: hidden;
  border: 1px solid rgba(82, 138, 208, 0.2);
  border-radius: 8px;
  background: #ffffff;
}

.profile-post-card__image {
  aspect-ratio: 1;
  background: #e7f3ff;
}

.profile-post-card__image img,
.profile-post-card__placeholder {
  width: 100%;
  height: 100%;
}

.profile-post-card__image img {
  display: block;
  object-fit: cover;
}

.profile-post-card__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: #315067;
  font-weight: 800;
  text-align: center;
}

.profile-post-card__body {
  display: grid;
  gap: 10px;
  padding: 14px;
}

.profile-post-card__body p {
  min-height: 48px;
  margin: 0;
  overflow: hidden;
  color: #2f4156;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.profile-post-card__meta,
.profile-post-card__footer {
  color: #8a99aa;
  font-size: 13px;
  font-weight: 700;
}

.profile-user-list {
  display: grid;
  gap: 12px;
}

.profile-user-row {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid rgba(71, 153, 136, 0.18);
  border-radius: 8px;
  background: rgba(247, 251, 255, 0.9);
}

.profile-user-row img,
.profile-user-row__avatar {
  width: 46px;
  height: 46px;
  border-radius: 8px;
}

.profile-user-row img {
  display: block;
  object-fit: cover;
}

.profile-user-row__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
}

.profile-user-row strong {
  display: block;
  overflow: hidden;
  color: #17324f;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-edit-panel section {
  padding: 18px;
  border: 1px solid rgba(82, 138, 208, 0.18);
  border-radius: 8px;
  background: rgba(247, 251, 255, 0.86);
}

.profile-avatar-editor {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.84);
}

.profile-avatar-preview {
  width: 86px;
  height: 86px;
  border-radius: 8px;
  object-fit: cover;
  display: block;
}

.profile-avatar-actions {
  display: grid;
  gap: 10px;
}

.profile-avatar-input {
  display: none;
}

.profile-danger-zone {
  border-color: rgba(220, 38, 38, 0.2) !important;
  background: rgba(255, 245, 245, 0.9) !important;
}

@media (max-width: 1100px) {
  .profile-home-grid,
  .profile-post-grid {
    grid-template-columns: 1fr 1fr;
  }

  .profile-side-column {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .profile-cover,
  .profile-section-head {
    display: grid;
  }

  .profile-cover__identity {
    display: grid;
  }

  .profile-stats-row,
  .profile-home-grid,
  .profile-post-grid {
    grid-template-columns: 1fr;
  }

  .profile-cover {
    padding: 22px;
  }

  .profile-cover__copy h1 {
    font-size: 30px;
  }
}
</style>
