<template>
  <div class="brand-page">
    <div class="brand-shell tracks-shell">
      <section class="glass-panel tracks-hero-panel">
        <div class="section-heading">
          <span class="page-kicker">我的旅行轨迹</span>
          <h1 class="page-title tracks-title">把每一次搜索过的城市，留在属于你的地图里</h1>
          <p class="page-subtitle">点击左侧城市可以让地图聚焦到对应位置，没有坐标的记录会显示为“定位补全中”</p>
        </div>

        <div class="brand-stat-grid tracks-stats">
          <div class="brand-stat">
            <span>鎬昏褰曟暟</span>
            <strong>{{ sortedTracks.length }}</strong>
          </div>
          <div class="brand-stat">
            <span>已显示点位</span>
            <strong>{{ mappedTrackCount }}</strong>
          </div>
          <div class="brand-stat tracks-playback-card">
            <span>旅行回放</span>
            <a-button type="primary" class="tracks-playback-button" :disabled="playbackTracks.length < 2" @click="togglePlayback">
              {{ isPlaying ? '⏸️ 暂停播放' : '▶️ 播放我的行程' }}
            </a-button>
          </div>
        </div>
      </section>

      <div class="split-layout tracks-layout">
        <aside class="glass-panel tracks-list-panel">
          <div class="section-heading tracks-list-heading">
            <h2>去过的城市</h2>
            <p>这里会按照时间顺序保留你的旅行记录，点击后地图会聚焦到对应位置</p>
          </div>

          <div class="tracks-list-scroller">
            <a-empty v-if="!sortedTracks.length && !loading" description="还没有可展示的旅行轨迹" />

            <a-spin :spinning="loading" class="tracks-list-spin">
              <div v-if="sortedTracks.length" class="tracks-list-items">
                <div
                  v-for="track in sortedTracks"
                  :key="track.id"
                  class="track-item"
                  :class="{ 'track-item--active': playbackActiveTrackId === track.id }"
                  :data-track-id="track.id"
                >
                  <div class="track-item__head">
                    <div class="track-item__title-wrap">
                      <strong>{{ track.city }}</strong>
                      <span v-if="!hasCoordinates(track)" class="track-pill">定位补全中</span>
                    </div>
                    <a-button size="small" :disabled="!hasCoordinates(track)" @click="focusTrack(track)">
                      地图定位
                    </a-button>
                    <a-popconfirm title="确认删除这条旅行记录吗" ok-text="删除" cancel-text="取消" @confirm="deleteTrack(track)">
                      <a-button
                        size="small"
                        danger
                        class="track-delete-button"
                        :loading="deletingTrackId === track.id"
                      >
                        删除
                      </a-button>
                    </a-popconfirm>
                  </div>

                  <button class="track-item__main" type="button" @click="openTrackPlan(track)">
                    <span>{{ formatDateTime(track.searched_at) }}</span>
                    <span>{{ track.start_date }} - {{ track.end_date }}</span>
                    <small>{{ track.trip_summary || '杩欎竴娆℃梾琛屽凡缁忚璁板綍涓嬫潵' }}</small>
                  </button>
                </div>
              </div>
            </a-spin>
          </div>
        </aside>

        <section class="glass-panel glass-panel--soft tracks-map-panel">
          <div class="section-heading tracks-map-heading">
            <h2>城市地图</h2>
            <p>支持鼠标滚轮缩放和拖拽查看，播放时会按时间顺序展示你的旅行轨迹</p>
          </div>
          <div v-if="!amapKey" class="map-placeholder">
            璇峰厛鍦ㄥ墠绔幆澧冨彉閲忎腑閰嶇疆鍦板浘瀵嗛挜 `VITE_AMAP_API_KEY`锛屽湴鍥鹃〉闈㈡墠鑳藉姞杞?          </div>
          <div v-else ref="mapContainer" class="map-canvas"></div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import AMapLoader from '@amap/amap-jsapi-loader'

import { deleteTravelTrack, getTravelTrackPlan, getTravelTracks } from '@/services/api'
import type { TravelTrackItem } from '@/types'
import { AMAP_MAP_STYLE } from '@/utils/mapStyle'

const amapKey = import.meta.env.VITE_AMAP_API_KEY || ''
const amapSecurityJsCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE || ''
const router = useRouter()
const loading = ref(false)
const deletingTrackId = ref('')
const tracks = ref<TravelTrackItem[]>([])
const mapContainer = ref<HTMLDivElement | null>(null)
const isPlaying = ref(false)
const playbackActiveTrackId = ref('')

const sortedTracks = computed(() =>
  [...tracks.value].sort((a, b) => new Date(a.searched_at).getTime() - new Date(b.searched_at).getTime()),
)

const playbackTracks = computed(() => sortedTracks.value.filter(hasCoordinates))

const mappedTrackCount = computed(
  () => playbackTracks.value.length,
)

let amapSdk: any = null
let mapInstance: any = null
let infoWindow: any = null
let markers: any[] = []
let playbackMarker: any = null
let playbackTrail: any = null
let playbackFrameId = 0
let playbackTrailPath: number[][] = []

const formatDateTime = (value: string) => new Date(value).toLocaleString('zh-CN')
const hasCoordinates = (track: TravelTrackItem) => track.city_longitude != null && track.city_latitude != null

const buildInfoHtml = (track: TravelTrackItem) => `
  <div style="padding: 8px 10px; min-width: 220px; color: #17324f; line-height: 1.7;">
    <div style="font-size: 16px; font-weight: 700; margin-bottom: 8px;">${track.city}</div>
    <div style="margin-bottom: 4px;">搜索时间：${formatDateTime(track.searched_at)}</div>
    <div style="margin-bottom: 4px;">行程日期：${track.start_date} - ${track.end_date}</div>
    <div style="color: #5f7893;">${track.trip_summary || '这一趟旅行已经被记录下来'}</div>
  </div>
`

const createTravelerContent = () => `
  <div class="tracks-traveler">
    <div class="tracks-traveler__bubble">🚶</div>
    <div class="tracks-traveler__shadow"></div>
  </div>
`

const clearPlaybackTrail = () => {
  playbackTrailPath = []
  if (playbackTrail) {
    playbackTrail.setPath([])
  }
}

const stopPlayback = (keepActive = false, keepTrail = true) => {
  isPlaying.value = false
  if (!keepActive) {
    playbackActiveTrackId.value = ''
  }
  if (playbackFrameId) {
    cancelAnimationFrame(playbackFrameId)
    playbackFrameId = 0
  }
  if (playbackMarker && mapInstance) {
    mapInstance.remove(playbackMarker)
    playbackMarker = null
  }
  if (!keepTrail && playbackTrail && mapInstance) {
    mapInstance.remove(playbackTrail)
    playbackTrail = null
    playbackTrailPath = []
  }
}

const ensurePlaybackOverlays = () => {
  if (!mapInstance || !amapSdk) return
  if (!playbackMarker) {
    playbackMarker = new amapSdk.Marker({
      position: [0, 0],
      offset: new amapSdk.Pixel(-20, -48),
      content: createTravelerContent(),
      zIndex: 130,
    })
    mapInstance.add(playbackMarker)
  }
  if (!playbackTrail) {
    playbackTrail = new amapSdk.Polyline({
      path: [],
      strokeColor: '#2d86e7',
      strokeWeight: 5,
      strokeOpacity: 0.72,
      lineJoin: 'round',
      lineCap: 'round',
    })
    mapInstance.add(playbackTrail)
  }
}

const scrollTrackIntoView = (trackId: string) => {
  if (typeof document === 'undefined') return
  const element = document.querySelector(`[data-track-id="${trackId}"]`) as HTMLElement | null
  element?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
}

const animateSegment = (from: TravelTrackItem, to: TravelTrackItem) =>
  new Promise<void>((resolve) => {
    if (
      !mapInstance ||
      !amapSdk ||
      from.city_longitude == null ||
      from.city_latitude == null ||
      to.city_longitude == null ||
      to.city_latitude == null
    ) {
      resolve()
      return
    }

    ensurePlaybackOverlays()
    playbackActiveTrackId.value = to.id
    scrollTrackIntoView(to.id)

    const start = [Number(from.city_longitude), Number(from.city_latitude)]
    const end = [Number(to.city_longitude), Number(to.city_latitude)]
    const segmentPath = playbackTrailPath.length ? [...playbackTrailPath] : [start]
    const duration = 1400
    const startedAt = performance.now()

    playbackMarker?.setPosition(start)
    playbackTrail?.setPath(segmentPath)
    mapInstance.setFitView([playbackTrail, playbackMarker, ...markers], false, [90, 90, 90, 90])

    const step = (now: number) => {
      if (!isPlaying.value) {
        resolve()
        return
      }
      const progress = Math.min((now - startedAt) / duration, 1)
      const lng = start[0] + (end[0] - start[0]) * progress
      const lat = start[1] + (end[1] - start[1]) * progress
      const position = [lng, lat]
      playbackMarker?.setPosition(position)
      playbackTrail?.setPath([...segmentPath, position])
      if (progress < 1) {
        playbackFrameId = requestAnimationFrame(step)
        return
      }
      playbackTrailPath = [...segmentPath, end]
      playbackTrail?.setPath(playbackTrailPath)
      resolve()
    }

    playbackFrameId = requestAnimationFrame(step)
  })

const playJourney = async () => {
  if (playbackTracks.value.length < 2 || !mapInstance || !amapSdk) {
    message.info('至少需要两条有坐标的旅行记录才能播放')
    return
  }

  stopPlayback(false, false)
  isPlaying.value = true
  clearPlaybackTrail()
  playbackActiveTrackId.value = playbackTracks.value[0].id
  scrollTrackIntoView(playbackTracks.value[0].id)
  ensurePlaybackOverlays()
  playbackMarker?.setPosition([
    Number(playbackTracks.value[0].city_longitude),
    Number(playbackTracks.value[0].city_latitude),
  ])
  playbackTrailPath = [[
    Number(playbackTracks.value[0].city_longitude),
    Number(playbackTracks.value[0].city_latitude),
  ]]
  playbackTrail?.setPath(playbackTrailPath)

  for (let index = 1; index < playbackTracks.value.length; index += 1) {
    if (!isPlaying.value) return
    await animateSegment(playbackTracks.value[index - 1], playbackTracks.value[index])
  }

  stopPlayback(true, true)
}

const togglePlayback = async () => {
  if (isPlaying.value) {
    stopPlayback(true, true)
    return
  }
  await playJourney()
}

const refreshMarkers = () => {
  if (!mapInstance || !amapSdk) return

  markers.forEach((marker) => mapInstance.remove(marker))
  markers = []

  const validTracks = playbackTracks.value

  validTracks.forEach((track) => {
    const marker = new amapSdk.Marker({
      position: [track.city_longitude, track.city_latitude],
      title: track.city,
      label: {
        direction: 'top',
        content: `<div style="padding: 4px 8px; border-radius: 999px; background: rgba(255,255,255,0.92); border: 1px solid rgba(140,190,236,0.86); color: #245184; font-weight: 700;">${track.city}</div>`,
      },
    })

    marker.on('click', () => {
      if (!infoWindow) {
        infoWindow = new amapSdk.InfoWindow({ offset: new amapSdk.Pixel(0, -28) })
      }
      infoWindow.setContent(buildInfoHtml(track))
      infoWindow.open(mapInstance, marker.getPosition())
    })

    mapInstance.add(marker)
    markers.push(marker)
  })

  if (validTracks.length) {
    mapInstance.setFitView(markers, false, [80, 80, 80, 80])
  }
}

const initMap = async () => {
  if (!amapKey || !mapContainer.value) return

  if (amapSecurityJsCode) {
    ;(window as typeof window & { _AMapSecurityConfig?: Record<string, string> })._AMapSecurityConfig = {
      securityJsCode: amapSecurityJsCode,
    }
  }

  amapSdk = await AMapLoader.load({
    key: amapKey,
    version: '2.0',
  })

  mapInstance = new amapSdk.Map(mapContainer.value, {
    zoom: 4.5,
    center: [104.195397, 35.86166],
    mapStyle: AMAP_MAP_STYLE,
    resizeEnable: true,
    scrollWheel: true,
  })

  refreshMarkers()
}

const focusTrack = (track: TravelTrackItem) => {
  stopPlayback(false, false)
  if (!hasCoordinates(track)) {
    message.info('这条轨迹正在补全坐标，稍后再来看看')
    return
  }
  if (!mapInstance) return

  mapInstance.setZoomAndCenter?.(8, [track.city_longitude, track.city_latitude])
  if (!infoWindow && amapSdk) {
    infoWindow = new amapSdk.InfoWindow({ offset: new amapSdk.Pixel(0, -28) })
  }
  infoWindow?.setContent(buildInfoHtml(track))
  infoWindow?.open(mapInstance, [track.city_longitude, track.city_latitude])
}

const openTrackPlan = async (track: TravelTrackItem) => {
  try {
    const response = await getTravelTrackPlan(track.id)
    if (!response.success || !response.data) {
      throw new Error(response.message || '没有找到这条旅行规划')
    }
    sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
    sessionStorage.setItem('tripPlannerSessionId', track.id)
    sessionStorage.removeItem('tripPlannerSummary')
    router.push({ path: '/result', query: { trackId: track.id } })
  } catch (error: any) {
    message.error(error.message || '打开旅行规划失败')
  }
}

const loadTracks = async () => {
  loading.value = true
  try {
    const response = await getTravelTracks()
    tracks.value = (response.data || []).filter((item) => item.city)
    stopPlayback(false, false)
    refreshMarkers()
  } catch (error: any) {
    message.error(error.message || '鍔犺浇鏃呰杞ㄨ抗澶辫触')
  } finally {
    loading.value = false
  }
}

const deleteTrack = async (track: TravelTrackItem) => {
  deletingTrackId.value = track.id
  try {
    stopPlayback(false, false)
    await deleteTravelTrack(track.id)
    tracks.value = tracks.value.filter((item) => item.id !== track.id)
    infoWindow?.close?.()
    refreshMarkers()
    message.success('已删除这条旅行记录')
  } catch (error: any) {
    message.error(error.message || '鍒犻櫎鏃呰杞ㄨ抗澶辫触')
  } finally {
    deletingTrackId.value = ''
  }
}

onMounted(async () => {
  await loadTracks()
  try {
    if (amapKey) {
      await initMap()
    }
  } catch (error: any) {
    message.error(error.message || '鍔犺浇鍦板浘澶辫触')
  }
})

onUnmounted(() => {
  stopPlayback(false, false)
  if (mapInstance) {
    mapInstance.destroy()
    mapInstance = null
  }
})
</script>

<style scoped>
.tracks-shell {
  display: grid;
  gap: 22px;
}

.tracks-hero-panel {
  padding: 24px;
}

.tracks-layout {
  grid-template-columns: 360px minmax(0, 1fr);
  align-items: stretch;
}

.tracks-list-panel,
.tracks-map-panel {
  display: flex;
  flex-direction: column;
  padding: 24px;
  height: clamp(480px, calc(100vh - 360px), 620px);
  min-height: 480px;
  overflow: hidden;
}

.tracks-title {
  font-size: clamp(32px, 3.8vw, 48px);
}

.tracks-stats {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.tracks-playback-card {
  display: grid;
  gap: 12px;
}

.tracks-playback-button {
  width: 100%;
  min-height: 46px;
  border-radius: 14px;
  font-weight: 700;
}

.tracks-list-heading {
  margin-bottom: 14px;
}

.tracks-list-scroller {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: rgba(107, 150, 204, 0.7) rgba(255, 255, 255, 0.22);
}

.tracks-list-scroller::-webkit-scrollbar {
  width: 10px;
}

.tracks-list-scroller::-webkit-scrollbar-track {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.28);
}

.tracks-list-scroller::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(107, 150, 204, 0.7);
  border: 2px solid rgba(255, 255, 255, 0.24);
}

.tracks-list-spin,
.tracks-list-items {
  display: flex;
  flex-direction: column;
}

.tracks-list-spin {
  flex: 1;
  min-height: 0;
}

.tracks-list-items {
  min-height: min-content;
}

.track-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
  padding: 16px 18px;
  border: 1px solid rgba(255, 255, 255, 0.52);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.58);
  color: var(--brand-text);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.track-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(66, 109, 166, 0.12);
}

.track-item--active {
  border-color: rgba(84, 151, 230, 0.76);
  background: linear-gradient(135deg, rgba(231, 242, 255, 0.92), rgba(245, 250, 255, 0.95));
  box-shadow: 0 16px 30px rgba(82, 138, 208, 0.16);
}

.track-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.track-item__title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.track-item__main {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.track-item__main span,
.track-item__main small {
  color: var(--brand-muted);
  line-height: 1.7;
}

.track-delete-button {
  border-radius: 999px;
}

.track-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(231, 240, 255, 0.92);
  color: #356ca8 !important;
  font-size: 16px;
  font-weight: 700;
}

.tracks-map-heading {
  margin-bottom: 16px;
}

.map-canvas,
.map-placeholder {
  width: 100%;
  flex: 1;
  min-height: 0;
  border-radius: 22px;
  overflow: hidden;
}

.map-placeholder {
  display: grid;
  place-items: center;
  padding: 24px;
  text-align: center;
  background: rgba(255, 255, 255, 0.5);
  color: var(--brand-muted);
}

:deep(.tracks-traveler) {
  position: relative;
  width: 56px;
  height: 76px;
}

:deep(.tracks-traveler__bubble) {
  position: absolute;
  inset: 0 5px 10px;
  display: grid;
  place-items: center;
  border-radius: 26px 26px 22px 22px;
  background: linear-gradient(180deg, #ffffff, #d9ebff);
  border: 1px solid rgba(122, 172, 233, 0.72);
  box-shadow:
    0 14px 24px rgba(85, 136, 201, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.82);
  font-size: 30px;
}

:deep(.tracks-traveler__shadow) {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 3px;
  height: 10px;
  border-radius: 999px;
  background: rgba(70, 114, 172, 0.18);
  filter: blur(4px);
}

@media (max-width: 960px) {
  .tracks-hero-panel {
    padding: 22px;
  }

  .tracks-layout {
    grid-template-columns: 1fr;
  }

  .tracks-list-panel,
  .tracks-map-panel {
    padding: 22px;
    height: auto;
    min-height: auto;
  }

  .tracks-list-scroller {
    height: 320px;
    min-height: 320px;
    max-height: 320px;
    overflow-y: auto;
    padding-right: 0;
  }

  .tracks-stats {
    grid-template-columns: 1fr;
  }

  .map-canvas,
  .map-placeholder {
    flex: none;
    min-height: 360px;
    max-height: 360px;
  }
}
</style>


