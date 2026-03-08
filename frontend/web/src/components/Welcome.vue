<template>
  <div ref="welcomeRoot" class="welcome-page" :class="{ 'welcome-page-fullscreen': isFullscreen }">
    <div id="mars3dContainer" class="map-container" :class="{ 'map-container-hidden': isSwitchingScene }"></div>
    <div v-if="map3dLoading" class="loading-overlay">{{ loadingText }}</div>

    <div class="map-legend">
      <div v-for="item in legendStats" :key="item.key" class="legend-block">
        <div class="legend-inline-row">
          <span class="legend-total-label">{{ item.label }}</span>
          <span class="legend-total-value">{{ item.total }}</span>
          <span class="legend-inline-status">
            <span class="status-dot online"></span>在线{{ item.online }}
          </span>
          <span class="legend-inline-status legend-inline-status-offline">
            <span class="status-dot offline"></span>离线{{ item.offline }}
          </span>
        </div>
      </div>

      <div class="scene-tools">
        <span class="scene-tools-label"></span>
        <button class="scene-btn" :class="{ active: currentSceneMode === '3D' }" :disabled="isSwitchingScene" @click="switchSceneMode('3D')">3D</button>
        <button class="scene-btn" :class="{ active: currentSceneMode === '2D' }" :disabled="isSwitchingScene" @click="switchSceneMode('2D')">2D</button>
        <button
          class="scene-btn fullscreen-btn"
          :title="isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'"
          @click="toggleFullscreen"
        >
          <span :class="['fullscreen-icon', isFullscreen ? 'is-exit' : 'is-enter']"></span>
        </button>
      </div>
    </div>

    <el-dialog
      :visible.sync="deviceCardVisible"
      :append-to-body="true"
      :show-close="false"
      :fullscreen="true"
      :destroy-on-close="true"
      custom-class="device-detail-embed-dialog"
      @closed="handleDetailDialogClosed"
    >
      <button class="floating-close-btn" @click="deviceCardVisible = false">×</button>
      <iframe
        v-if="detailFrameUrl"
        :src="detailFrameUrl"
        class="detail-embed-frame"
        frameborder="0"
      />
    </el-dialog>
  </div>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
import * as mars3d from 'mars3d'
import locationIcon from '../assets/location.png'
import { mapOptions as scenePreset } from '../utils/map'

const MARKER_HEIGHT = 180000
const DEFAULT_SCENE_CENTER = (scenePreset && scenePreset.scene && scenePreset.scene.center)
  ? scenePreset.scene.center
  : { lat: 31.84, lng: 117.22, alt: 2800000, heading: 0, pitch: -60 }

export default {
  name: 'Welcome',
  computed: {
    legendStats () {
      return [
        { key: 'total', label: '设备总数', ...this.deviceStats.total },
        { key: 'north', label: '北极设备数量', ...this.deviceStats.north },
        { key: 'south', label: '南极设备数量', ...this.deviceStats.south },
        { key: 'domestic', label: '国内设备数量', ...this.deviceStats.domestic }
      ]
    }
  },
  data () {
    return {
      map3dLoading: true,
      map: null,
      deviceEntities: [],
      deviceEntityMap: new Map(),
      deviceStats: {
        total: { total: 0, online: 0, offline: 0 },
        domestic: { total: 0, online: 0, offline: 0 },
        south: { total: 0, online: 0, offline: 0 },
        north: { total: 0, online: 0, offline: 0 }
      },
      markerImage: locationIcon,
      currentSceneMode: '3D',
      latestDeviceList: [],
      isSwitchingScene: false,
      pendingRenderTimer: null,
      scaleTuneTimer: null,
      mapClickHandler: null,
      deviceCardVisible: false,
      detailFrameUrl: '',
      loadingText: '地图加载中...',
      mapPointsReqSeq: 0,
      mapPointsRefreshTimer: null,
      lastMapClickTs: 0,
      isFullscreen: false
    }
  },
  mounted () {
    this.$nextTick(() => {
      this.initMap3D()
    })
    document.addEventListener('fullscreenchange', this.handleFullscreenChange)
  },
  beforeDestroy () {
    document.removeEventListener('fullscreenchange', this.handleFullscreenChange)
    if (this.pendingRenderTimer) {
      clearTimeout(this.pendingRenderTimer)
      this.pendingRenderTimer = null
    }
    if (this.scaleTuneTimer) {
      clearInterval(this.scaleTuneTimer)
      this.scaleTuneTimer = null
    }
    if (this.mapPointsRefreshTimer) {
      clearInterval(this.mapPointsRefreshTimer)
      this.mapPointsRefreshTimer = null
    }
    this.clearDeviceEntities()
    if (this.mapClickHandler && this.map && this.map.viewer) {
      this.mapClickHandler.destroy()
      this.mapClickHandler = null
    }
    if (this.map) {
      this.map.destroy()
      this.map = null
    }
  },
  methods: {
    async toggleFullscreen () {
      const root = this.$refs.welcomeRoot
      if (!root) return
      try {
        if (!document.fullscreenElement) {
          if (root.requestFullscreen) await root.requestFullscreen()
          this.isFullscreen = true
        } else {
          if (document.exitFullscreen) await document.exitFullscreen()
          this.isFullscreen = false
        }
      } catch (e) {
        this.$message.warning('全屏切换失败，请检查浏览器权限')
      } finally {
        this.$nextTick(() => {
          if (this.map && this.map.viewer) this.map.viewer.resize()
        })
      }
    },
    handleFullscreenChange () {
      this.isFullscreen = Boolean(document.fullscreenElement)
      this.$nextTick(() => {
        if (this.map && this.map.viewer) this.map.viewer.resize()
      })
    },
    bindMapDeviceClick () {
      if (!this.map || !this.map.viewer) return
      const Cesium = mars3d.Cesium
      if (this.mapClickHandler) {
        this.mapClickHandler.destroy()
        this.mapClickHandler = null
      }
      this.mapClickHandler = new Cesium.ScreenSpaceEventHandler(this.map.viewer.scene.canvas)
      this.mapClickHandler.setInputAction((movement) => {
        const now = Date.now()
        if (now - this.lastMapClickTs < 150) return
        this.lastMapClickTs = now
        const picked = this.map.viewer.scene.pick(movement.position)
        if (!picked) return
        const entity = picked.id
        const pid = entity && entity.properties && entity.properties.device_id
        const deviceId = pid && typeof pid.getValue === 'function' ? pid.getValue() : ''
        if (!deviceId) return
        this.openDeviceDetailById(deviceId)
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK)
    },
    openDeviceDetailById (deviceId) {
      const did = String(deviceId || '').trim()
      if (!did) return
      const base = `${window.location.origin}${window.location.pathname}`
      const nextUrl = `${base}#/device_list?device_id=${encodeURIComponent(did)}&embed=1&_t=${Date.now()}`
      if (this.detailFrameUrl === nextUrl && this.deviceCardVisible) return
      this.detailFrameUrl = nextUrl
      this.deviceCardVisible = true
    },
    handleDetailDialogClosed () {
      this.detailFrameUrl = ''
    },
    initMap3D () {
      try {
        this.map3dLoading = true
        this.loadingText = 'loading...'
        mars3d.Log.hasInfo(false)

        const mapOptions = {
          scene: {
            center: DEFAULT_SCENE_CENTER,
            sceneMode: mars3d.Cesium.SceneMode.SCENE3D,
            fxaa: false,
            highDynamicRange: false,
            requestRenderMode: true,
            maximumRenderTimeChange: Infinity
          },
          globe: {
            enableLighting: false,
            showGroundAtmosphere: false,
            depthTestAgainstTerrain: false
          },
          basemaps: [
            {
              id: 2021,
              name: '高德影像(经后端代理)',
              type: 'group',
              layers: [
                { name: '底图', type: 'xyz', url: '/api/device/map/tile/?style=6&x={x}&y={y}&z={z}' },
                { name: '注记', type: 'xyz', url: '/api/device/map/tile/?style=8&lang=zh_cn&x={x}&y={y}&z={z}' }
              ],
              show: true
            },
            {
              id: 2022,
              name: '高德矢量(经后端代理)',
              type: 'xyz',
              url: '/api/device/map/tile/?style=7&x={x}&y={y}&z={z}',
              show: false
            }
          ],
          control: {
            baseLayerPicker: false,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            vrButton: false,
            geocoder: false,
            homeButton: true,
            infoBox: false,
            sceneModePicker: false,
            navigationHelpButton: true,
            compass: true,
            zoom: true,
            distanceLegend: true,
            locationBar: true,
            mouseDownView: false
          }
        }

        this.map = new mars3d.Map('mars3dContainer', mapOptions)
        this.bindMapDeviceClick()

        const creditContainer = this.map?.viewer?.cesiumWidget?.creditContainer
        if (creditContainer) {
          creditContainer.style.display = 'none'
        }

        this.map.readyPromise.then(async () => {
          this.currentSceneMode = this.map.viewer.scene.mode === mars3d.Cesium.SceneMode.SCENE2D ? '2D' : '3D'
          this.applySceneModeVisuals(this.currentSceneMode)
          await this.loadAndRenderDevices()
          this.startMapPointsRefresh()
          // 首次进入首页默认将比例尺校准到1000公里
          this.tuneScaleAfterSwitch(this.currentSceneMode, () => {
            this.map3dLoading = false
          }, 1000000)
        }).catch((err) => {
          console.error('[mars3d] 地图加载失败', err)
          this.map3dLoading = false
          this.$message.error('地图加载失败，请稍后重试')
        })
      } catch (error) {
        console.error('[mars3d] 初始化失败', error)
        this.map3dLoading = false
        this.$message.error(`初始化失败: ${error.message || '未知错误'}`)
      }
    },

    switchSceneMode (mode) {
      if (!this.map || !this.map.viewer || this.isSwitchingScene) return
      if (this.currentSceneMode === mode) return

      const Cesium = mars3d.Cesium
      const viewer = this.map.viewer
      const scene = viewer.scene
      const camera = viewer.camera

      this.isSwitchingScene = true
      this.map3dLoading = true
      this.loadingText = mode === '2D' ? '2D地图加载中...' : '3D地图加载中...'

      if (this.pendingRenderTimer) {
        clearTimeout(this.pendingRenderTimer)
        this.pendingRenderTimer = null
      }

      const centerCartesian = camera.pickEllipsoid(
        new Cesium.Cartesian2(scene.canvas.clientWidth / 2, scene.canvas.clientHeight / 2),
        scene.globe.ellipsoid
      ) || camera.positionWC
      const centerCarto = Cesium.Cartographic.fromCartesian(centerCartesian)

      this.map.basemap = mode === '2D' ? 2022 : 2021
      this.applySceneModeVisuals(mode)

      const onMorphComplete = () => {
        try {
          const max2DLat = Cesium.Math.toRadians(80.0)
          const min2DLat = Cesium.Math.toRadians(-80.0)
          const clampedLat = Cesium.Math.clamp(centerCarto.latitude, min2DLat, max2DLat)
          const targetHeight = mode === '2D'
            ? 3000000
            : 15000000

          camera.setView({
            destination: Cesium.Cartesian3.fromRadians(centerCarto.longitude, clampedLat, targetHeight),
            orientation: mode === '2D'
              ? { heading: 0, pitch: -Cesium.Math.PI_OVER_TWO, roll: 0 }
              : undefined
          })
        } catch (e) {
          console.warn('[scene] setView after morph failed', e)
        }

        this.pendingRenderTimer = setTimeout(() => {
          this.currentSceneMode = mode
          this.renderDevices(this.latestDeviceList, { forceRebuild: true })
          this.tuneScaleAfterSwitch(mode, () => {
            this.isSwitchingScene = false
            this.map3dLoading = false
            this.loadingText = '地图加载中...'
            this.pendingRenderTimer = null
          })
        }, 120)
      }

      scene.morphComplete.addEventListener(onMorphComplete)

      if (mode === '2D') {
        scene.morphTo2D(0.35)
      } else {
        scene.morphTo3D(0.35)
      }

      setTimeout(() => {
        scene.morphComplete.removeEventListener(onMorphComplete)
      }, 1800)
    },

    tuneScaleAfterSwitch (mode, done, forcedTargetMeters = null) {
      if (!this.map || !this.map.viewer) {
        if (done) done()
        return
      }

      if (this.scaleTuneTimer) {
        clearInterval(this.scaleTuneTimer)
        this.scaleTuneTimer = null
      }

      const viewer = this.map.viewer
      const targetMeters = forcedTargetMeters || (mode === '2D' ? 300000 : 500000) // 2D=300公里, 3D=500公里
      let attempts = 0
      let stableLabelCount = 0
      let lastLabel = ''

      const parseScaleToMeters = (text) => {
        if (!text) return null
        const value = parseFloat(text)
        if (!Number.isFinite(value)) return null
        if (text.includes('公里')) return value * 1000
        if (text.includes('米')) return value
        return null
      }

      const finish = () => {
        clearInterval(this.scaleTuneTimer)
        this.scaleTuneTimer = null
        if (done) done()
      }

      const step = () => {
        attempts += 1
        const label = document.querySelector('.mars3d-distance-legend .legend-label')?.innerText || ''
        const currentMeters = parseScaleToMeters(label)

        if (label === lastLabel) stableLabelCount += 1
        else stableLabelCount = 0
        lastLabel = label

        if (!currentMeters) {
          if (attempts >= 18) finish()
          return
        }

        const diff = currentMeters - targetMeters
        if (Math.abs(diff) <= targetMeters * 0.18 || attempts >= 18 || stableLabelCount >= 3) {
          finish()
          return
        }

        const delta = Math.max(viewer.camera.positionCartographic.height * 0.2, 120000)
        if (diff > 0) viewer.camera.zoomIn(delta)
        else viewer.camera.zoomOut(delta)
      }

      this.scaleTuneTimer = setInterval(step, 180)
      step()
    },

    applySceneModeVisuals (mode) {
      if (!this.map || !this.map.viewer) return
      const viewer = this.map.viewer
      const is2D = mode === '2D'

      viewer.shadows = false
      // 3D开启日照，2D关闭
      viewer.scene.globe.enableLighting = !is2D
      viewer.scene.fog.enabled = false
      if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = !is2D
      viewer.scene.backgroundColor = mars3d.Cesium.Color.fromCssColorString('#dbeafe')
      viewer.scene.globe.baseColor = mars3d.Cesium.Color.fromCssColorString('#dbeafe')
      viewer.scene.requestRenderMode = !is2D
      viewer.scene.maximumRenderTimeChange = is2D ? 0 : Infinity
      viewer.scene.screenSpaceCameraController.maximumZoomDistance = is2D ? 80000000 : 60000000
      viewer.scene.screenSpaceCameraController.minimumZoomDistance = is2D ? 10000 : 100
    },

    startMapPointsRefresh () {
      if (this.mapPointsRefreshTimer) return
      this.mapPointsRefreshTimer = setInterval(() => {
        this.loadAndRenderDevices({ silent: true })
      }, 20000)
    },
    async loadAndRenderDevices (options = {}) {
      const { silent = false } = options
      const reqSeq = ++this.mapPointsReqSeq
      try {
        const { data: res } = await this.$axios.get('/device/map/points/', {
          timeout: 15000
        })

        if (reqSeq !== this.mapPointsReqSeq) return

        if (res.code !== 200) {
          if (!silent) this.$message.warning(res.msg || '设备数据加载失败')
          return
        }

        const list = (res.data && res.data.device_list) || []
        this.latestDeviceList = list
        this.renderDevices(list)
      } catch (error) {
        if (reqSeq !== this.mapPointsReqSeq) return
        console.error('[welcome] 设备上图失败', error)
        if (!silent) this.$message.warning('设备数据加载失败')
      }
    },

    createDeviceEntity (device, index) {
      if (!this.map || !this.map.viewer) return null
      const Cesium = mars3d.Cesium
      const lat = Number(device.latitude)
      const lng = Number(device.longitude)
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null

      const is2D = this.currentSceneMode === '2D'
      const entityId = `device-${String(device.device_id).trim()}`
      return this.map.viewer.entities.add({
        id: entityId,
        position: Cesium.Cartesian3.fromDegrees(lng, lat, is2D ? 0 : MARKER_HEIGHT),
        billboard: {
          image: this.markerImage,
          width: 30,
          height: 30,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          scaleByDistance: new Cesium.NearFarScalar(8.0e5, 1.2, 2.5e7, 0.45),
          translucencyByDistance: new Cesium.NearFarScalar(1.0e6, 1.0, 2.8e7, 0.25),
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 3.2e7),
          scale: is2D
            ? 1.0
            : new Cesium.CallbackProperty(() => {
              const now = Date.now() * 0.0032
              return 1.0 + Math.sin(now + index * 0.9) * 0.12
            }, false)
        },
        label: {
          text: device.device_name || device.device_id,
          font: is2D ? '13px sans-serif' : '12px sans-serif',
          fillColor: Cesium.Color.fromCssColorString('#fee2e2'),
          outlineColor: Cesium.Color.fromCssColorString('#7f1d1d'),
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, is2D ? -20 : -30),
          scaleByDistance: new Cesium.NearFarScalar(1.0e6, 1.0, 2.2e7, 0.35),
          translucencyByDistance: new Cesium.NearFarScalar(1.0e6, 1.0, 2.4e7, 0.1),
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 2.6e7)
        },
        ...(is2D
          ? {}
          : {
              polyline: {
                positions: [
                  Cesium.Cartesian3.fromDegrees(lng, lat, 0),
                  Cesium.Cartesian3.fromDegrees(lng, lat, MARKER_HEIGHT)
                ],
                width: 1,
                material: Cesium.Color.fromCssColorString('#f87171'),
                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0.0, 2.2e7)
              }
            }),
        properties: {
          is_cluster: false,
          device_id: device.device_id,
          device_name: device.device_name,
          device_type: device.device_type,
          status_name: device.status_name,
          ownership: device.ownership,
          packet_time: device.latest_packet_time || '',
          last_report_time: device.last_report_time
        }
      })
    },
    clusterDevices (devices) {
      return devices.map((d) => ({
        type: 'single',
        device: d,
        id: `device-${String(d.device_id || '').trim()}`
      }))
    },
    countByPrefix (devices, prefix) {
      const matched = devices.filter(d => {
        const did = String(d.device_id || d.devid || '').trim()
        return did.startsWith(prefix)
      })
      const online = matched.filter(d => Number(d.status) === 1).length
      return {
        total: matched.length,
        online,
        offline: matched.length - online
      }
    },
    updateDeviceStats (devices) {
      const allOnline = devices.filter(d => Number(d.status) === 1).length
      this.deviceStats.total = {
        total: devices.length,
        online: allOnline,
        offline: devices.length - allOnline
      }
      this.deviceStats.domestic = this.countByPrefix(devices, '01')
      this.deviceStats.south = this.countByPrefix(devices, '02')
      this.deviceStats.north = this.countByPrefix(devices, '03')
    },
    renderDevices (deviceList, options = {}) {
      if (!this.map || !this.map.viewer) return
      const { forceRebuild = false } = options

      const deviceMap = new Map()
      deviceList.forEach((device) => {
        const key = String(device.device_id || '').trim()
        if (!key) return
        const exists = deviceMap.get(key)
        if (!exists) {
          deviceMap.set(key, device)
          return
        }
        const t1 = new Date(exists.latest_packet_time || exists.last_report_time || 0).getTime() || 0
        const t2 = new Date(device.latest_packet_time || device.last_report_time || 0).getTime() || 0
        if (t2 >= t1) deviceMap.set(key, device)
      })

      const uniqueDevices = Array.from(deviceMap.values())
      this.updateDeviceStats(uniqueDevices)

      if (forceRebuild) this.clearDeviceEntities()

      const renderUnits = this.clusterDevices(uniqueDevices)
      const nextIds = new Set(renderUnits.map(item => item.id))
      if (!forceRebuild) {
        this.deviceEntities = this.deviceEntities.filter((entity) => {
          if (!entity || !entity.id || !nextIds.has(entity.id)) {
            if (entity) this.map.viewer.entities.remove(entity)
            this.deviceEntityMap.delete(entity && entity.id)
            return false
          }
          return true
        })
      }

      renderUnits.forEach((item, index) => {
        const id = item.id
        const oldEntity = forceRebuild ? null : this.deviceEntityMap.get(id)
        if (oldEntity) {
          this.map.viewer.entities.remove(oldEntity)
          this.deviceEntityMap.delete(id)
          this.deviceEntities = this.deviceEntities.filter(e => e && e.id !== id)
        }

        const created = this.createDeviceEntity(item.device, index)
        if (!created) return
        this.deviceEntityMap.set(id, created)
        this.deviceEntities.push(created)
      })
    },

    clearDeviceEntities () {
      if (!this.map || !this.map.viewer || !this.deviceEntities.length) {
        this.deviceEntities = []
        this.deviceEntityMap.clear()
        return
      }

      this.deviceEntities.forEach((entity) => {
        this.map.viewer.entities.remove(entity)
      })
      this.deviceEntities = []
      this.deviceEntityMap.clear()
    }
  }
}
</script>

<style scoped>
.welcome-page {
  position: relative;
  height: calc(100vh - 140px);
  min-height: 640px;
  border-radius: 14px;
  overflow: hidden;
  background: #000;
}

.welcome-page-fullscreen {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  border-radius: 0;
  z-index: 3000;
}

.map-container {
  width: 100%;
  height: 100%;
}

.map-container-hidden {
  visibility: hidden;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 20px;
  z-index: 1000;
}

.map-legend {
  position: absolute;
  top: 16px;
  left: 16px;
  min-width: 220px;
  padding: 0;
  color: #f8fafc;
  background: transparent;
  border: none;
  box-shadow: none;
  backdrop-filter: none;
}

.legend-inline-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.55);
}

.legend-total-label {
  font-size: 13px;
  color: #fde68a;
}

.legend-total-value {
  font-size: 22px;
  line-height: 1;
  font-weight: 800;
  color: #ffffff;
  min-width: 32px;
}

.legend-inline-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #e5e7eb;
}

.legend-inline-status-offline {
  font-size: 11px;
  opacity: 0.95;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.online {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.9);
}

.status-dot.offline {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.9);
}

.scene-tools {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.scene-tools-label {
  font-size: 12px;
  color: #fecaca;
  margin-right: 4px;
}

.scene-btn {
  border: 1px solid rgba(248, 113, 113, 0.45);
  background: rgba(15, 23, 42, 0.55);
  color: #fecaca;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.scene-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.scene-btn.active {
  color: #fff;
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.4);
}

.fullscreen-btn {
  width: 28px;
  height: 24px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-icon {
  position: relative;
  width: 12px;
  height: 12px;
  display: inline-block;
}

.fullscreen-icon::before,
.fullscreen-icon::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.fullscreen-icon.is-enter::before {
  border-top: 2px solid #fecaca;
  border-left: 2px solid #fecaca;
  left: -2px;
  top: -2px;
}

.fullscreen-icon.is-enter::after {
  border-right: 2px solid #fecaca;
  border-bottom: 2px solid #fecaca;
  right: -2px;
  bottom: -2px;
}

.fullscreen-icon.is-exit::before {
  border-top: 2px solid #fecaca;
  border-right: 2px solid #fecaca;
  right: 2px;
  top: 2px;
  width: 8px;
  height: 8px;
}

.fullscreen-icon.is-exit::after {
  border-left: 2px solid #fecaca;
  border-bottom: 2px solid #fecaca;
  left: 2px;
  bottom: 2px;
  width: 8px;
  height: 8px;
}

::v-deep .device-detail-embed-dialog {
  margin: 0 !important;
}

::v-deep .device-detail-embed-dialog .el-dialog {
  margin: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  max-width: none !important;
  border-radius: 0;
  overflow: hidden;
}

::v-deep .device-detail-embed-dialog .el-dialog__header {
  display: none;
}

::v-deep .device-detail-embed-dialog .el-dialog__body {
  position: relative;
  padding: 0;
  height: 100vh;
  overflow: hidden;
}

.floating-close-btn {
  position: absolute;
  top: 10px;
  right: 14px;
  z-index: 10;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.65);
  color: #fff;
  font-size: 24px;
  line-height: 34px;
  cursor: pointer;
}

.detail-embed-frame {
  width: 100%;
  height: 100vh;
  display: block;
  border: none;
  background: #fff;
}
</style>
