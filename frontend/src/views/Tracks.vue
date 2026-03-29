<template>
  <div class="tracks-page">
    <div class="tracks-shell">
      <aside class="tracks-list">
        <div class="panel-head">
          <h1>我的旅行轨迹</h1>
          <p>每一次搜索过的城市，都会在地图上留下一个轻轻发亮的脚印。</p>
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
            <strong>{{ track.city }}</strong>
            <span>{{ formatDateTime(track.searched_at) }}</span>
            <span>{{ track.start_date }} - {{ track.end_date }}</span>
          </button>
        </a-spin>
      </aside>

      <section class="map-panel">
        <div v-if="!amapKey" class="map-placeholder">
          请先在前端环境变量中配置 `VITE_AMAP_API_KEY`，地图页才能加载。
        </div>
        <div v-else ref="mapContainer" class="map-canvas"></div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import AMapLoader from '@amap/amap-jsapi-loader'

import { getTravelTracks } from '@/services/api'
import type { TravelTrackItem } from '@/types'

const amapKey = import.meta.env.VITE_AMAP_API_KEY || ''
const amapSecurityJsCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE || ''
const loading = ref(false)
const tracks = ref<TravelTrackItem[]>([])
const mapContainer = ref<HTMLDivElement | null>(null)

let amapSdk: any = null
let mapInstance: any = null
let infoWindow: any = null
let markers: any[] = []

const formatDateTime = (value: string) => new Date(value).toLocaleString('zh-CN')

const buildInfoHtml = (track: TravelTrackItem) => `
  <div style="padding: 6px 8px; min-width: 220px;">
    <div style="font-size: 16px; font-weight: 700; margin-bottom: 8px;">${track.city}</div>
    <div style="margin-bottom: 4px;">搜索时间：${formatDateTime(track.searched_at)}</div>
    <div style="margin-bottom: 4px;">行程日期：${track.start_date} - ${track.end_date}</div>
    <div style="color: #4f5d72;">${track.trip_summary || '这一次旅程已经被记录下来。'}</div>
  </div>
`

const refreshMarkers = () => {
  if (!mapInstance || !amapSdk) return

  markers.forEach((marker) => mapInstance.remove(marker))
  markers = []

  const validTracks = tracks.value.filter(
    (item) => typeof item.city_longitude === 'number' && typeof item.city_latitude === 'number',
  )

  validTracks.forEach((track) => {
    const marker = new amapSdk.Marker({
      position: [track.city_longitude, track.city_latitude],
      title: track.city,
      label: {
        direction: 'top',
        content: `<div class="track-marker-label">${track.city}</div>`,
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
  if (!mapInstance || track.city_longitude == null || track.city_latitude == null) return
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
.tracks-page {
  padding: 24px;
}

.tracks-shell {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 20px;
  min-height: calc(100vh - 140px);
}

.tracks-list,
.map-panel {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 18px 40px rgba(31, 50, 81, 0.12);
}

.tracks-list {
  padding: 24px;
}

.panel-head h1 {
  margin-bottom: 10px;
}

.panel-head p {
  color: #607086;
  line-height: 1.7;
}

.track-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 12px;
  padding: 14px 16px;
  border: none;
  border-radius: 16px;
  text-align: left;
  cursor: pointer;
  background: linear-gradient(135deg, #fef2e5, #f5f9ff);
}

.track-item:hover {
  background: linear-gradient(135deg, #ffe5c6, #e8f3ff);
}

.map-panel {
  padding: 16px;
}

.map-canvas,
.map-placeholder {
  width: 100%;
  min-height: calc(100vh - 172px);
  border-radius: 18px;
}

.map-placeholder {
  display: grid;
  place-items: center;
  background: #eef3f8;
  color: #536275;
  padding: 24px;
  text-align: center;
}

@media (max-width: 960px) {
  .tracks-shell {
    grid-template-columns: 1fr;
  }

  .map-canvas,
  .map-placeholder {
    min-height: 460px;
  }
}
</style>
