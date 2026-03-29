<template>
  <div class="landing-page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">旅行灵感发动机</p>
        <h1>智能旅行助手</h1>
        <p class="lead">
          想去哪、怎么玩、住哪里、吃什么，全都可以交给我们来排兵布阵。
          你负责心动，我们负责把旅程安排得顺路、顺心、顺手出发。
        </p>
      </div>
      <div class="action-grid">
        <button class="action-card register-card" @click="goRegister">
          <span class="action-label">注册</span>
          <span class="action-desc">第一次来？先建一个专属旅行身份，把偏好和轨迹都留住。</span>
        </button>
        <button class="action-card login-card" @click="goLogin">
          <span class="action-label">登录</span>
          <span class="action-desc">回来继续规划下一站，让画像、记忆和历史行程接着为你服务。</span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goRegister = () => router.push('/register')
const goLogin = () => router.push('/login')
</script>

<style scoped>
.landing-page {
  min-height: calc(100vh - 64px);
  padding: 48px 24px;
}

.hero {
  max-width: 1200px;
  margin: 0 auto;
  padding: 56px;
  border-radius: 32px;
  background:
    linear-gradient(135deg, rgba(15, 40, 70, 0.94), rgba(25, 88, 132, 0.88)),
    linear-gradient(160deg, #d7e8ff 0%, #fef5e8 100%);
  color: #fefaf1;
  box-shadow: 0 28px 70px rgba(24, 45, 74, 0.22);
}

.hero-copy {
  max-width: 720px;
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 14px;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: #ffd89a;
}

h1 {
  margin: 0;
  font-size: clamp(44px, 8vw, 88px);
  line-height: 0.95;
  font-weight: 800;
}

.lead {
  max-width: 640px;
  margin: 20px 0 0;
  font-size: 18px;
  line-height: 1.8;
  color: rgba(253, 247, 237, 0.9);
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-top: 40px;
}

.action-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 220px;
  padding: 28px;
  border: none;
  border-radius: 24px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(15, 29, 48, 0.2);
}

.register-card {
  background: linear-gradient(135deg, #ffe8cb, #fff7ef);
  color: #53361d;
}

.login-card {
  background: linear-gradient(135deg, #d6ebff, #eff7ff);
  color: #173a62;
}

.action-label {
  font-size: 30px;
  font-weight: 700;
}

.action-desc {
  font-size: 16px;
  line-height: 1.8;
}

@media (max-width: 900px) {
  .hero {
    padding: 28px;
  }

  .action-grid {
    grid-template-columns: 1fr;
  }
}
</style>
