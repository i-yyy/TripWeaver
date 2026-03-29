<template>
  <div id="app-shell">
    <a-layout class="app-layout">
      <a-layout-header class="app-header">
        <div class="brand" @click="goBrandHome">智能旅行助手</div>
        <a-space wrap>
          <template v-if="authenticated">
            <a-button type="text" class="nav-btn" @click="goPlanner">旅行规划</a-button>
            <a-button type="text" class="nav-btn" @click="goTracks">我的旅行轨迹</a-button>
            <a-button type="text" class="nav-btn" @click="goProfile">个人设置</a-button>
            <a-button @click="logout">退出登录</a-button>
          </template>
          <template v-else>
            <a-button type="text" class="nav-btn" @click="goLogin">登录</a-button>
            <a-button type="primary" @click="goRegister">注册</a-button>
          </template>
        </a-space>
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

const goBrandHome = () => router.push(authenticated.value ? '/planner' : '/')
const goPlanner = () => router.push('/planner')
const goTracks = () => router.push('/tracks')
const goProfile = () => router.push('/profile')

const goLogin = () => {
  if (route.path !== '/login') {
    router.push('/login')
  }
}

const goRegister = () => {
  if (route.path !== '/register') {
    router.push('/register')
  }
}

const logout = () => {
  clearAuthSession()
  sessionStorage.removeItem('tripPlan')
  sessionStorage.removeItem('tripPlannerSessionId')
  router.push('/login')
}
</script>

<style>
#app-shell,
body,
html {
  margin: 0;
  min-height: 100%;
}

body {
  background: #f4f7fb;
}

#app {
  min-height: 100vh;
}

.app-layout {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(255, 205, 163, 0.55), transparent 30%),
    radial-gradient(circle at bottom right, rgba(107, 170, 255, 0.28), transparent 28%),
    linear-gradient(180deg, #f7f4ef 0%, #eef3fb 100%);
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  background: rgba(18, 37, 63, 0.92);
  backdrop-filter: blur(10px);
}

.brand {
  color: #fff3dd;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
}

.nav-btn {
  color: #f6f8fb !important;
}

.app-content {
  padding: 0;
}
</style>
