<template>
  <div class="welcome-page">
    <div id="mars3dContainer" class="map-container"></div>
    <div v-if="map3dLoading" class="loading-overlay">Loading...</div>
  </div>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
import * as mars3d from 'mars3d'

export default {
  name: 'Welcome',
  data () {
    return {
      map3dLoading: true,
      map: null
    }
  },
  mounted () {
    this.$nextTick(() => {
      this.initMap3D()
    })
  },
  beforeDestroy () {
    if (this.map) {
      this.map.destroy()
      this.map = null
    }
  },
  methods: {
    initMap3D () {
      try {
        this.map3dLoading = true
        mars3d.Log.hasInfo(false)

        const mapOptions = {
          scene: {
            center: { lat: 31.84, lng: 117.22, alt: 2800000, heading: 0, pitch: -60 },
            fxaa: false,
            highDynamicRange: false,
            requestRenderMode: true,
            maximumRenderTimeChange: Infinity
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
            }
          ],
          control: {
            baseLayerPicker: false,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            vrButton: false,
            geocoder: false,
            homeButton: false,
            infoBox: false,
            sceneModePicker: false,
            navigationHelpButton: false
          }
        }

        this.map = new mars3d.Map('mars3dContainer', mapOptions)
        this.map.readyPromise.then(() => {
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

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 20px;
}
</style>
