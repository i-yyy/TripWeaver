<template>
  <div id="app-shell">
    <a-layout class="app-layout">
      <a-layout-header v-if="showAppHeader" class="app-header">
        <div class="app-header__inner brand-shell">
          <button class="brand-button" type="button" @click="goBrandHome">智能旅行助手</button>
          <div class="app-nav">
            <template v-if="authenticated">
              <a-button type="text" class="nav-btn" @click="goPlanner">旅行规划</a-button>
              <a-button type="text" class="nav-btn" @click="goTracks">旅行轨迹</a-button>
              <a-button type="text" class="nav-btn" @click="goProfile">个人设置</a-button>
              <a-button @click="logout">退出登录</a-button>
            </template>
            <template v-else>
              <a-button type="text" class="nav-btn" @click="goLogin">登录</a-button>
              <a-button type="primary" @click="goRegister">注册</a-button>
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
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { clearAuthSession, useAuthState } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const authState = useAuthState()

const authenticated = computed(() => Boolean(authState.token && authState.user))
const showAppHeader = computed(() => route.path !== '/')

const goBrandHome = () => router.push('/')
const goPlanner = () => router.push('/planner')
const goTracks = () => router.push('/tracks')
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

.nav-btn {
  color: #264a71 !important;
  font-weight: 700;
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
}
</style>
