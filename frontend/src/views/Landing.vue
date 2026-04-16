<template>
  <div class="brand-page landing-page">
    <section class="brand-shell glass-panel landing-hero">
      <div class="landing-cloud landing-cloud--one" aria-hidden="true"></div>
      <div class="landing-cloud landing-cloud--two" aria-hidden="true"></div>
      <div class="landing-cloud landing-cloud--three" aria-hidden="true"></div>

      <header class="landing-nav">
        <div class="landing-nav__pill">
          <div class="landing-brand">
            <span class="landing-brand__badge">旅</span>
            <span class="landing-brand__name">智能旅行助手</span>
          </div>
          <span class="landing-nav__text">🧭 规划</span>
          <span class="landing-nav__text">🤝 陪伴</span>
          <span class="landing-nav__text">👣 足迹</span>
        </div>
      </header>

      <div class="landing-grid">
        <div class="landing-copy">
          <span class="page-kicker">✨ 灵感一来，立刻出发</span>
          <h1 class="page-title landing-title">
            <span class="landing-title__cn">云途智织</span>
            <span class="landing-title__en">TripWeaver</span>
          </h1>
          <p class="page-subtitle landing-subtitle">
            输入城市、时间和偏好，系统会结合路线、知识库和历史选择，为你生成更贴合需求的旅行方案
          </p>

          <div class="landing-actions">
            <template v-if="authenticated">
              <button class="landing-action landing-action--primary" type="button" @click="goCommunity">💬 进入社区交流</button>
              <button class="landing-action landing-action--secondary" type="button" @click="goTracks">🗺️ 查看旅行轨迹</button>
            </template>
            <template v-else>
              <button class="landing-action landing-action--primary" type="button" @click="goLogin">🔑 登录</button>
              <button class="landing-action landing-action--secondary" type="button" @click="goRegister">✨ 注册</button>
            </template>
          </div>

        </div>

        <div class="landing-visual" aria-hidden="true">
          <div class="floating-card floating-card--plan">
            <strong>🧭 智能规划中</strong>
            <span>把旅行灵感整理成清晰路线</span>
          </div>
          <div class="floating-card floating-card--track">
            <strong>👣 足迹已点亮</strong>
            <span>每一次探索都会留下旅行印记</span>
          </div>
          <div class="floating-card floating-card--profile">
            <strong>💗 偏好已记住</strong>
            <span>你的节奏和选择都会被温柔记下</span>
          </div>
          <div class="floating-card floating-card--memory">
            <strong>📌 灵感已收藏</strong>
            <span>喜欢的目的地和片刻都会慢慢积累</span>
          </div>

          <div class="planet-card">
            <div class="planet-shape planet-shape--green"></div>
            <div class="planet-shape planet-shape--purple"></div>
            <div class="planet-shape planet-shape--yellow"></div>
            <div class="planet-shape planet-shape--orange"></div>
            <div class="planet-route planet-route--one"></div>
            <div class="planet-route planet-route--two"></div>
            <div class="planet-route planet-route--three"></div>
            <div class="planet-pin" aria-label="位置标记">
              <span class="planet-pin__marker" aria-hidden="true"></span>
            </div>
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
const goCommunity = () => router.push('/community')
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
  padding: 22px 30px 28px;
  background:
    radial-gradient(circle at left top, rgba(255, 255, 255, 0.7), transparent 30%),
    radial-gradient(circle at right 26%, rgba(255, 255, 255, 0.18), transparent 18%),
    linear-gradient(135deg, #cfe4fb 0%, #7db9f1 46%, #3c97e8 100%);
  overflow: hidden;
}

.landing-nav {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
}

.landing-nav__pill {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 16px 24px;
  line-height: 1;
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
  line-height: 1;
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
  line-height: 1.1;
}

.landing-nav__text {
  color: rgba(36, 72, 110, 0.86);
  font-size: 17px;
  font-weight: 700;
  line-height: 1.2;
}

.landing-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.04fr) minmax(420px, 0.96fr);
  align-items: center;
  gap: 18px;
  min-height: calc(100vh - 170px);
}

.landing-cloud {
  position: absolute;
  z-index: 0;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(240, 247, 255, 0.8) 100%);
  box-shadow:
    0 18px 40px rgba(77, 132, 191, 0.12),
    inset 0 -8px 14px rgba(190, 215, 242, 0.28);
  pointer-events: none;
  animation: float-soft 9s ease-in-out infinite;
}

.landing-cloud::before,
.landing-cloud::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(241, 247, 255, 0.84) 100%);
}

.landing-cloud--one {
  left: 5%;
  top: 12%;
  width: 168px;
  height: 50px;
  opacity: 0.8;
}

.landing-cloud--one::before {
  left: 14px;
  bottom: 12px;
  width: 66px;
  height: 66px;
  box-shadow:
    38px -16px 0 10px rgba(255, 255, 255, 0.94),
    92px -4px 0 2px rgba(247, 251, 255, 0.9);
}

.landing-cloud--one::after {
  right: 18px;
  bottom: 10px;
  width: 58px;
  height: 58px;
  box-shadow: -42px -8px 0 6px rgba(248, 251, 255, 0.9);
}

.landing-cloud--two {
  right: 34%;
  top: 18%;
  width: 150px;
  height: 44px;
  opacity: 0.62;
  animation-delay: 1.2s;
}

.landing-cloud--two::before {
  left: 12px;
  bottom: 10px;
  width: 58px;
  height: 58px;
  box-shadow:
    32px -14px 0 8px rgba(255, 255, 255, 0.92),
    74px -3px 0 2px rgba(247, 251, 255, 0.88);
}

.landing-cloud--two::after {
  right: 14px;
  bottom: 9px;
  width: 50px;
  height: 50px;
  box-shadow: -34px -7px 0 4px rgba(248, 252, 255, 0.88);
}

.landing-cloud--three {
  right: 6%;
  bottom: 14%;
  width: 186px;
  height: 54px;
  opacity: 0.7;
  animation-delay: 2.4s;
}

.landing-cloud--three::before {
  left: 18px;
  bottom: 12px;
  width: 72px;
  height: 72px;
  box-shadow:
    42px -18px 0 12px rgba(255, 255, 255, 0.94),
    102px -5px 0 2px rgba(247, 251, 255, 0.9);
}

.landing-cloud--three::after {
  right: 18px;
  bottom: 10px;
  width: 60px;
  height: 60px;
  box-shadow: -44px -8px 0 6px rgba(248, 252, 255, 0.9);
}

.landing-copy {
  padding: 12px 4px 0 12px;
}

.landing-title {
  max-width: 620px;
  color: #ffffff;
  margin-bottom: 18px;
  line-height: 0.92;
  text-shadow: 0 10px 24px rgba(41, 92, 145, 0.15);
}

.landing-title__cn,
.landing-title__en {
  display: block;
  font-weight: 700;
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
}

.landing-title__cn {
  font-size: clamp(66px, 8vw, 108px);
  line-height: 1.02;
  letter-spacing: 0.04em;
  text-shadow:
    0 10px 24px rgba(41, 92, 145, 0.15),
    0 2px 0 rgba(255, 255, 255, 0.18);
}

.landing-title__en {
  margin-top: 10px;
  font-size: clamp(32px, 4vw, 54px);
  line-height: 1.08;
  letter-spacing: 0.08em;
  opacity: 0.94;
  text-transform: none;
}

.landing-subtitle {
  max-width: 620px;
  color: rgba(245, 249, 255, 0.96);
  font-size: 20px;
  line-height: 1.8;
}

.landing-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 56px;
}

.landing-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 148px;
  padding: 16px 28px;
  border: none;
  border-radius: 999px;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.2;
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

.landing-visual {
  position: relative;
  min-height: 640px;
  isolation: isolate;
  animation: fade-up 0.9s ease both;
}

.planet-card {
  position: absolute;
  right: 18px;
  top: 50%;
  translate: 0 -50%;
  width: min(46vw, 620px);
  aspect-ratio: 1;
  z-index: 1;
  border: 8px solid #ffffff;
  border-radius: 50%;
  background: #e6f2ff;
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
  opacity: 1;
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
  overflow: visible;
  z-index: 2;
}

.planet-pin__marker {
  position: relative;
  width: 34px;
  height: 34px;
  border-radius: 50% 50% 50% 0;
  background: linear-gradient(180deg, #ff6d80 0%, #e25168 100%);
  box-shadow: 0 10px 18px rgba(226, 82, 108, 0.28);
  transform: rotate(-45deg);
}

.planet-pin__marker::before {
  content: "";
  position: absolute;
  inset: 9px;
  border-radius: 50%;
  background: #ffffff;
}

.planet-pin::before,
.planet-pin::after {
  content: "";
  position: absolute;
  inset: -10px;
  border: 3px solid rgba(226, 82, 108, 0.42);
  border-radius: 50%;
  pointer-events: none;
  animation: pin-ripple 2.8s ease-out infinite;
}

.planet-pin::after {
  animation-delay: 1.4s;
}

.floating-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 2;
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
  line-height: 1.3;
}

.floating-card span {
  color: #7890a7;
  line-height: 1.65;
}

.floating-card--plan {
  left: 2%;
  top: 18%;
  animation-delay: 0.2s;
}

.floating-card--track {
  left: 6%;
  bottom: 16%;
  animation-delay: 1s;
}

.floating-card--profile {
  right: 0;
  bottom: 14%;
  animation-delay: 1.8s;
}

.floating-card--memory {
  right: 6%;
  top: 10%;
  animation-delay: 2.4s;
}

@media (max-width: 1180px) {
  .landing-cloud--one {
    left: 2%;
    top: 10%;
    width: 150px;
    height: 46px;
  }

  .landing-cloud--two {
    right: 28%;
    top: 16%;
    width: 134px;
    height: 40px;
  }

  .landing-cloud--three {
    right: 2%;
    bottom: 10%;
    width: 162px;
    height: 48px;
  }

  .landing-hero {
    padding: 20px 20px 24px;
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
    right: auto;
    top: auto;
    translate: none;
    width: min(82vw, 560px);
    margin: 0 auto;
  }

  .floating-card--plan {
    left: 0;
    top: 8%;
  }

  .floating-card--track {
    left: 2%;
    bottom: 4%;
  }

  .floating-card--profile {
    right: 0;
    top: auto;
    bottom: 14%;
  }

  .floating-card--memory {
    right: 2%;
    top: 2%;
  }
}

@media (max-width: 760px) {
  .landing-cloud--one {
    left: 4%;
    top: 11%;
    width: 118px;
    height: 36px;
  }

  .landing-cloud--two {
    right: 10%;
    top: 24%;
    width: 108px;
    height: 32px;
  }

  .landing-cloud--three {
    right: 4%;
    bottom: 6%;
    width: 128px;
    height: 38px;
  }

  .landing-title__cn {
    font-size: clamp(46px, 16vw, 72px);
  }

  .landing-title__en {
    font-size: clamp(24px, 8vw, 34px);
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

@keyframes pin-ripple {
  0% {
    opacity: 0.72;
    transform: scale(0.9);
  }

  70% {
    opacity: 0.18;
  }

  100% {
    opacity: 0;
    transform: scale(1.9);
  }
}
</style>
