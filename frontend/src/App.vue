<template>
  <div id="app">
    <a-layout style="min-height: 100vh">
      <a-layout-header class="top-header">
        <div class="brand">
          HelloAgents 智能旅行助手
        </div>
        <a-space>
          <router-link to="/">
            <a-button :type="route.path === '/' ? 'primary' : 'default'">行程规划</a-button>
          </router-link>
          <router-link to="/kb-eval">
            <a-button :type="route.path === '/kb-eval' ? 'primary' : 'default'">RAG评测</a-button>
          </router-link>
        </a-space>
      </a-layout-header>
      <a-layout-content style="padding: 24px">
        <router-view />
      </a-layout-content>
      <a-layout-footer style="text-align: center">
        HelloAgents 智能旅行助手 ©2026
      </a-layout-footer>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
}

.top-header {
  background: #0a1e3a;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  color: #ffffff;
  font-size: 22px;
  font-weight: 700;
}
</style>
