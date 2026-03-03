<template>
  <div class="welcome-page">
    <div id="mars3dContainer" class="map-container" :class="{ 'map-container-hidden': isSwitchingScene }"></div>
    <div v-if="map3dLoading" class="loading-overlay">{{ loadingText }}</div>

    <div class="map-legend">
      <div class="legend-total">
        <div class="legend-total-label">设备总数</div>
        <div class="legend-total-value">{{ deviceStats.total }}</div>
      </div>
      <div class="legend-status-row">
        <span class="status-dot online"></span>
        <span>在线 {{ deviceStats.online }}</span>
      </div>
      <div class="legend-status-row">
        <span class="status-dot offline"></span>
        <span>离线 {{ deviceStats.offline }}</span>
      </div>

      <div class="scene-tools">
        <span class="scene-tools-label">场景</span>
        <button class="scene-btn" :class="{ active: currentSceneMode === '3D' }" :disabled="isSwitchingScene" @click="switchSceneMode('3D')">3D</button>
        <button class="scene-btn" :class="{ active: currentSceneMode === '2D' }" :disabled="isSwitchingScene" @click="switchSceneMode('2D')">2D</button>
      </div>
    </div>
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
  data () {
    return {
      map3dLoading: true,
      map: null,
      deviceEntities: [],
      deviceStats: {
        total: 0,
        online: 0,
        offline: 0
      },
      markerImage: locationIcon,
      currentSceneMode: '3D',
      latestDeviceList: [],
      isSwitchingScene: false,
      pendingRenderTimer: null,
      scaleTuneTimer: null,
      loadingText: 'loading...'
    }
  },
  mounted () {
    this.$nextTick(() => {
      this.initMap3D()
    })
  },
  beforeDestroy () {
    if (this.pendingRenderTimer) {
      clearTimeout(this.pendingRenderTimer)
      this.pendingRenderTimer = null
    }
    if (this.scaleTuneTimer) {
      clearInterval(this.scaleTuneTimer)
      this.scaleTuneTimer = null
    }
    this.clearDeviceEntities()
    if (this.map) {
      this.map.destroy()
      this.map = null
    }
  },
  methods: {
    initMap3D () {
      try {
        this.map3dLoading = true
        this.loadingText = '地图加载中...'
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
              type: 'group',
              layers: [
                { name: '底图', type: 'xyz', url: '/api/device/map/tile/?style=7&x={x}&y={y}&z={z}' },
                { name: '注记', type: 'xyz', url: '/api/device/map/tile/?style=8&lang=zh_cn&x={x}&y={y}&z={z}' }
              ],
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
            sceneModePicker: true,
            navigationHelpButton: true,
            compass: true,
            zoom: true,
            distanceLegend: true,
            locationBar: true,
            mouseDownView: false
          }
        }

        this.map = new mars3d.Map('mars3dContainer', mapOptions)

        const creditContainer = this.map?.viewer?.cesiumWidget?.creditContainer
        if (creditContainer) {
          creditContainer.style.display = 'none'
        }

        this.map.readyPromise.then(async () => {
          this.currentSceneMode = this.map.viewer.scene.mode === mars3d.Cesium.SceneMode.SCENE2D ? '2D' : '3D'
          this.applySceneModeVisuals(this.currentSceneMode)
          await this.loadAndRenderDevices()
          this.map3dLoading = false
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
          console.log('[scene] morph complete setView', { mode, targetHeight })
        } catch (e) {
          console.warn('[scene] setView after morph failed', e)
        }

        this.pendingRenderTimer = setTimeout(() => {
          this.currentSceneMode = mode
          this.renderDevices(this.latestDeviceList)
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
      console.log('[scene] switch requested', {
        mode,
        currentScaleLabel: document.querySelector('.mars3d-distance-legend .legend-label')?.innerText
      })

      setTimeout(() => {
        scene.morphComplete.removeEventListener(onMorphComplete)
      }, 1800)
    },

    tuneScaleAfterSwitch (mode, done) {
      if (!this.map || !this.map.viewer) {
        if (done) done()
        return
      }

      if (this.scaleTuneTimer) {
        clearInterval(this.scaleTuneTimer)
        this.scaleTuneTimer = null
      }

      const viewer = this.map.viewer
      const targetMeters = mode === '2D' ? 100000 : 500000 // 2D=100公里, 3D=500公里
      let attempts = 0

      const parseScaleToMeters = (text) => {
        if (!text) return null
        const value = parseFloat(text)
        if (!Number.isFinite(value)) return null
        if (text.includes('公里')) return value * 1000
        if (text.includes('米')) return value
        return null
      }

      const step = () => {
        attempts += 1
        const label = document.querySelector('.mars3d-distance-legend .legend-label')?.innerText || ''
        const currentMeters = parseScaleToMeters(label)

        if (!currentMeters) {
          if (attempts >= 20) {
            clearInterval(this.scaleTuneTimer)
            this.scaleTuneTimer = null
            if (done) done()
          }
          return
        }

        const diff = currentMeters - targetMeters
        if (Math.abs(diff) <= targetMeters * 0.18 || attempts >= 20) {
          console.log('[scene] scale tuned', { mode, label, currentMeters, targetMeters, attempts })
          clearInterval(this.scaleTuneTimer)
          this.scaleTuneTimer = null
          if (done) done()
          return
        }

        const delta = Math.max(viewer.camera.positionCartographic.height * 0.22, 150000)
        if (diff > 0) {
          // 比例尺偏大（如1000公里），需要拉近
          viewer.camera.zoomIn(delta)
        } else {
          // 比例尺偏小（如20公里），需要拉远
          viewer.camera.zoomOut(delta)
        }
      }

      this.scaleTuneTimer = setInterval(step, 120)
      step()
    },

    applySceneModeVisuals (mode) {
      if (!this.map || !this.map.viewer) return
      const viewer = this.map.viewer
      const is2D = mode === '2D'

      viewer.shadows = false
      viewer.scene.globe.enableLighting = false
      viewer.scene.fog.enabled = false
      if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = !is2D
      viewer.scene.backgroundColor = mars3d.Cesium.Color.fromCssColorString('#dbeafe')
      viewer.scene.globe.baseColor = mars3d.Cesium.Color.fromCssColorString('#dbeafe')
      viewer.scene.requestRenderMode = !is2D
      viewer.scene.maximumRenderTimeChange = is2D ? 0 : Infinity
      viewer.scene.screenSpaceCameraController.maximumZoomDistance = is2D ? 80000000 : 60000000
      viewer.scene.screenSpaceCameraController.minimumZoomDistance = is2D ? 10000 : 100
    },

    async loadAndRenderDevices () {
      try {
        const { data: res } = await this.$axios.get('/device/map/points/', {
          timeout: 15000
        })

        if (res.code !== 200) {
          this.$message.warning(res.msg || '设备数据加载失败')
          return
        }

        const list = (res.data && res.data.device_list) || []
        this.latestDeviceList = list
        this.renderDevices(list)
      } catch (error) {
        console.error('[welcome] 设备上图失败', error)
        this.$message.warning('设备数据加载失败')
      }
    },

    renderDevices (deviceList) {
      if (!this.map || !this.map.viewer) return
      const Cesium = mars3d.Cesium
      this.clearDeviceEntities()

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
      this.deviceStats.total = uniqueDevices.length
      this.deviceStats.online = uniqueDevices.filter(d => Number(d.status) === 1).length
      this.deviceStats.offline = this.deviceStats.total - this.deviceStats.online

      uniqueDevices.forEach((device, index) => {
        const lat = Number(device.latitude)
        const lng = Number(device.longitude)
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return

        const is2D = this.currentSceneMode === '2D'
        const entityId = `device-${String(device.device_id).trim()}`
        const existed = this.map.viewer.entities.getById(entityId)
        if (existed) this.map.viewer.entities.remove(existed)

        const entity = this.map.viewer.entities.add({
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
            device_id: device.device_id,
            device_name: device.device_name,
            device_type: device.device_type,
            status_name: device.status_name,
            ownership: device.ownership,
            packet_time: device.latest_packet_time || '',
            last_report_time: device.last_report_time
          }
        })

        this.deviceEntities.push(entity)
      })
    },

    clearDeviceEntities () {
      if (!this.map || !this.map.viewer || !this.deviceEntities.length) {
        this.deviceEntities = []
        return
      }

      this.deviceEntities.forEach((entity) => {
        this.map.viewer.entities.remove(entity)
      })
      this.deviceEntities = []
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
  top: 14px;
  right: 14px;
  min-width: 220px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(9, 12, 21, 0.75);
  border: 1px solid rgba(248, 113, 113, 0.55);
  color: #f8fafc;
  backdrop-filter: blur(4px);
}

.legend-total {
  margin-top: 4px;
  margin-bottom: 8px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.legend-total-label {
  font-size: 12px;
  color: #fecaca;
}

.legend-total-value {
  font-size: 20px;
  line-height: 1;
  font-weight: 700;
  color: #fee2e2;
}

.legend-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 12px;
  color: #fecaca;
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
</style>
