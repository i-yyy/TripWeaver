<template>
  <div class="brand-page">
    <div class="brand-shell split-layout tracks-layout">
      <aside class="glass-panel tracks-list-panel">
        <div class="section-heading">
          <span class="page-kicker">我的旅行轨迹</span>
          <h1 class="page-title tracks-title">把每一次搜索过的城市，留在属于你的地图里</h1>
          <p class="page-subtitle">点击左侧城市可以让地图聚焦到对应位置。没有坐标的记录会显示为“定位补全中”。</p>
        </div>

        <div class="brand-stat-grid tracks-stats">
          <div class="brand-stat">
            <span>总记录数</span>
            <strong>{{ tracks.length }}</strong>
          </div>
          <div class="brand-stat">
            <span>已显示点位</span>
            <strong>{{ mappedTrackCount }}</strong>
          </div>
        </div>

        <a-empty v-if="!tracks.length && !loading" description="还没有可展示的旅行轨迹" />

        <a-spin :spinning="loading">
          <button
            v-for="track in tracks"
            :key="track.id"
            class="track-item"
            type="button"
            @click="focusTrack(track)"
          >
            <div class="track-item__head">
              <strong>{{ track.city }}</strong>
              <span v-if="!hasCoordinates(track)" class="track-pill">定位补全中</span>
            </div>
            <span>{{ formatDateTime(track.searched_at) }}</span>
            <span>{{ track.start_date }} - {{ track.end_date }}</span>
            <small>{{ track.trip_summary || '这一次旅行已经被记录下来。' }}</small>
          </button>
        </a-spin>
      </aside>

      <section class="glass-panel glass-panel--soft tracks-map-panel">
        <div class="section-heading tracks-map-heading">
          <h2>城市地图</h2>
          <p>支持鼠标滚轮缩放和拖拽查看，点开标记还能看到搜索时间和行程区间。</p>
        </div>
        <div v-if="!amapKey" class="map-placeholder">
          请先在前端环境变量中配置 `VITE_AMAP_API_KEY`，地图页面才能加载。
        </div>
        <div v-else ref="mapContainer" class="map-canvas"></div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import AMapLoader from '@amap/amap-jsapi-loader'

import { getTravelTracks } from '@/services/api'
import type { TravelTrackItem } from '@/types'

const amapKey = import.meta.env.VITE_AMAP_API_KEY || ''
const amapSecurityJsCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE || ''
const loading = ref(false)
const tracks = ref<TravelTrackItem[]>([])
const mapContainer = ref<HTMLDivElement | null>(null)

const mappedTrackCount = computed(
  () => tracks.value.filter((item) => typeof item.city_longitude === 'number' && typeof item.city_latitude === 'number').length,
)

let amapSdk: any = null
let mapInstance: any = null
let infoWindow: any = null
let markers: any[] = []

const formatDateTime = (value: string) => new Date(value).toLocaleString('zh-CN')
const hasCoordinates = (track: TravelTrackItem) => track.city_longitude != null && track.city_latitude != null

const buildInfoHtml = (track: TravelTrackItem) => `
  <div style="padding: 8px 10px; min-width: 220px; color: #17324f; line-height: 1.7;">
    <div style="font-size: 16px; font-weight: 700; margin-bottom: 8px;">${track.city}</div>
    <div style="margin-bottom: 4px;">搜索时间：${formatDateTime(track.searched_at)}</div>
    <div style="margin-bottom: 4px;">行程日期：${track.start_date} - ${track.end_date}</div>
    <div style="color: #5f7893;">${track.trip_summary || '这一次旅行已经被记录下来。'}</div>
  </div>
`

const refreshMarkers = () => {
  if (!mapInstance || !amapSdk) return

  markers.forEach((marker) => mapInstance.remove(marker))
  markers = []

  const validTracks = tracks.value.filter(hasCoordinates)

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
    resizeEnable: true,
    scrollWheel: true,
  })

  refreshMarkers()
}

const focusTrack = (track: TravelTrackItem) => {
  if (!hasCoordinates(track)) {
    message.info('这条轨迹正在补全坐标，稍后再来看看。')
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

onMounted(async () => {
  loading.value = true
  try {
    const response = await getTravelTracks()
    tracks.value = (response.data || []).filter((item) => item.city)
    if (amapKey) {
      await initMap()
    }
  } catch (error: any) {
    message.error(error.message || '加载旅行轨迹失败')
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.destroy()
    mapInstance = null
  }
})
</script>

<style scoped>
.tracks-layout {
  grid-template-columns: 360px minmax(0, 1fr);
}

.tracks-list-panel,
.tracks-map-panel {
  padding: 24px;
}

.tracks-title {
  font-size: clamp(32px, 3.8vw, 48px);
}

.tracks-stats {
  margin-bottom: 16px;
}

.track-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  padding: 16px 18px;
  border: 1px solid rgba(255, 255, 255, 0.52);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.58);
  color: var(--brand-text);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.track-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(66, 109, 166, 0.12);
}

.track-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.track-item span,
.track-item small {
  color: var(--brand-muted);
  line-height: 1.7;
}

.track-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(231, 240, 255, 0.92);
  color: #356ca8 !important;
  font-size: 12px;
  font-weight: 700;
}

.tracks-map-heading {
  margin-bottom: 16px;
}

.map-canvas,
.map-placeholder {
  width: 100%;
  min-height: calc(100vh - 228px);
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

@media (max-width: 960px) {
  .tracks-layout {
    grid-template-columns: 1fr;
  }

  .tracks-list-panel,
  .tracks-map-panel {
    padding: 22px;
  }

  .map-canvas,
  .map-placeholder {
    min-height: 460px;
  }
}
</style>
