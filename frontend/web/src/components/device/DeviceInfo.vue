<template>
  <div :class="['device-page', { 'device-page-embed': isEmbedMode }]">
    <el-breadcrumb v-if="!isEmbedMode" separator-class="el-icon-arrow-right" class="breadcrumb">
      <el-breadcrumb-item to="/home">首页</el-breadcrumb-item>
      <el-breadcrumb-item>设备管理</el-breadcrumb-item>
      <el-breadcrumb-item>设备列表</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card v-if="!isEmbedMode" shadow="never" class="filter-card">
      <el-row :gutter="12" class="toolbar">
        <el-col :span="8">
          <el-input v-model="searchKeyword" placeholder="输入设备名称或设备ID搜索" clearable @clear="search" @keyup.enter.native="search">
            <el-button slot="append" icon="el-icon-search" @click="search" />
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-input v-model="searchOwnership" placeholder="输入归属区域过滤" clearable @clear="search" @keyup.enter.native="search">
            <el-button slot="append" icon="el-icon-search" @click="search" />
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="searchStatus" placeholder="在线状态" clearable @change="search">
            <el-option label="在线" value="1" />
            <el-option label="离线" value="0" />
          </el-select>
        </el-col>
        <el-col :span="6" class="toolbar-buttons"></el-col>
      </el-row>
    </el-card>

    <el-card v-if="!isEmbedMode" shadow="never" class="table-card">
      <el-table v-loading="tableLoading" :data="tableData" border class="device-table" highlight-current-row empty-text="暂无设备数据">
        <el-table-column prop="id" label="序号" width="70" />
        <el-table-column prop="name" label="设备名称" min-width="140" />
        <el-table-column prop="devid" label="设备序列号" width="150" />
        <el-table-column prop="iridiumid" label="铱星号" width="120" />
        <el-table-column prop="sensorflag" label="传感器标志位" min-width="140" />
        <el-table-column prop="lat" label="纬度" width="110" />
        <el-table-column prop="lon" label="经度" width="110" />
        <el-table-column prop="workstate" label="工作状态" width="100" />
        <el-table-column prop="display" label="同步标志位" width="110" />
        <el-table-column prop="ownership" label="归属单位" min-width="140" />
        <el-table-column prop="last_report_time" label="最后上报时间" width="170" />
        <el-table-column prop="status_name" label="状态" width="90">
          <template slot-scope="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">
              {{ scope.row.status_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="showData(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="page"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <el-dialog :visible.sync="dataVisible" :width="isEmbedMode ? '100%' : '1200px'" :fullscreen="isEmbedMode" :show-close="!isEmbedMode" :modal="!isEmbedMode" :close-on-click-modal="!isEmbedMode" top="3vh" class="device-detail-dialog" @opened="onDetailDialogOpened" @closed="onDetailDialogClosed">
      <template slot="title">
        <div class="dialog-title-wrap">
          <span class="dialog-title-main">设备详情</span>
          <span class="dialog-title-sub">{{ detailSubtitle }}</span>
        </div>
      </template>
      <el-row :gutter="16" class="detail-grid">
        <el-col :span="24">
          <el-card shadow="never" class="inner-card">
            <div slot="header" class="latest-header">
              <span>最新数据</span>
            </div>

            <div v-if="keyFieldList.length" class="field-list key-fields">
              <div v-for="item in keyFieldList" :key="item.field" class="field-item">
                <span class="field-label">{{ formatFieldLabel(item.label) }}：</span>
                <span class="field-value">{{ showValue(item.value) }}</span>
              </div>
            </div>

            <el-empty v-else description="暂无最新数据" :image-size="60" />

            <el-collapse v-if="otherFieldList.length" class="more-collapse">
              <el-collapse-item name="more">
                <template slot="title">
                  <span class="collapse-title">更多字段（{{ otherFieldList.length }}项）</span>
                </template>
                <div class="field-list other-fields">
                  <div v-for="item in otherFieldList" :key="item.field" class="field-item">
                    <span class="field-label">{{ formatFieldLabel(item.label) }}：</span>
                    <span class="field-value">{{ showValue(item.value) }}</span>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </el-col>

        <el-col :span="24">
          <el-card shadow="never" class="inner-card analysis-card">
            <div slot="header" class="analysis-header">
              <div class="analysis-header-left">
                <span>设备数据分析</span>
              </div>
              <div class="trend-tools analysis-tools">
                <el-radio-group v-model="trendRangeType" size="mini" @change="handleTrendRangeChange">
                  <el-radio-button label="1d">1天</el-radio-button>
                  <el-radio-button label="7d">7天</el-radio-button>
                  <el-radio-button label="30d">30天</el-radio-button>
                  <el-radio-button label="1y">1年</el-radio-button>
                  <el-radio-button label="custom">自定义</el-radio-button>
                </el-radio-group>
                <el-date-picker
                  v-if="trendRangeType === 'custom'"
                  v-model="trendDateRange"
                  type="daterange"
                  unlink-panels
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="yyyy-MM-dd"
                  size="mini"
                  style="margin-left: 8px;"
                  @change="handleCustomDateChange"
                />
              </div>
            </div>
            <el-row :gutter="16" class="analysis-grid">
              <el-col :span="12">
                <div class="panel-title panel-title-map">
                  <span>设备轨迹</span>
                  <el-button type="text" class="map-zoom-btn" @click="mapZoomVisible = true">扩展</el-button>
                </div>
                <div class="track-map-wrap">
                  <div ref="trackMapContainer" class="real-track-map" />
                  <div v-if="trackLoading" class="panel-empty">轨迹加载中...</div>
                  <div v-else-if="trackLoaded && !trackPoints.length" class="panel-empty">暂无轨迹数据</div>
                  <div v-if="trackHover.visible" class="track-tooltip" :style="trackTooltipMainStyle">
                    <div>{{ trackHover.time || '-' }}</div>
                    <div>纬度：{{ trackHover.lat }}</div>
                    <div>经度：{{ trackHover.lng }}</div>
                  </div>
                </div>

              </el-col>

              <el-col :span="12">
                <div class="panel-title panel-title-chart">
                  <span>图表分析</span>
                  <el-popover placement="bottom-end" width="340" trigger="click">
                    <div class="field-selector-wrap">
                      <div class="field-selector-title">选择分析指标（最多3个）</div>
                      <el-checkbox-group v-model="selectedChartFields" @change="handleChartFieldChange">
                        <el-checkbox
                          v-for="item in availableChartFields"
                          :key="item.field"
                          :label="item.field"
                        >{{ item.label }}</el-checkbox>
                      </el-checkbox-group>
                    </div>
                    <el-button slot="reference" type="text" class="field-selector-btn">选择指标</el-button>
                  </el-popover>
                </div>
                <div ref="trendChart" class="trend-chart" />
                <div v-if="!chartSeries.length" class="panel-empty panel-empty-chart">暂无可绘制指标</div>
              </el-col>
            </el-row>

            <div class="analysis-playback" v-if="trackPoints.length">
              <div class="playback-line-row">
                <div class="playback-slider-wrap">
                  <el-slider
                    class="playback-slider"
                    v-model="playbackProgress"
                    :min="0"
                    :max="Math.max(trackPoints.length - 1, 0)"
                    :step="1"
                    :show-tooltip="false"
                    @input="handlePlaybackProgressInput"
                    @change="handlePlaybackProgressChange"
                  />
                </div>
                <div class="playback-actions">
                  <el-select v-model="playbackSpeed" size="mini" class="speed-select" @change="handlePlaybackSpeedChange">
                    <el-option :value="0.5" label="0.5x" />
                    <el-option :value="1" label="1x" />
                    <el-option :value="2" label="2x" />
                    <el-option :value="4" label="4x" />
                  </el-select>
                  <button :class="['play-toggle-btn', { playing: isTrackPlaying }]" type="button" @click="toggleTrackPlayback">
                    <span v-if="!isTrackPlaying" class="icon-play" />
                    <span v-else class="icon-stop" />
                  </button>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="24">
          <el-card shadow="never" class="inner-card">
            <div slot="header" class="trend-header">
              <span>设备详细数据</span>
            </div>
            <el-table :data="trendPoints" size="mini" height="260" border class="trend-table" empty-text="暂无趋势数据">
              <el-table-column prop="time" label="数据包解析时间" width="170" fixed="left" show-overflow-tooltip />
              <el-table-column v-for="col in sortedTrendColumns" :key="col.field" :prop="col.field" :label="formatFieldLabel(col.label)" min-width="120" show-overflow-tooltip />
            </el-table>
            <el-pagination
              class="pagination"
              background
              layout="total, sizes, prev, pager, next"
              :current-page="trendPage"
              :page-size="trendPageSize"
              :page-sizes="[50, 100, 200, 500]"
              :total="trendTotal"
              @size-change="handleTrendSizeChange"
              @current-change="handleTrendPageChange"
            />
          </el-card>
        </el-col>
      </el-row>
    </el-dialog>

    <el-dialog
      :visible.sync="mapZoomVisible"
      title="设备轨迹"
      width="88vw"
      top="4vh"
      append-to-body
      class="map-zoom-dialog"
      @opened="syncTrackMapRender"
    >
      <div class="track-map-wrap map-zoom-wrap">
        <div ref="trackMapZoomContainer" class="real-track-map" />
        <div v-if="trackLoading" class="panel-empty">轨迹加载中...</div>
        <div v-else-if="trackLoaded && !trackPoints.length" class="panel-empty">暂无轨迹数据</div>
        <div v-if="trackHover.visible" class="track-tooltip" :style="trackTooltipZoomStyle">
          <div>{{ trackHover.time || '-' }}</div>
          <div>纬度：{{ trackHover.lat }}</div>
          <div>经度：{{ trackHover.lng }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
/* eslint vue/multi-word-component-names: "off" */
export default {
  data () {
    return {
      tableData: [],
      tableLoading: false,
      total: 0,
      page: 1,
      pageSize: 10,
      searchKeyword: '',
      searchOwnership: '',
      searchStatus: '',
      dataVisible: false,
      currentDevice: {},
      currentSourceTable: '',
      latestFieldList: [],
      keyFieldList: [],
      otherFieldList: [],
      trendColumns: [],
      trendPoints: [],
      chartPoints: [],
      trendDateRange: [],
      trendRangeType: '1y',
      trendPage: 1,
      trendPageSize: 100,
      trendTotal: 0,
      trackPoints: [],
      trackLoading: false,
      trackLoaded: false,
      trendChartIns: null,
      chartSeries: [],
      availableChartFields: [],
      selectedChartFields: [],
      activeTrackIndex: -1,
      trackHover: {
        visible: false,
        time: '',
        lat: '-',
        lng: '-'
      },
      trackHoverMainPos: { x: 50, y: 50 },
      trackHoverZoomPos: { x: 50, y: 50 },
      isTrackPlaying: false,
      trackPlayTimer: null,
      playbackProgress: 0,
      playbackSpeed: 1,
      mapZoomVisible: false,
      trackMapIns: null,
      trackMapZoomIns: null,
      trackMapPathLayer: null,
      trackMapZoomPathLayer: null,
      trackMapMarkerLayer: null,
      trackMapZoomMarkerLayer: null
    }
  },
  computed: {
    isEmbedMode () {
      return String(this.$route.query.embed || '') === '1'
    },
    detailSubtitle () {
      if (!this.currentDevice.device_id) return ''
      const base = `${this.currentDevice.device_name || this.currentDevice.device_id} - ${this.currentDevice.device_id}`
      return this.currentSourceTable ? `${base}（${this.currentSourceTable}）` : base
    },
    sortedTrendColumns () {
      if (!this.trendColumns.length) return []
      const filteredColumns = this.trendColumns.filter(col => col.field !== 'time' && col.field !== 'packet_time')
      if (!this.keyFieldList.length) return filteredColumns
      const keyFields = this.keyFieldList.map(item => item.field)
      const keyCols = filteredColumns.filter(col => keyFields.includes(col.field))
      const otherCols = filteredColumns.filter(col => !keyFields.includes(col.field))
      return [...keyCols, ...otherCols]
    },
    trackTooltipMainStyle () {
      return this.getTrackTooltipStyle(this.trackHoverMainPos)
    },
    trackTooltipZoomStyle () {
      return this.getTrackTooltipStyle(this.trackHoverZoomPos)
    }
  },
  created () {
    this.initDefaultYearRange()
    if (!this.isEmbedMode) {
      this.getTableData()
    }
  },
  watch: {
    '$route.query.device_id': {
      immediate: true,
      handler (val) {
        const did = String(val || '').trim()
        if (!did) return
        this.tryOpenDeviceFromRoute(did)
      }
    }
  },
  mounted () {
    window.addEventListener('resize', this.handleWindowResize)
    this.$nextTick(() => this.initTrackMap())
  },
  beforeDestroy () {
    window.removeEventListener('resize', this.handleWindowResize)
    this.stopTrackPlayback()
    this.destroyTrendChart()
    this.destroyTrackMap()
    this.destroyTrackMapZoom()
  },
  methods: {
    getTrackTooltipStyle (pos) {
      const x = Number(pos && pos.x)
      const y = Number(pos && pos.y)
      const safeX = Number.isFinite(x) ? Math.max(2, Math.min(98, x)) : 50
      const safeY = Number.isFinite(y) ? Math.max(6, Math.min(94, y)) : 50

      const style = {
        left: `${safeX}%`,
        top: `${safeY}%`
      }

      const translateX = safeX < 18 ? '0%' : (safeX > 82 ? '-100%' : '-50%')
      const translateY = safeY <= 18 ? '12px' : 'calc(-100% - 10px)'
      style.transform = `translate(${translateX}, ${translateY})`
      return style
    },
    initDefaultYearRange () {
      this.trendRangeType = '1y'
      this.updateTrendDateRange()
    },
    updateTrendDateRange () {
      const now = new Date()
      const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
      let startDate
      switch (this.trendRangeType) {
        case '1d':
          startDate = new Date(endDate.getTime() - 24 * 60 * 60 * 1000)
          break
        case '7d':
          startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000)
          break
        case '30d':
          startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000)
          break
        case '1y':
          startDate = new Date(endDate.getTime() - 365 * 24 * 60 * 60 * 1000)
          break
        case 'custom':
          return
        default:
          startDate = new Date(now.getFullYear(), 0, 1, 0, 0, 0)
      }
      this.trendDateRange = [this.formatDate(startDate), this.formatDate(endDate)]
    },
    formatDate (date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    handleTrendRangeChange (value) {
      if (value !== 'custom') {
        this.updateTrendDateRange()
        this.loadAnalysisByDateRange()
        return
      }
      const now = new Date()
      const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
      const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000)
      this.trendDateRange = [this.formatDate(startDate), this.formatDate(endDate)]
    },
    handleCustomDateChange (value) {
      if (value && value.length === 2) this.loadAnalysisByDateRange()
    },
    splitLatestFields () {
      const highPriority = ['time', 'packet_time', 'latitude', 'longitude', 'lat', 'lon', 'temp', 'board_temp', 'air_temp', 'humidity', 'air_humid', 'pressure', 'atmosphere', 'wind_speed', 'wind_direct', 'voltage', 'board_voltage']
      const sorted = [...this.latestFieldList].sort((a, b) => {
        const ai = highPriority.indexOf(a.field)
        const bi = highPriority.indexOf(b.field)
        const av = ai === -1 ? 999 : ai
        const bv = bi === -1 ? 999 : bi
        return av - bv
      })
      this.keyFieldList = sorted.slice(0, 8)
      this.otherFieldList = sorted.slice(8)
    },
    showValue (val) {
      return val === undefined || val === null || val === '' ? '-' : val
    },
    formatFieldLabel (label) {
      if (!label) return label
      const labelMap = new Map([
        ['数据库入库时间，自动生成', '入库时间'],
        ['本地是否同步标志位，0：未同步；1：已经同步', '本地同步标志']
      ])
      if (labelMap.has(label)) return labelMap.get(label)
      let formatted = label.split('，')[0].split(',')[0].trim()
      formatted = formatted.replace(/^[yY]\s*/, '')
      if (formatted === '铱星序列号') return '铱星编号'
      if (formatted.includes('：') && !formatted.includes('标志')) formatted = formatted.split('：')[0].trim()
      return formatted || label
    },
    handleWindowResize () {
      if (this.trendChartIns) this.trendChartIns.resize()
      if (this.trackMapIns) this.trackMapIns.invalidateSize()
      if (this.trackMapZoomIns) this.trackMapZoomIns.invalidateSize()
      this.renderTrackToMap(false)
    },
    createTrackTileLayer () {
      return L.tileLayer('/api/device/map/tile/?style=7&x={x}&y={y}&z={z}', {
        maxZoom: 18,
        minZoom: 2,
        attribution: 'Gaode'
      })
    },
    initTrackMap () {
      const container = this.$refs.trackMapContainer
      if (!container || this.trackMapIns) return
      const map = L.map(container, {
        zoomControl: false,
        attributionControl: false,
        preferCanvas: true,
        zoomSnap: 0.25,
        zoomDelta: 0.5
      }).setView([31.84, 117.22], 3.25)
      this.createTrackTileLayer().addTo(map)
      this.trackMapPathLayer = L.layerGroup().addTo(map)
      this.trackMapMarkerLayer = L.layerGroup().addTo(map)
      this.trackMapIns = map
      this.renderTrackToMap(false)
    },
    initTrackMapZoom () {
      const container = this.$refs.trackMapZoomContainer
      if (!container || this.trackMapZoomIns) return
      const map = L.map(container, {
        zoomControl: true,
        attributionControl: false,
        preferCanvas: true,
        zoomSnap: 0.25,
        zoomDelta: 0.5
      }).setView([31.84, 117.22], 3.5)
      this.createTrackTileLayer().addTo(map)
      this.trackMapZoomPathLayer = L.layerGroup().addTo(map)
      this.trackMapZoomMarkerLayer = L.layerGroup().addTo(map)
      this.trackMapZoomIns = map
      this.renderTrackToMap(false)
    },
    destroyTrackMap () {
      if (this.trackMapIns) {
        this.trackMapIns.remove()
        this.trackMapIns = null
      }
      this.trackMapPathLayer = null
      this.trackMapMarkerLayer = null
    },
    destroyTrackMapZoom () {
      if (this.trackMapZoomIns) {
        this.trackMapZoomIns.remove()
        this.trackMapZoomIns = null
      }
      this.trackMapZoomPathLayer = null
      this.trackMapZoomMarkerLayer = null
    },
    syncTrackMapRender () {
      this.$nextTick(() => {
        if (!this.trackMapZoomIns) this.initTrackMapZoom()
        this.renderTrackToMap(true)
      })
    },
    renderTrackToMap (needFly = false) {
      const points = (this.trackPoints || [])
        .map(p => ({ lng: Number(p.lng), lat: Number(p.lat), time: p.time }))
        .filter(p => Number.isFinite(p.lng) && Number.isFinite(p.lat))
      this.renderTrackToSingleMap(this.trackMapIns, this.trackMapPathLayer, 'main', points, needFly)
      this.renderTrackToSingleMap(this.trackMapZoomIns, this.trackMapZoomPathLayer, 'zoom', points, needFly)
      this.updateTrackTooltipPosition(points)
    },
    updateTrackTooltipPosition (points) {
      const idx = Number(this.activeTrackIndex)
      if (!Number.isInteger(idx) || idx < 0 || idx >= points.length) return

      if (!this.trackHover.visible) {
        const point = this.trackPoints[idx] || {}
        this.trackHover = {
          visible: true,
          time: point.time || '-',
          lat: Number.isFinite(Number(point.lat)) ? Number(point.lat).toFixed(6) : '-',
          lng: Number.isFinite(Number(point.lng)) ? Number(point.lng).toFixed(6) : '-'
        }
      }

      const point = points[idx]
      const updateFor = (mapIns, key) => {
        if (!mapIns) return
        const p = mapIns.latLngToContainerPoint([point.lat, point.lng])
        const size = mapIns.getSize()
        const width = size.x || 1
        const height = size.y || 1
        this[key] = {
          x: Math.max(0, Math.min(100, (p.x / width) * 100)),
          y: Math.max(0, Math.min(100, (p.y / height) * 100))
        }
      }

      updateFor(this.trackMapIns, 'trackHoverMainPos')
      updateFor(this.trackMapZoomIns, 'trackHoverZoomPos')
    },
    renderTrackToSingleMap (mapIns, pathLayer, scope, points, needFly = false) {
      if (!mapIns || !pathLayer) return
      const markerLayer = scope === 'zoom' ? this.trackMapZoomMarkerLayer : this.trackMapMarkerLayer
      pathLayer.clearLayers()
      if (markerLayer) markerLayer.clearLayers()
      if (!points.length) return

      const latlngs = points.map(p => [p.lat, p.lng])
      L.polyline(latlngs, {
        color: '#2563eb',
        weight: scope === 'zoom' ? 3 : 2.5,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(pathLayer)

      const start = points[0]
      const end = points[points.length - 1]
      const activeIdx = Math.min(Math.max(this.activeTrackIndex, 0), points.length - 1)
      const active = points[activeIdx]

      if (markerLayer) {
        L.circleMarker([start.lat, start.lng], {
          radius: scope === 'zoom' ? 5.5 : 4.5,
          color: '#ffffff',
          weight: 2,
          fillColor: '#22c55e',
          fillOpacity: 0.95
        }).addTo(markerLayer)

        L.circleMarker([end.lat, end.lng], {
          radius: scope === 'zoom' ? 5.5 : 4.5,
          color: '#ffffff',
          weight: 2,
          fillColor: '#f43f5e',
          fillOpacity: 0.95
        }).addTo(markerLayer)

        L.circleMarker([active.lat, active.lng], {
          radius: scope === 'zoom' ? 6.5 : 5.5,
          color: '#ffffff',
          weight: 2,
          fillColor: '#2563eb',
          fillOpacity: 0.95
        }).addTo(markerLayer)
      }

      if (needFly) {
        const bounds = L.latLngBounds(latlngs)
        mapIns.fitBounds(bounds, {
          padding: scope === 'zoom' ? [52, 52] : [64, 64],
          maxZoom: scope === 'zoom' ? 9 : 7.5
        })
      }
    },
    onDetailDialogOpened () {
      this.$nextTick(() => {
        if (!this.trackMapIns) this.initTrackMap()
        this.renderTrackToMap(true)
      })
    },
    onDetailDialogClosed () {
      this.stopTrackPlayback()
      this.trackPoints = []
      this.trackLoading = false
      this.trackLoaded = false
      this.chartPoints = []
      this.chartSeries = []
      this.renderTrackToMap()
      this.availableChartFields = []
      this.selectedChartFields = []
      this.activeTrackIndex = -1
      this.trackHover.visible = false
      this.destroyTrendChart()
    },
    destroyTrendChart () {
      if (this.trendChartIns) {
        this.trendChartIns.dispose()
        this.trendChartIns = null
      }
    },
    handleTrackHover (idx) {
      const point = this.trackPoints[idx]
      if (!point) return
      this.activeTrackIndex = idx
      this.trackHover = {
        visible: true,
        time: point.time || '-',
        lat: Number.isFinite(Number(point.lat)) ? Number(point.lat).toFixed(6) : '-',
        lng: Number.isFinite(Number(point.lng)) ? Number(point.lng).toFixed(6) : '-'
      }
      this.renderTrackToMap()
    },
    handleTrackLeave () {
      this.activeTrackIndex = -1
      this.trackHover.visible = false
    },
    handleTrackClick (idx) {
      this.handleTrackHover(idx)
    },
    toggleTrackPlayback () {
      if (!this.trackPoints.length) return
      if (this.isTrackPlaying) {
        this.stopTrackPlayback()
        return
      }
      if (this.activeTrackIndex < 0) {
        this.activeTrackIndex = 0
        this.playbackProgress = 0
      }
      this.isTrackPlaying = true
      this.startTrackPlaybackTimer()
      this.handleTrackHover(this.activeTrackIndex)
    },
    startTrackPlaybackTimer () {
      this.stopTrackPlaybackTimerOnly()
      const speed = Number(this.playbackSpeed) || 1
      const baseMs = 1000
      const intervalMs = Math.max(150, Math.floor(baseMs / speed))
      this.trackPlayTimer = setInterval(() => {
        this.playNextTrackPoint()
      }, intervalMs)
    },
    stopTrackPlaybackTimerOnly () {
      if (this.trackPlayTimer) {
        clearInterval(this.trackPlayTimer)
        this.trackPlayTimer = null
      }
    },
    stopTrackPlayback () {
      this.isTrackPlaying = false
      this.stopTrackPlaybackTimerOnly()
    },
    playNextTrackPoint () {
      if (!this.trackPoints.length) {
        this.stopTrackPlayback()
        return
      }
      const next = this.activeTrackIndex + 1
      if (next >= this.trackPoints.length) {
        this.stopTrackPlayback()
        return
      }
      this.activeTrackIndex = next
      this.playbackProgress = next
      this.handleTrackHover(next)
    },
    handlePlaybackProgressInput (value) {
      const idx = Number(value) || 0
      this.activeTrackIndex = idx
      this.handleTrackHover(idx)
    },
    handlePlaybackProgressChange (value) {
      const idx = Number(value) || 0
      this.activeTrackIndex = idx
      this.playbackProgress = idx
      this.handleTrackHover(idx)
    },
    handlePlaybackSpeedChange () {
      if (this.isTrackPlaying) {
        this.startTrackPlaybackTimer()
      }
    },
    async loadTrackData () {
      if (!this.currentDevice.device_id) return
      const { startDate, endDate } = this.getTrendDateParams()
      this.trackLoading = true
      this.trackLoaded = false
      try {
        const { data: res } = await this.$axios.get('/device/track/', {
          params: {
            device_id: this.currentDevice.device_id,
            start_date: startDate,
            end_date: endDate,
            limit: 600
          }
        })
        this.trackPoints = (res.code === 200 && res.data && res.data.points) ? res.data.points : []
        if (this.trackPoints.length) {
          this.activeTrackIndex = 0
          this.playbackProgress = 0
          this.handleTrackHover(0)
          this.renderTrackToMap(true)
        } else {
          this.activeTrackIndex = -1
          this.playbackProgress = 0
          this.trackHover.visible = false
          this.renderTrackToMap()
        }
      } catch (e) {
        console.error('[track] 请求异常', e)
        this.$message.error('轨迹加载失败，请稍后重试')
        this.trackPoints = []
        this.activeTrackIndex = -1
        this.playbackProgress = 0
        this.trackHover.visible = false
        this.renderTrackToMap()
      } finally {
        this.trackLoading = false
        this.trackLoaded = true
      }
    },
    buildAvailableChartFields () {
      if (!this.chartPoints.length || !this.sortedTrendColumns.length) {
        this.availableChartFields = []
        this.selectedChartFields = []
        return
      }
      const numericFields = []
      this.sortedTrendColumns.forEach(col => {
        const values = this.chartPoints.map(p => Number(p[col.field])).filter(v => Number.isFinite(v))
        if (values.length >= 2) numericFields.push({ field: col.field, label: this.formatFieldLabel(col.label) })
      })
      const priority = ['air_temp', 'board_temp', 'wind_speed', 'atmosphere', 'board_voltage']
      const ordered = []
      priority.forEach(name => {
        const hit = numericFields.find(f => f.field === name)
        if (hit) ordered.push(hit)
      })
      numericFields.forEach(f => {
        if (!ordered.find(x => x.field === f.field)) ordered.push(f)
      })
      this.availableChartFields = ordered

      const availableSet = new Set(ordered.map(item => item.field))
      let selected = (this.selectedChartFields || []).filter(field => availableSet.has(field))
      if (!selected.length) selected = ordered.slice(0, 1).map(item => item.field)
      this.selectedChartFields = selected.slice(0, 3)
    },
    handleChartFieldChange (value) {
      const normalized = Array.isArray(value) ? value : []
      if (normalized.length > 3) {
        this.selectedChartFields = normalized.slice(0, 3)
        this.$message.warning('最多选择3个分析指标')
      } else {
        this.selectedChartFields = normalized
      }
      this.renderTrendChart()
    },
    extractChartSeries () {
      if (!this.availableChartFields.length || !this.selectedChartFields.length) {
        this.chartSeries = []
        return []
      }
      const selectedSet = new Set(this.selectedChartFields)
      const seriesFields = this.availableChartFields.filter(item => selectedSet.has(item.field))
      this.chartSeries = seriesFields
      return seriesFields
    },
    renderTrendChart () {
      const chartEl = this.$refs.trendChart
      if (!chartEl) return
      const seriesFields = this.extractChartSeries()
      if (!seriesFields.length) {
        this.destroyTrendChart()
        return
      }
      if (!this.trendChartIns) this.trendChartIns = echarts.init(chartEl)

      const xData = this.chartPoints.map(p => p.time)
      const palette = ['#2563eb', '#16a34a', '#f97316']
      const series = seriesFields.map((f, idx) => ({
        name: f.label,
        type: 'line',
        smooth: true,
        showSymbol: false,
        symbolSize: 6,
        lineStyle: { width: 2 },
        itemStyle: { color: palette[idx % palette.length] },
        data: this.chartPoints.map(p => {
          const val = Number(p[f.field])
          return Number.isFinite(val) ? val : null
        })
      }))

      this.trendChartIns.setOption({
        grid: { top: 36, left: 42, right: 24, bottom: 40 },
        tooltip: { trigger: 'axis' },
        legend: { top: 4, type: 'scroll', icon: 'circle', itemWidth: 10, itemHeight: 10 },
        xAxis: { type: 'category', data: xData, axisLabel: { color: '#64748b', fontSize: 11, hideOverlap: true } },
        yAxis: { type: 'value', scale: true, axisLabel: { color: '#64748b', fontSize: 11 }, splitLine: { lineStyle: { color: '#e2e8f0' } } },
        series
      }, true)
    },
    async getTableData () {
      this.tableLoading = true
      try {
        const { data: res } = await this.$axios.get('/device/list/', {
          params: {
            page: this.page,
            page_size: this.pageSize,
            keyword: this.searchKeyword,
            ownership: this.searchOwnership,
            status: this.searchStatus
          }
        })
        if (res.code === 200) {
          this.tableData = res.data.device_list
          this.total = res.data.total
        } else {
          this.$message.error(res.msg || '获取列表失败')
        }
      } finally {
        this.tableLoading = false
      }
    },
    async tryOpenDeviceFromRoute (deviceId) {
      try {
        const hit = (this.tableData || []).find(item => String(item.device_id || item.devid || '').trim() === deviceId)
        if (hit) {
          await this.showData(hit)
          return
        }
        const { data: res } = await this.$axios.get('/device/list/', {
          params: {
            page: 1,
            page_size: 200,
            keyword: deviceId
          }
        })
        if (res.code !== 200) return
        const list = (res.data && res.data.device_list) || []
        const row = list.find(item => String(item.device_id || item.devid || '').trim() === deviceId)
        if (row) await this.showData(row)
      } catch (e) {
        console.error('[route-open-device] 打开设备详情失败', e)
      }
    },
    search () {
      this.page = 1
      this.getTableData()
    },
    handleSizeChange (size) {
      this.pageSize = size
      this.page = 1
      this.getTableData()
    },
    handleCurrentChange (page) {
      this.page = page
      this.getTableData()
    },
    resetDetailState (row) {
      this.currentDevice = row
      this.currentSourceTable = ''
      this.latestFieldList = []
      this.keyFieldList = []
      this.otherFieldList = []
      this.trendColumns = []
      this.trendPoints = []
      this.chartPoints = []
      this.trackPoints = []
      this.chartSeries = []
      this.availableChartFields = []
      this.selectedChartFields = []
      this.activeTrackIndex = -1
      this.playbackProgress = 0
      this.playbackSpeed = 1
      this.trackHover.visible = false
      this.trendPage = 1
      this.trendPageSize = 100
      this.trendTotal = 0
      this.trendRangeType = '1y'
      this.dataVisible = true
      this.updateTrendDateRange()
    },
    getTrendDateParams () {
      if (this.trendRangeType !== 'custom') this.updateTrendDateRange()
      return {
        startDate: (this.trendDateRange && this.trendDateRange[0]) || '',
        endDate: (this.trendDateRange && this.trendDateRange[1]) || ''
      }
    },
    applyTrendData (res) {
      if (res.code === 200) {
        const d = res.data || {}
        this.currentSourceTable = d.source_table || this.currentSourceTable
        this.trendColumns = d.columns || []
        this.trendPoints = d.points || []
        this.trendTotal = d.total || 0
        return
      }
      this.trendColumns = []
      this.trendPoints = []
      this.trendTotal = 0
    },
    async showData (row) {
      try {
        this.resetDetailState(row)
        const latestRes = await this.$axios.get('/device/data/latest/', { params: { device_id: row.device_id } })
        if (latestRes.data.code === 200) {
          const d = latestRes.data.data || {}
          this.currentSourceTable = d.source_table || ''
          this.latestFieldList = d.field_list || []
          this.splitLatestFields()
        }

        await this.loadAnalysisByDateRange()
      } catch (error) {
        console.error('[showData] 加载设备详情失败:', error)
        this.$message.error('加载设备详情失败，请稍后重试')
      }
    },
    getChartFetchSize () {
      switch (this.trendRangeType) {
        case '1d': return 300
        case '7d': return 1200
        case '30d': return 4000
        case '1y': return 12000
        case 'custom': return 6000
        default: return 4000
      }
    },
    async loadTrendData () {
      if (!this.currentDevice.device_id) return
      const { startDate, endDate } = this.getTrendDateParams()

      const { data: res } = await this.$axios.get('/device/data/trend/', {
        params: {
          device_id: this.currentDevice.device_id,
          range_type: this.trendRangeType,
          start_date: startDate,
          end_date: endDate,
          page: this.trendPage,
          page_size: this.trendPageSize
        }
      })
      this.applyTrendData(res)

      try {
        const { data: chartRes } = await this.$axios.get('/device/data/trend/', {
          params: {
            device_id: this.currentDevice.device_id,
            range_type: this.trendRangeType,
            start_date: startDate,
            end_date: endDate,
            page: 1,
            page_size: this.getChartFetchSize()
          }
        })
        const points = (chartRes.code === 200 && chartRes.data && chartRes.data.points) ? chartRes.data.points : []
        this.chartPoints = [...points].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
      } catch (e) {
        this.chartPoints = [...this.trendPoints].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
      }

      this.buildAvailableChartFields()
      this.$nextTick(() => this.renderTrendChart())
    },
    async loadAnalysisByDateRange () {
      if (!this.currentDevice.device_id) return
      this.trendPage = 1
      await Promise.all([
        this.loadTrendData(),
        this.loadTrackData()
      ])
    },
    handleTrendSizeChange (size) {
      this.trendPageSize = size
      this.trendPage = 1
      this.loadTrendData()
    },
    handleTrendPageChange (page) {
      this.trendPage = page
      this.loadTrendData()
    }
  }
}
</script>

<style scoped>
.device-page { padding: 22px; min-height: 100vh; font-size: 14px; background: #f1f5f9; }
.device-page-embed { padding: 0; min-height: 100vh; background: transparent; }
.breadcrumb { margin-bottom: 14px; }
.filter-card, .table-card, .summary-card, .inner-card { border-radius: 12px; border: 1px solid #e2e8f0; }
.filter-card { margin-bottom: 12px; }
.table-card { margin-bottom: 14px; }
.toolbar { margin-bottom: 0; display: flex; align-items: center; }
.toolbar-buttons { display: flex; justify-content: flex-end; gap: 10px; }
.device-table ::v-deep th { background: #f8fafc; color: #334155; font-weight: 600; }
.device-table ::v-deep td { background: #fff; color: #1f2937; }
.device-table ::v-deep tr:hover td { background: #f8fbff; }
.pagination { margin-top: 16px; text-align: right; }
.detail-grid { margin-top: 12px; }
.dialog-title-wrap { display: flex; align-items: baseline; gap: 10px; }
.dialog-title-main { font-size: 14px; font-weight: 600; color: #1f2937; }
.dialog-title-sub { font-size: 12px; color: #475569; font-weight: 600; }
.inner-card { margin-bottom: 12px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06); }
.latest-header { display: flex; justify-content: space-between; align-items: center; }
.latest-header span:first-child { font-size: 13px; font-weight: 600; color: #1f2937; }
.field-list { display: flex; flex-wrap: wrap; gap: 8px 16px; }
.field-item { display: flex; align-items: baseline; flex: 0 0 calc(25% - 12px); min-width: 140px; line-height: 1.6; }
.field-label { color: #64748b; font-size: 11px; font-weight: 500; white-space: nowrap; flex-shrink: 0; }
.field-value { color: #1f2937; font-size: 11px; margin-left: 2px; word-break: break-word; flex: 1; }
.key-fields { margin-bottom: 8px; padding: 4px 0; }
.other-fields { padding: 4px 0; }
.more-collapse { margin-top: 8px; }
.collapse-title { font-size: 11px; color: #475569; font-weight: 500; }
.more-collapse ::v-deep .el-collapse-item__header { font-size: 11px; padding: 4px 0; height: auto; line-height: 1.5; }
.more-collapse ::v-deep .el-collapse-item__content { padding-bottom: 4px; padding-top: 4px; }
.more-collapse ::v-deep .el-collapse-item__arrow { font-size: 12px; }

.analysis-card {
  background: radial-gradient(120% 120% at 0% 0%, #f0f7ff 0%, #ffffff 45%, #f8fbff 100%);
  border: 1px solid #dbeafe;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.08);
}
.analysis-header { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.analysis-header-left { display: flex; align-items: baseline; gap: 10px; }
.analysis-header span:first-child { font-size: 14px; font-weight: 700; color: #0f172a; }
.analysis-sub { font-size: 12px; color: #64748b; }
.analysis-grid { min-height: auto; }
.panel-title { font-size: 12px; font-weight: 700; color: #334155; margin-bottom: 8px; }
.panel-title-chart { display: flex; align-items: center; justify-content: space-between; }
.panel-title-map { display: flex; align-items: center; justify-content: space-between; }
.map-zoom-btn { color: #2563eb; padding: 0; font-size: 12px; }
.map-zoom-btn:hover { color: #1d4ed8; }

.field-selector-btn { color: #2563eb; padding: 0; font-size: 12px; }
.field-selector-wrap { max-height: 260px; overflow: auto; }
.field-selector-title { font-size: 12px; color: #334155; margin-bottom: 8px; font-weight: 600; }
.field-selector-wrap ::v-deep .el-checkbox { width: 48%; margin-right: 0; margin-bottom: 6px; }

.track-map-wrap {
  position: relative;
  height: 220px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: #dbeafe;
  overflow: hidden;
}
.real-track-map {
  width: 100%;
  height: 100%;
}
.track-map-wrap ::v-deep .leaflet-container {
  background: #dbeafe;
}
.track-map-wrap ::v-deep .leaflet-control-attribution,
.track-map-wrap ::v-deep .leaflet-control-container .leaflet-bottom {
  display: none;
}
.track-map-wrap ::v-deep .leaflet-pane,
.track-map-wrap ::v-deep .leaflet-top,
.track-map-wrap ::v-deep .leaflet-bottom {
  z-index: 200 !important;
}
.track-tooltip {
  position: absolute;
  background: rgba(15, 23, 42, 0.9);
  color: #fff;
  font-size: 11px;
  line-height: 1.5;
  padding: 6px 8px;
  border-radius: 6px;
  pointer-events: none;
  white-space: nowrap;
  z-index: 1200;
}
.analysis-playback {
  margin-top: 2px;
  padding: 2px 0 0;
}
.playback-line-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.playback-slider-wrap {
  position: relative;
  flex: 1;
  padding-top: 2px;
}
.playback-slider { flex: 1; }
.playback-slider ::v-deep .el-slider__runway {
  height: 6px;
  border-radius: 999px;
  margin: 6px 0;
  background: #dbe6f6;
}
.playback-slider ::v-deep .el-slider__bar {
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, #60a5fa, #2563eb);
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.28);
}
.playback-slider ::v-deep .el-slider__button {
  width: 14px;
  height: 14px;
  border: 2px solid #fff;
  background: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18);
}
.playback-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 0;
  margin-right: 6px;
}
.speed-select { width: 44px; }
.speed-select ::v-deep .el-input__inner {
  height: 22px;
  line-height: 22px;
  border: none;
  background: transparent;
  padding: 0 14px 0 0;
  font-size: 12px;
  color: #64748b;
}
.speed-select ::v-deep .el-input__suffix {
  right: 0;
}
.speed-select ::v-deep .el-input__suffix-inner {
  color: #94a3b8;
}
.speed-select ::v-deep .el-input .el-select__caret {
  font-size: 12px;
  transform: scale(0.9);
}
.play-toggle-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid #c8d7ee;
  background: #ffffff;
  color: #2563eb;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1);
  transition: all 0.2s ease;
}
.play-toggle-btn.playing {
  border-color: #1d4ed8;
  background: linear-gradient(180deg, #3b82f6, #2563eb);
  color: #fff;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.3);
}
.play-toggle-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 5px 12px rgba(15, 23, 42, 0.16);
}
.icon-play {
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 7px solid currentColor;
  margin-left: 1px;
}
.icon-stop {
  width: 7px;
  height: 7px;
  background: currentColor;
}

.trend-chart {
  position: relative;
  height: 220px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
}
.panel-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 12px;
}
.panel-empty-chart { position: relative; height: 0; top: -130px; pointer-events: none; }

.trend-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.trend-header span:first-child { font-size: 13px; font-weight: 600; color: #1f2937; }
.trend-tools { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.trend-table ::v-deep .el-table__body-wrapper .el-table__body td { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.trend-table ::v-deep .el-table__body-wrapper .el-table__body td .cell { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.map-zoom-wrap { height: calc(88vh - 120px); min-height: 520px; max-height: 780px; }
.map-zoom-dialog ::v-deep .el-dialog__body { padding-top: 8px; }
</style>
