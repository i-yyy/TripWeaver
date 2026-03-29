<template>
  <div class="day-route-map">
    <div v-if="!amapKey" class="day-route-map__placeholder">
      <p>未配置高德 JS Key，当前显示静态路线图。</p>
      <img
        v-if="fallbackStaticMapUrl"
        class="day-route-map__fallback"
        :src="fallbackStaticMapUrl"
        alt="路线静态图"
      />
    </div>

    <div v-else-if="loading" class="day-route-map__placeholder">
      <p>正在加载当日路线地图...</p>
      <img
        v-if="fallbackStaticMapUrl"
        class="day-route-map__fallback"
        :src="fallbackStaticMapUrl"
        alt="路线静态图"
      />
    </div>

    <div v-else-if="route?.markers?.length" ref="mapContainer" class="day-route-map__canvas"></div>

    <div v-else-if="fallbackStaticMapUrl" class="day-route-map__placeholder">
      <p>交互式路线暂不可用，当前显示静态路线图。</p>
      <img class="day-route-map__fallback" :src="fallbackStaticMapUrl" alt="路线静态图" />
    </div>

    <div v-else class="day-route-map__placeholder">
      <p>当前没有可展示的路线点位。</p>
    </div>

    <p v-if="error" class="day-route-map__error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'

import type { DayRouteInfo, DayRouteMarker } from '@/types'

const props = defineProps<{
  route?: DayRouteInfo | null
  loading?: boolean
  error?: string | null
  fallbackStaticMapUrl?: string | null
}>()

const amapKey = import.meta.env.VITE_AMAP_API_KEY || ''
const amapSecurityJsCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE || ''
const mapContainer = ref<HTMLDivElement | null>(null)

const canRenderInteractive = computed(() => Boolean(amapKey && props.route?.markers?.length))

let amapSdk: any = null
let mapInstance: any = null
let infoWindow: any = null
let markers: any[] = []
let polylines: any[] = []

const buildInfoHtml = (marker: DayRouteMarker) => {
  const imageBlock = marker.image_url
    ? `<img src="${marker.image_url}" alt="${marker.title}" style="width:100%;height:120px;object-fit:cover;border-radius:12px;margin-bottom:10px;" />`
    : ''

  return `
    <div style="min-width:220px;max-width:260px;padding:8px;color:#17324f;line-height:1.7;">
      ${imageBlock}
      <div style="display:inline-flex;align-items:center;gap:8px;margin-bottom:8px;">
        <span style="display:inline-grid;place-items:center;min-width:26px;height:26px;padding:0 8px;border-radius:999px;background:#17324f;color:#fff;font-weight:700;">${marker.label}</span>
        <strong style="font-size:15px;">${marker.title}</strong>
      </div>
      <div style="color:#5f7893;">${marker.address || '暂无地址信息'}</div>
    </div>
  `
}

const clearOverlays = () => {
  if (!mapInstance) return
  markers.forEach((marker) => mapInstance.remove(marker))
  polylines.forEach((line) => mapInstance.remove(line))
  markers = []
  polylines = []
}

const drawRoute = () => {
  if (!mapInstance || !amapSdk || !props.route) return

  clearOverlays()

  props.route.segments.forEach((segment) => {
    if (!segment.polyline?.length) return
    const polyline = new amapSdk.Polyline({
      path: segment.polyline.map((point) => [point.longitude, point.latitude]),
      strokeColor: segment.route_type === 'walking' ? '#245184' : segment.route_type === 'driving' ? '#ff6b35' : '#2f7d32',
      strokeWeight: 6,
      strokeOpacity: 0.88,
      strokeStyle: segment.route_type === 'transit' ? 'dashed' : 'solid',
      lineJoin: 'round',
      lineCap: 'round',
    })
    mapInstance.add(polyline)
    polylines.push(polyline)
  })

  props.route.markers.forEach((markerData) => {
    const marker = new amapSdk.Marker({
      position: [markerData.location.longitude, markerData.location.latitude],
      title: markerData.title,
      offset: new amapSdk.Pixel(0, -8),
      label: {
        direction: 'top',
        content: `<div style="padding:4px 9px;border-radius:999px;background:rgba(255,255,255,0.94);border:1px solid rgba(23,50,79,0.18);color:#17324f;font-weight:700;">${markerData.label}</div>`,
      },
    })

    marker.on('click', () => {
      if (!infoWindow) {
        infoWindow = new amapSdk.InfoWindow({ offset: new amapSdk.Pixel(0, -28) })
      }
      infoWindow.setContent(buildInfoHtml(markerData))
      infoWindow.open(mapInstance, marker.getPosition())
    })

    mapInstance.add(marker)
    markers.push(marker)
  })

  const overlays = [...polylines, ...markers]
  if (overlays.length) {
    mapInstance.setFitView(overlays, false, [70, 70, 70, 70])
  }
}

const ensureMap = async () => {
  if (!amapKey || !mapContainer.value || mapInstance) return

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
    zoom: 12,
    center: [104.195397, 35.86166],
    resizeEnable: true,
    scrollWheel: true,
    jogEnable: true,
  })
}

const renderIfReady = async () => {
  if (!canRenderInteractive.value || props.loading) {
    clearOverlays()
    return
  }
  await nextTick()
  await ensureMap()
  drawRoute()
}

watch(
  () => props.route,
  () => {
    void renderIfReady()
  },
  { deep: true, flush: 'post' },
)

watch(
  () => props.loading,
  () => {
    void renderIfReady()
  },
  { flush: 'post' },
)

onMounted(() => {
  void renderIfReady()
})

onUnmounted(() => {
  clearOverlays()
  if (mapInstance) {
    mapInstance.destroy()
    mapInstance = null
  }
})
</script>

<style scoped>
.day-route-map {
  width: 100%;
}

.day-route-map__canvas,
.day-route-map__placeholder {
  width: 100%;
  min-height: 360px;
  border-radius: 22px;
}

.day-route-map__canvas {
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.55);
}

.day-route-map__placeholder {
  display: grid;
  place-items: center;
  gap: 12px;
  padding: 20px;
  background: rgba(243, 246, 251, 0.92);
  color: var(--brand-muted);
  text-align: center;
}

.day-route-map__fallback {
  width: 100%;
  max-height: 360px;
  object-fit: cover;
  border-radius: 18px;
}

.day-route-map__error {
  margin: 10px 0 0;
  color: #b42318;
  font-size: 13px;
}
</style>
