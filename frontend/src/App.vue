<template>
  <div id="app-shell">
    <a-layout class="app-layout">
      <a-layout-header v-if="showAppHeader" class="app-header">
        <div class="app-header__inner brand-shell">
          <button class="brand-button" type="button" @click="goBrandHome">智能旅行助手</button>
          <div class="app-nav">
            <template v-if="authenticated">
              <div class="account-meta">
                <span class="account-text">已登录账号：{{ authState.user?.nickname || authState.user?.email || '旅行者' }}</span>
                <span v-if="isDeveloperUser" class="developer-badge">开发者</span>
              </div>
              <a-button type="text" :class="navButtonClass('/community')" @click="goCommunity">社区交流</a-button>
              <a-button type="text" :class="navButtonClass('/planner')" @click="goPlanner">🧭 旅行规划</a-button>
              <a-button type="text" :class="navButtonClass('/tracks')" @click="goTracks">🗺️ 旅行轨迹</a-button>
              <a-button type="text" :class="navButtonClass('/collab')" @click="goCollab">🤝 协同行程</a-button>
              <a-button
                v-if="isDeveloperUser"
                type="text"
                :class="navButtonClass('/kb-eval')"
                @click="goKBEval"
              >
                🧪 RAG评测
              </a-button>
              <a-button type="text" :class="navButtonClass('/profile')" @click="goProfile">👤 个人设置</a-button>
              <a-button @click="logout">🚪 退出登录</a-button>
            </template>
            <template v-else>
              <a-button type="text" :class="navButtonClass('/login')" @click="goLogin">🔑 登录</a-button>
              <a-button type="text" :class="navButtonClass('/register')" @click="goRegister">✨ 注册</a-button>
            </template>
          </div>
        </div>
      </a-layout-header>
      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getCurrentUser } from '@/services/api'
import { clearAuthSession, updateStoredUser, useAuthState } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const authState = useAuthState()

const authenticated = computed(() => Boolean(authState.token && authState.user))
const isDeveloperUser = computed(() => authState.user?.is_developer === true)
const showAppHeader = computed(() => authenticated.value || !['/', '/login', '/register'].includes(route.path))
const navButtonClass = (path: string) => ({
  'nav-btn': true,
  'nav-btn--active': path === '/' ? route.path === '/' : route.path === path || route.path.startsWith(`${path}/`),
})

const goBrandHome = () => router.push(authenticated.value ? '/community' : '/')
const goCommunity = () => router.push('/community')
const goPlanner = () => router.push('/planner')
const goTracks = () => router.push('/tracks')
const goCollab = () => router.push('/collab')
const goKBEval = () => router.push('/kb-eval')
const goProfile = () => router.push('/profile')
const goLogin = () => router.push('/login')
const goRegister = () => router.push('/register')

const logout = () => {
  clearAuthSession()
  sessionStorage.removeItem('tripPlan')
  sessionStorage.removeItem('tripPlannerSessionId')
  sessionStorage.removeItem('tripPlannerUserId')
  router.push('/')
}

onMounted(async () => {
  if (!authenticated.value) return
  if (typeof authState.user?.is_developer === 'boolean') return
  tryRefreshCurrentUser()
})

const tryRefreshCurrentUser = async () => {
  try {
    const response = await getCurrentUser()
    if (response.success && response.data) {
      updateStoredUser(response.data)
    }
  } catch {
    // Let the auth interceptor handle invalid sessions silently.
  }
}

watch(
  () => [authenticated.value, authState.user?.id, authState.user?.is_developer] as const,
  ([isAuthed, userId, isDeveloper]) => {
    if (!isAuthed || !userId || typeof isDeveloper === 'boolean') {
      return
    }
    void tryRefreshCurrentUser()
  },
  { immediate: true },
)
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: transparent;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 40;
  height: auto;
  padding: 14px 18px 0;
  line-height: normal;
  background: transparent;
}

.app-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.58);
  box-shadow: 0 18px 44px rgba(77, 122, 181, 0.14);
  backdrop-filter: blur(16px);
}

.brand-button {
  border: none;
  background: transparent;
  color: #183453;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.04em;
  cursor: pointer;
}

.app-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.account-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.account-text {
  color: rgba(71, 89, 112, 0.78);
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.developer-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(29, 93, 155, 0.14);
  color: #1d5d9b;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.nav-btn {
  color: #264a71 !important;
  font-weight: 700;
  border-radius: 999px;
  transition: all 0.2s ease;
}

.nav-btn:hover {
  color: #183453 !important;
  background: rgba(169, 210, 255, 0.16) !important;
}

.nav-btn--active {
  color: #1d5d9b !important;
  background: rgba(169, 210, 255, 0.32) !important;
  border: 1px solid rgba(134, 186, 246, 0.55);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.24);
}

.app-content {
  padding: 0;
}

@media (max-width: 760px) {
  .app-header {
    padding: 12px 12px 0;
  }

  .app-header__inner {
    flex-direction: column;
    align-items: stretch;
    border-radius: 24px;
  }

  .app-nav {
    justify-content: center;
  }

  .account-meta {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }

  .account-text {
    width: 100%;
    text-align: center;
  }
}
</style>
