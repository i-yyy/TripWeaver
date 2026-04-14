import { createRouter, createWebHistory } from 'vue-router'

import Community from '@/views/Community.vue'
import CommunityCardDetail from '@/views/CommunityCardDetail.vue'
import CollabTripDetail from '@/views/CollabTripDetail.vue'
import CollabTrips from '@/views/CollabTrips.vue'
import Home from '@/views/Home.vue'
import KBEval from '@/views/KBEval.vue'
import Landing from '@/views/Landing.vue'
import Login from '@/views/Login.vue'
import Profile from '@/views/Profile.vue'
import Register from '@/views/Register.vue'
import Result from '@/views/Result.vue'
import Tracks from '@/views/Tracks.vue'
import { isAuthenticated, useAuthState } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Community', component: Community },
    { path: '/community/cards/:cardId', name: 'CommunityCardDetail', component: CommunityCardDetail },
    { path: '/landing', name: 'Landing', component: Landing },
    { path: '/login', name: 'Login', component: Login, meta: { publicOnly: true } },
    { path: '/register', name: 'Register', component: Register, meta: { publicOnly: true } },
    { path: '/planner', name: 'Planner', component: Home, meta: { requiresAuth: true } },
    { path: '/result', name: 'Result', component: Result, meta: { requiresAuth: true } },
    { path: '/collab', name: 'CollabTrips', component: CollabTrips, meta: { requiresAuth: true } },
    { path: '/collab/:tripId', name: 'CollabTripDetail', component: CollabTripDetail, meta: { requiresAuth: true } },
    { path: '/profile', name: 'Profile', component: Profile, meta: { requiresAuth: true } },
    { path: '/tracks', name: 'Tracks', component: Tracks, meta: { requiresAuth: true } },
    { path: '/kb-eval', name: 'KBEval', component: KBEval, meta: { requiresAuth: true, requiresDeveloper: true } },
  ],
})

router.beforeEach((to) => {
  const authed = isAuthenticated()
  const authState = useAuthState()
  if (to.meta.requiresAuth && !authed) {
    return '/login'
  }
  if (to.meta.requiresDeveloper && authState.user?.is_developer === false) {
    return '/planner'
  }
  if (to.meta.publicOnly && authed && to.path !== '/') {
    return '/'
  }
  return true
})

export default router
