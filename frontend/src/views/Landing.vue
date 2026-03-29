<template>
  <div class="brand-page landing-page">
    <section class="brand-shell glass-panel landing-hero">
      <header class="landing-nav">
        <div class="landing-nav__pill">
          <div class="landing-brand">
            <span class="landing-brand__badge">旅</span>
            <span class="landing-brand__name">智能旅行助手</span>
          </div>
          <span class="landing-nav__text">旅行规划</span>
          <span class="landing-nav__text">旅行轨迹</span>
          <span class="landing-nav__text">个人设置</span>
        </div>
      </header>

      <div class="landing-grid">
        <div class="landing-copy">
          <span class="page-kicker">灵感一来，立刻出发</span>
          <h1 class="page-title landing-title">把下一段旅行，规划成真正想去的样子</h1>
          <p class="page-subtitle landing-subtitle">
            从想去哪个城市，到住哪里、怎么玩、路线怎么排，我们都会替你认真想好。它懂你的偏好，记得你的选择，也会把每一次探索悄悄留在地图里。
          </p>

          <div class="landing-actions">
            <template v-if="authenticated">
              <button class="landing-action landing-action--primary" type="button" @click="goPlanner">进入旅行规划</button>
              <button class="landing-action landing-action--secondary" type="button" @click="goTracks">查看旅行轨迹</button>
            </template>
            <template v-else>
              <button class="landing-action landing-action--primary" type="button" @click="goLogin">登录</button>
              <button class="landing-action landing-action--secondary" type="button" @click="goRegister">注册</button>
            </template>
          </div>

          <div class="brand-stat-grid landing-stats">
            <div class="brand-stat">
              <span>智能推荐</span>
              <strong>景点、酒店、节奏一体生成</strong>
            </div>
            <div class="brand-stat">
              <span>旅行轨迹</span>
              <strong>搜索过的城市自动点亮</strong>
            </div>
            <div class="brand-stat">
              <span>个人偏好</span>
              <strong>越用越懂你想怎么旅行</strong>
            </div>
          </div>
        </div>

        <div class="landing-visual" aria-hidden="true">
          <div class="floating-card floating-card--plan">
            <strong>旅行规划</strong>
            <span>把城市灵感整理成可执行的行程</span>
          </div>
          <div class="floating-card floating-card--track">
            <strong>旅行轨迹</strong>
            <span>每一次搜索都会在地图上留下足迹</span>
          </div>
          <div class="floating-card floating-card--profile">
            <strong>个人设置</strong>
            <span>昵称、偏好、账号信息统一管理</span>
          </div>

          <div class="planet-card">
            <div class="planet-shape planet-shape--green"></div>
            <div class="planet-shape planet-shape--purple"></div>
            <div class="planet-shape planet-shape--yellow"></div>
            <div class="planet-shape planet-shape--orange"></div>
            <div class="planet-route planet-route--one"></div>
            <div class="planet-route planet-route--two"></div>
            <div class="planet-route planet-route--three"></div>
            <div class="planet-pin">行</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthState } from '@/utils/auth'

const router = useRouter()
const authState = useAuthState()
const authenticated = computed(() => Boolean(authState.token && authState.user))

const goLogin = () => router.push('/login')
const goRegister = () => router.push('/register')
const goPlanner = () => router.push('/planner')
const goTracks = () => router.push('/tracks')
</script>

<style scoped>
.landing-page {
  display: flex;
  align-items: stretch;
}

.landing-hero {
  width: 100%;
  min-height: calc(100vh - 56px);
  padding: 28px 32px 36px;
  background:
    radial-gradient(circle at left top, rgba(255, 255, 255, 0.7), transparent 30%),
    radial-gradient(circle at right 26%, rgba(255, 255, 255, 0.18), transparent 18%),
    linear-gradient(135deg, #cfe4fb 0%, #7db9f1 46%, #3c97e8 100%);
  overflow: hidden;
}

.landing-nav {
  display: flex;
  justify-content: center;
}

.landing-nav__pill {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 16px 24px;
  padding: 12px 20px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
  animation: fade-up 0.68s ease both;
}

.landing-brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #24486e;
  font-weight: 800;
}

.landing-brand__badge {
  display: inline-grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #3388e8;
  font-weight: 800;
}

.landing-brand__name {
  font-size: 22px;
}

.landing-nav__text {
  color: rgba(36, 72, 110, 0.86);
  font-size: 17px;
  font-weight: 700;
}

.landing-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.04fr) minmax(420px, 0.96fr);
  align-items: center;
  gap: 30px;
  min-height: calc(100vh - 170px);
}

.landing-copy {
  padding: 18px 10px 0 28px;
}

.landing-title {
  max-width: 620px;
  color: #ffffff;
  font-size: clamp(60px, 7vw, 96px);
  line-height: 0.95;
  text-shadow: 0 10px 24px rgba(41, 92, 145, 0.15);
}

.landing-subtitle {
  max-width: 620px;
  color: rgba(245, 249, 255, 0.96);
  font-size: 20px;
}

.landing-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 36px;
}

.landing-action {
  min-width: 148px;
  padding: 16px 28px;
  border: none;
  border-radius: 999px;
  font-size: 20px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.landing-action:hover {
  transform: translateY(-2px);
}

.landing-action--primary {
  background: rgba(255, 255, 255, 0.94);
  color: #2e75bf;
  box-shadow: 0 20px 36px rgba(45, 101, 160, 0.2);
}

.landing-action--secondary {
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.42);
}

.landing-stats {
  margin-top: 34px;
}

.landing-visual {
  position: relative;
  min-height: 640px;
  animation: fade-up 0.9s ease both;
}

.planet-card {
  position: absolute;
  right: 28px;
  top: 78px;
  width: min(46vw, 620px);
  aspect-ratio: 1;
  border: 8px solid rgba(255, 255, 255, 0.92);
  border-radius: 50%;
  background: rgba(241, 247, 252, 0.74);
  animation: float-soft 6.8s ease-in-out infinite, drift-glow 6.8s ease-in-out infinite;
}

.planet-shape,
.planet-route,
.planet-pin,
.floating-card {
  position: absolute;
}

.planet-shape {
  border-radius: 48% 52% 44% 56% / 42% 47% 53% 58%;
  opacity: 0.94;
}

.planet-shape--green {
  left: 18%;
  top: 16%;
  width: 22%;
  height: 38%;
  background: #82c681;
}

.planet-shape--purple {
  right: 16%;
  top: 20%;
  width: 16%;
  height: 14%;
  background: #b063c2;
}

.planet-shape--yellow {
  right: 28%;
  top: 40%;
  width: 20%;
  height: 30%;
  background: #f0ca4f;
}

.planet-shape--orange {
  left: 24%;
  bottom: 20%;
  width: 24%;
  height: 22%;
  background: #ff845c;
}

.planet-route {
  border: 3px dashed rgba(255, 255, 255, 0.5);
  border-color: rgba(255, 255, 255, 0.5) transparent transparent transparent;
  border-radius: 50%;
}

.planet-route--one {
  left: 18%;
  top: 22%;
  width: 52%;
  height: 34%;
  transform: rotate(8deg);
}

.planet-route--two {
  right: 14%;
  bottom: 22%;
  width: 36%;
  height: 42%;
  transform: rotate(10deg);
}

.planet-route--three {
  left: 20%;
  bottom: 20%;
  width: 52%;
  height: 18%;
  transform: rotate(8deg);
}

.planet-pin {
  left: 50%;
  top: 50%;
  display: grid;
  place-items: center;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  transform: translate(-50%, -50%);
  box-shadow: 0 18px 34px rgba(69, 123, 181, 0.16);
  color: #d94f6f;
  font-size: 32px;
  font-weight: 800;
}

.floating-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 230px;
  padding: 18px 20px;
  border-radius: 26px;
  background: rgba(244, 248, 252, 0.82);
  box-shadow: 0 18px 34px rgba(59, 109, 166, 0.14);
  backdrop-filter: blur(10px);
  animation: float-soft 5.8s ease-in-out infinite;
}

.floating-card strong {
  color: #3f6488;
  font-size: 18px;
}

.floating-card span {
  color: #7890a7;
  line-height: 1.7;
}

.floating-card--plan {
  right: 44%;
  top: 18%;
  animation-delay: 0.2s;
}

.floating-card--track {
  left: 8%;
  bottom: 22%;
  animation-delay: 1s;
}

.floating-card--profile {
  right: 4%;
  top: 28%;
  animation-delay: 1.8s;
}

@media (max-width: 1180px) {
  .landing-hero {
    padding: 24px 22px 30px;
  }

  .landing-grid {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .landing-copy {
    padding: 10px 8px 0;
  }

  .landing-visual {
    min-height: 520px;
  }

  .planet-card {
    position: relative;
    inset: auto;
    width: min(82vw, 560px);
    margin: 0 auto;
  }

  .floating-card--plan {
    right: auto;
    left: 4%;
    top: 2%;
  }

  .floating-card--track {
    left: 2%;
    bottom: 4%;
  }

  .floating-card--profile {
    right: 2%;
    top: 18%;
  }
}

@media (max-width: 760px) {
  .landing-title {
    font-size: clamp(44px, 16vw, 72px);
  }

  .landing-subtitle {
    font-size: 18px;
  }

  .landing-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .landing-visual {
    min-height: 420px;
  }

  .planet-card {
    width: min(92vw, 420px);
  }

  .floating-card {
    min-width: 0;
    padding: 14px 16px;
  }
}
</style>
