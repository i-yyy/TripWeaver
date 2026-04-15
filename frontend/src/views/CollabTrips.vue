<template>
  <div class="brand-page">
    <div class="brand-shell collab-page">
      <section class="collab-hero">
        <div>
          <span class="page-kicker">协同行程</span>
          <h1>和好友一起把路线改到大家都满意</h1>
          <p>从已生成的旅行轨迹创建协同空间，邀请好友加入，一起编辑、评论、投票并留下修改记录。</p>
        </div>
        <a-button type="primary" size="large" @click="showCreateModal = true">创建协同行程</a-button>
      </section>

      <section v-if="pendingInvites.length" class="collab-panel">
        <div class="collab-section-head">
          <div>
            <h2>待处理邀请</h2>
            <p>好友邀请你一起编辑的旅行计划。</p>
          </div>
        </div>
        <div class="collab-invite-list">
          <article v-for="invite in pendingInvites" :key="invite.id" class="collab-invite-card">
            <div>
              <strong>{{ invite.trip_title || '协同行程' }}</strong>
              <p>{{ invite.city || '目的地待确认' }} · {{ roleLabel(invite.role) }} · 来自 {{ invite.inviter?.nickname || '旅行者' }}</p>
            </div>
            <div class="collab-card-actions">
              <a-button type="primary" :loading="handlingInviteId === invite.id" @click="handleInvite(invite.id, 'accept')">接受</a-button>
              <a-button :loading="handlingInviteId === invite.id" @click="handleInvite(invite.id, 'reject')">拒绝</a-button>
            </div>
          </article>
        </div>
      </section>

      <section class="collab-panel">
        <div class="collab-section-head">
          <div>
            <h2>我的协同行程</h2>
            <p>包含你创建的行程，以及好友邀请你参与的行程。</p>
          </div>
          <a-button :loading="loading" @click="loadTrips">刷新</a-button>
        </div>

        <a-spin :spinning="loading">
          <a-empty v-if="!trips.length" description="还没有协同行程，可以先从旅行轨迹创建一份" />
          <div v-else class="collab-trip-grid">
            <article v-for="trip in trips" :key="trip.id" class="collab-trip-card" @click="openTrip(trip.id)">
              <div class="collab-trip-card__top">
                <span>{{ trip.city || '旅行计划' }}</span>
                <strong>v{{ trip.version }}</strong>
              </div>
              <h3>{{ trip.title }}</h3>
              <p>{{ trip.start_date }} - {{ trip.end_date }}</p>
              <div class="collab-trip-card__meta">
                <span>{{ roleLabel(trip.my_role) }}</span>
                <span>{{ trip.member_count }} 位成员</span>
                <span>{{ trip.comment_count }} 条讨论</span>
              </div>
              <div class="collab-trip-card__footer">
                <span>管理员：{{ trip.owner.nickname }}</span>
                <button
                  type="button"
                  class="collab-trip-card__danger"
                  :disabled="deletingTripId === trip.id"
                  @click.stop="removeTrip(trip)"
                >
                  {{ trip.my_role === 'owner' ? '删除' : '退出' }}
                </button>
              </div>
            </article>
          </div>
        </a-spin>
      </section>

      <a-modal
        v-model:open="showCreateModal"
        title="创建协同行程"
        :confirm-loading="creating"
        ok-text="创建"
        cancel-text="取消"
        @ok="createTrip"
      >
        <a-form layout="vertical">
          <a-form-item label="选择本地旅行规划">
            <a-select
              v-model:value="createForm.sourceTrackId"
              placeholder="请选择一条已生成的旅行轨迹"
              :loading="trackLoading"
              :not-found-content="trackLoading ? '正在加载旅行轨迹...' : '暂无旅行轨迹，请先生成旅行规划'"
            >
              <a-select-option v-for="track in tracks" :key="track.id" :value="track.id">
                {{ track.city }} · {{ track.start_date }} - {{ track.end_date }}
              </a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="协同行程标题">
            <a-input v-model:value="createForm.title" placeholder="例如：五一杭州好友共创路线" />
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { createCollabTrip, deleteCollabTrip, getCollabTrips, getTravelTracks, respondCollabInvite } from '@/services/api'
import type { CollabTripInvite, CollabTripSummary, TravelTrackItem } from '@/types'

const router = useRouter()
const loading = ref(false)
const trackLoading = ref(false)
const creating = ref(false)
const showCreateModal = ref(false)
const handlingInviteId = ref('')
const deletingTripId = ref('')
const trips = ref<CollabTripSummary[]>([])
const pendingInvites = ref<CollabTripInvite[]>([])
const tracks = ref<TravelTrackItem[]>([])

const createForm = reactive({
  sourceTrackId: undefined as string | undefined,
  title: '',
})

onMounted(async () => {
  await Promise.all([loadTrips(), loadTracks()])
})

const loadTrips = async () => {
  loading.value = true
  try {
    const response = await getCollabTrips()
    trips.value = response.data || []
    pendingInvites.value = response.pending_invites || []
  } catch (error: any) {
    message.error(error.message || '获取协同行程失败')
  } finally {
    loading.value = false
  }
}

const loadTracks = async () => {
  trackLoading.value = true
  try {
    const response = await getTravelTracks()
    tracks.value = response.data || []
  } catch (error: any) {
    message.error(error.message || '获取旅行轨迹失败')
  } finally {
    trackLoading.value = false
  }
}

const createTrip = async () => {
  if (!createForm.sourceTrackId) {
    message.error('请选择一条旅行轨迹')
    return
  }
  creating.value = true
  try {
    const response = await createCollabTrip({
      source_track_id: createForm.sourceTrackId,
      title: createForm.title.trim(),
    })
    if (!response.success || !response.data) {
      throw new Error(response.message || '创建协同行程失败')
    }
    message.success('协同行程已创建')
    showCreateModal.value = false
    createForm.sourceTrackId = undefined
    createForm.title = ''
    router.push({ name: 'CollabTripDetail', params: { tripId: response.data.id } })
  } catch (error: any) {
    message.error(error.message || '创建协同行程失败')
  } finally {
    creating.value = false
  }
}

const handleInvite = async (inviteId: string, action: 'accept' | 'reject') => {
  handlingInviteId.value = inviteId
  try {
    await respondCollabInvite(inviteId, action)
    message.success(action === 'accept' ? '已接受邀请' : '已拒绝邀请')
    await loadTrips()
  } catch (error: any) {
    message.error(error.message || '处理邀请失败')
  } finally {
    handlingInviteId.value = ''
  }
}

const openTrip = (tripId: string) => {
  router.push({ name: 'CollabTripDetail', params: { tripId } })
}

const removeTrip = async (trip: CollabTripSummary) => {
  const actionText = trip.my_role === 'owner' ? '删除' : '退出'
  const confirmed = window.confirm(`确定要${actionText}「${trip.title}」吗？`)
  if (!confirmed) return
  deletingTripId.value = trip.id
  try {
    await deleteCollabTrip(trip.id)
    message.success(trip.my_role === 'owner' ? '协同行程已删除' : '已退出协同行程')
    await loadTrips()
  } catch (error: any) {
    message.error(error.message || `${actionText}失败`)
  } finally {
    deletingTripId.value = ''
  }
}

const roleLabel = (role: string) => {
  const labels: Record<string, string> = {
    owner: '管理员',
    editor: '可编辑',
    viewer: '仅查看',
  }
  return labels[role] || role
}

</script>

<style scoped>
.collab-page {
  display: grid;
  gap: 24px;
}

.collab-hero,
.collab-panel {
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 24px 60px rgba(65, 110, 168, 0.14);
  backdrop-filter: blur(18px);
}

.collab-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 42px;
  background: #eaf5ff;
  overflow: hidden;
}

.collab-hero h1 {
  margin: 8px 0;
  color: var(--brand-text);
  font-size: 42px;
  line-height: 1.15;
  letter-spacing: 0;
}

.collab-hero p,
.collab-section-head p,
.collab-trip-card p,
.collab-invite-card p {
  margin: 0;
  color: var(--brand-muted);
  line-height: 1.7;
}

.collab-panel {
  padding: 26px;
}

.collab-section-head,
.collab-invite-card,
.collab-trip-card__top,
.collab-trip-card__footer,
.collab-card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.collab-section-head {
  margin-bottom: 18px;
}

.collab-section-head h2,
.collab-trip-card h3 {
  margin: 0;
  color: #111111;
  font-weight: 800;
}

.collab-invite-list,
.collab-trip-grid {
  display: grid;
  gap: 14px;
}

.collab-invite-card,
.collab-trip-card {
  border: 1px solid rgba(191, 214, 239, 0.76);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 18px 38px rgba(77, 122, 181, 0.12);
}

.collab-invite-card {
  padding: 16px;
}

.collab-trip-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.collab-trip-card {
  display: grid;
  gap: 12px;
  min-height: 210px;
  padding: 18px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.collab-trip-card:hover {
  border-color: rgba(45, 134, 231, 0.42);
  transform: translateY(-4px);
  box-shadow: 0 24px 44px rgba(77, 122, 181, 0.16);
}

.collab-trip-card__top span,
.collab-trip-card__top strong,
.collab-trip-card__meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(45, 134, 231, 0.12);
  color: #1d5d9b;
  font-size: 13px;
  font-weight: 800;
}

.collab-trip-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.collab-trip-card__footer {
  color: #5f7893;
  font-size: 13px;
  font-weight: 700;
}

.collab-trip-card__danger {
  padding: 4px 8px;
  border: 1px solid rgba(220, 38, 38, 0.28);
  border-radius: 999px;
  background: rgba(255, 245, 245, 0.95);
  color: #b42318;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

@media (max-width: 1050px) {
  .collab-trip-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .collab-hero,
  .collab-section-head,
  .collab-invite-card {
    display: grid;
  }

  .collab-trip-grid {
    grid-template-columns: 1fr;
  }
}
</style>
