<template>
  <div class="device-page">
    <el-breadcrumb separator-class="el-icon-arrow-right" class="breadcrumb">
      <el-breadcrumb-item to="/home">首页</el-breadcrumb-item>
      <el-breadcrumb-item>设备管理</el-breadcrumb-item>
      <el-breadcrumb-item>设备列表</el-breadcrumb-item>
    </el-breadcrumb>
    <el-card shadow="never" class="filter-card">
      <el-row :gutter="12" class="toolbar">
      <el-col :span="8">
        <el-input v-model="searchKeyword" placeholder="输入设备名称或设备ID搜索" clearable @clear="search" @keyup.enter.native="search">
          <el-button slot="append" icon="el-icon-search" @click="search" />
        </el-input>
      </el-col>
      <el-col :span="6">
        <el-input v-model="searchOwnership" placeholder="输入归属区域（ownership）过滤" clearable @clear="search" @keyup.enter.native="search">
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

    <el-card shadow="never" class="table-card">
    <el-table :data="tableData" border class="device-table" highlight-current-row>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="device_id" label="设备ID" width="130" />
      <el-table-column prop="device_name" label="设备名称" min-width="140" />
      <el-table-column prop="ownership" label="归属区域" min-width="140" />
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

    <el-dialog :visible.sync="dataVisible" width="1200px" top="3vh" @close="destroyMap" class="device-detail-dialog">
      <template slot="title">
        <div class="dialog-title-wrap">
          <span class="dialog-title-main">设备详情</span>
          <span class="dialog-title-sub">{{ detailSubtitle }}</span>
        </div>
      </template>
      <el-row :gutter="16" class="detail-grid">
        <!-- 最新数据 -->
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

        <!-- ========== 设备轨迹可视化模块 ========== -->
        <!-- 产品设计说明：
             1. 用户场景：科研人员需要查看设备（浮标/气象站）的漂移轨迹，分析路径和位置变化
             2. 功能需求：
                - 3D地球视图：适合极地设备（南极/北极），展示全球轨迹，立体可视化
                - 2D平面视图：适合区域设备（呼伦贝尔/青藏高原），展示局部轨迹，带地理标注
                - 轨迹播放：时间轴回放，分析漂移过程
                - 数据展示：时间、经纬度、其他业务数据
             3. 企业级特性：
                - 错误处理：网络异常、数据异常、地图加载失败
                - 性能优化：大量轨迹点的渲染优化、播放性能优化
                - 用户体验：加载状态、错误提示、操作反馈
                - 代码质量：模块化、可维护、可扩展
        -->
        <el-col :span="24">
          <el-card shadow="never" class="inner-card track-visualization-card">
            <!-- 标题栏：状态信息 + 视图切换 -->
            <div slot="header" class="track-header">
              <div class="track-header-left">
                <span class="track-title">
                  <i class="el-icon-location"></i>
                  设备轨迹可视化
                </span>
                <el-tag v-if="trackPoints.length" size="mini" type="info" class="track-count-tag">
                  {{ trackPoints.length }} 个轨迹点
                </el-tag>
                <!-- 状态提示 -->
                <transition name="fade">
                  <span v-if="mapLoading" class="map-status-text">
                    <i class="el-icon-loading"></i> 地图加载中...
                  </span>
                  <span v-else-if="mapError" class="map-status-text map-error">
                    <i class="el-icon-warning"></i> 地图模块加载失败，已切换为表格展示
                  </span>
                  <span v-else-if="!trackPoints.length" class="map-status-text">
                    <i class="el-icon-info"></i> 当前设备暂无轨迹数据
                  </span>
                </transition>
              </div>
              <!-- 视图切换：3D/2D -->
              <div class="track-header-right" v-if="trackPoints.length && !mapLoading">
                <el-radio-group v-model="mapViewMode" size="mini" @change="handleMapViewModeChange">
                  <el-radio-button label="3d">
                    <i class="el-icon-view"></i> 3D视图
                  </el-radio-button>
                  <el-radio-button label="2d">
                    <i class="el-icon-map-location"></i> 2D视图
                  </el-radio-button>
                </el-radio-group>
              </div>
            </div>

            <!-- ========== 3D地图容器 ========== -->
            <div v-show="mapViewMode === '3d'" class="map-container-wrapper">
              <!-- 3D地图画布 -->
              <div id="track-map-3d" class="map-box map-box-3d" v-show="mapReady && !mapLoading" v-loading="mapLoading" element-loading-text="正在加载3D地球..."></div>
              <!-- 加载遮罩（备用，如果v-loading不生效） -->
              <div v-if="mapLoading && !mapReady" class="map-loading-overlay">
                <div style="text-align: center; padding-top: 150px; color: #909399;">
                  <i class="el-icon-loading" style="font-size: 24px;"></i>
                  <div style="margin-top: 10px;">正在加载3D地球...</div>
                </div>
              </div>
              <!-- 3D地图控制面板 -->
              <div v-if="mapReady && trackPoints.length && !mapLoading" class="map-control-panel map-control-panel-3d">
                <div class="control-group">
                  <el-button-group>
                    <el-button size="mini" type="primary" :icon="playbackState === 'playing' ? 'el-icon-video-pause' : 'el-icon-video-play'" @click="togglePlayback">
                      {{ playbackState === 'playing' ? '暂停' : '播放' }}
                    </el-button>
                    <el-button size="mini" icon="el-icon-refresh-left" @click="resetPlayback">重置</el-button>
                    <el-button size="mini" icon="el-icon-aim" @click="flyToTrack">定位轨迹</el-button>
                  </el-button-group>
                </div>
                <div class="control-group">
                  <span class="control-label">播放速度</span>
                  <el-slider
                    v-model="playbackSpeed"
                    :min="1"
                    :max="10"
                    :step="1"
                    :format-tooltip="formatSpeedTooltip"
                    style="width: 120px; margin: 0 8px;"
                    @change="updatePlaybackSpeed"
                  />
                </div>
              </div>
              <!-- 时间轴 -->
              <div v-if="mapReady && trackPoints.length && !mapLoading" class="timeline-container">
                <div class="timeline-header">
                  <span class="timeline-label">轨迹时间轴</span>
                  <span class="timeline-time">{{ playbackTimeLabel }}</span>
                  <span class="timeline-progress">{{ playbackIndex + 1 }} / {{ trackPoints.length }}</span>
                </div>
                <el-slider
                  v-model="playbackProgress"
                  :min="0"
                  :max="trackPoints.length - 1"
                  :step="1"
                  :format-tooltip="formatTimelineTooltip"
                  @input="onTimelineChange"
                  class="timeline-slider"
                />
              </div>
            </div>

            <!-- ========== 2D地图容器 ========== -->
            <div v-show="mapViewMode === '2d'" class="map-container-wrapper">
              <!-- 2D地图画布 -->
              <div id="track-map-2d" class="map-box map-box-2d" v-show="map2dReady && !mapLoading" v-loading="mapLoading" element-loading-text="正在加载2D地图..."></div>
              <!-- 加载遮罩（备用，如果v-loading不生效） -->
              <div v-if="mapLoading && !map2dReady" class="map-loading-overlay">
                <div style="text-align: center; padding-top: 150px; color: #909399;">
                  <i class="el-icon-loading" style="font-size: 24px;"></i>
                  <div style="margin-top: 10px;">正在加载2D地图...</div>
                </div>
              </div>
              <!-- 2D地图控制面板 -->
              <div v-if="map2dReady && trackPoints.length && !mapLoading" class="map-control-panel map-control-panel-2d">
                <div class="control-group">
                  <el-button-group>
                    <el-button size="mini" type="primary" :icon="playbackState === 'playing' ? 'el-icon-video-pause' : 'el-icon-video-play'" @click="togglePlayback">
                      {{ playbackState === 'playing' ? '暂停' : '播放' }}
                    </el-button>
                    <el-button size="mini" icon="el-icon-refresh-left" @click="resetPlayback">重置</el-button>
                    <el-button size="mini" icon="el-icon-full-screen" @click="fitBounds2D">适应窗口</el-button>
                  </el-button-group>
                </div>
              </div>
              <!-- 2D地图时间轴（与3D保持一致） -->
              <div v-if="map2dReady && trackPoints.length && !mapLoading" class="timeline-container">
                <div class="timeline-header">
                  <span class="timeline-label">轨迹时间轴</span>
                  <span class="timeline-time">{{ playbackTimeLabel }}</span>
                  <span class="timeline-progress">{{ playbackIndex + 1 }} / {{ trackPoints.length }}</span>
                </div>
                <el-slider
                  v-model="playbackProgress"
                  :min="0"
                  :max="trackPoints.length - 1"
                  :step="1"
                  :format-tooltip="formatTimelineTooltip"
                  @input="onTimelineChange"
                  class="timeline-slider"
                />
              </div>
            </div>

            <!-- ========== 轨迹数据表格（备用展示） ========== -->
            <div v-if="!mapReady && !map2dReady && !mapLoading && trackPoints.length" class="track-table-fallback">
              <el-table :data="trackPoints" size="mini" height="300" border stripe>
                <el-table-column prop="time" label="时间" width="180" fixed="left" />
                <el-table-column prop="lat" label="纬度" width="120">
                  <template slot-scope="scope">
                    {{ scope.row.lat ? Number(scope.row.lat).toFixed(6) : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="lng" label="经度" width="120">
                  <template slot-scope="scope">
                    {{ scope.row.lng ? Number(scope.row.lng).toFixed(6) : '-' }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100" fixed="right">
                  <template slot-scope="scope">
                    <el-button type="text" size="mini" @click="viewPointDetail(scope.row)">详情</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </el-col>

        <!-- 设备详细数据 -->
        <el-col :span="24">
      <el-card shadow="never" class="inner-card">
        <div slot="header" class="trend-header">
          <span>设备详细数据</span>
          <div class="trend-tools">
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
        <el-table :data="trendPoints" size="mini" height="260" border class="trend-table">
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
  </div>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
export default {
  data () {
    return {
      tableData: [],
      total: 0,
      page: 1,
      pageSize: 10,
      searchKeyword: '',
      searchOwnership: '',
      searchStatus: '',
      dataVisible: false,
      currentDevice: {},
      latestFieldList: [],
      keyFieldList: [],
      otherFieldList: [],
      trendColumns: [],
      trendPoints: [],
      trendDateRange: [],
      trendRangeType: '1y',
      trendPage: 1,
      trendPageSize: 100,
      trendTotal: 0,
      // ========== 轨迹可视化相关数据 ==========
      trackPoints: [], // 轨迹点数据
      mapViewMode: '3d', // 视图模式：'3d' | '2d'
      mapLoading: false, // 地图加载状态
      mapError: false, // 地图加载错误
      // 3D地图（Cesium）
      map: null, // Cesium Viewer 实例
      mapReady: false, // 3D地图就绪状态
      trackTimeRange: null, // 轨迹时间范围 {start: JulianDate, stop: JulianDate}
      trackPositionProperty: null, // Cesium SampledPositionProperty（时间驱动的位置属性）
      cesiumEntities: {
        // 3D实体集合，便于统一管理
        polyline: null, // 轨迹线实体
        startPoint: null, // 起点
        endPoint: null, // 终点
        playbackMarker: null // 播放点实体（使用时间驱动）
      },
      // 2D地图（Leaflet）
      map2d: null, // Leaflet Map 实例
      map2dReady: false, // 2D地图就绪状态
      leafletLayers: {
        // Leaflet图层集合，便于统一管理
        polyline: null, // 轨迹线
        startMarker: null, // 起点
        endMarker: null, // 终点
        playbackMarker: null // 播放点
      },
      // 播放控制
      playbackState: 'paused', // 播放状态：'playing' | 'paused'
      playbackTimer: null, // 播放定时器（兼容旧代码）
      clockTickListener: null, // Cesium时钟tick监听器（Cesium官方推荐）
      playbackIndex: 0, // 当前播放索引
      playbackProgress: 0, // 播放进度（用于slider）
      playbackTimeLabel: '-', // 当前播放时间标签
      playbackSpeed: 3 // 播放速度（1-10，默认3），对应Cesium时钟multiplier
    }
  },
  computed: {
    detailSubtitle () {
      if (!this.currentDevice.device_id) return ''
      return `${this.currentDevice.device_name || this.currentDevice.device_id} - ${this.currentDevice.device_id}`
    },
    sortedTrendColumns () {
      if (!this.trendColumns.length) return []
      // 过滤掉 time 和 packet_time 字段（第一列已显示）
      const filteredColumns = this.trendColumns.filter(col => col.field !== 'time' && col.field !== 'packet_time')
      if (!this.keyFieldList.length) return filteredColumns
      // 获取关键字段的字段名列表
      const keyFields = this.keyFieldList.map(item => item.field)
      // 先展示关键字段，然后展示其他字段
      const keyCols = filteredColumns.filter(col => keyFields.includes(col.field))
      const otherCols = filteredColumns.filter(col => !keyFields.includes(col.field))
      return [...keyCols, ...otherCols]
    }
  },
  created () {
    this.getTableData()
    this.initDefaultYearRange()
  },
  methods: {
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
          startDate = new Date(now.getFullYear(), 0, 1, 0, 0, 0)
          break
        case 'custom':
          // 自定义模式，不自动更新日期范围
          return
        default:
          startDate = new Date(now.getFullYear(), 0, 1, 0, 0, 0)
      }
      this.trendDateRange = [
        this.formatDate(startDate),
        this.formatDate(endDate)
      ]
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
        this.loadTrendData()
      } else {
        // 切换到自定义模式时，初始化日期范围（默认最近7天）
        const now = new Date()
        const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
        const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000)
        this.trendDateRange = [
          this.formatDate(startDate),
          this.formatDate(endDate)
        ]
      }
    },
    handleCustomDateChange (value) {
      if (value && value.length === 2) {
        this.loadTrendData()
      }
    },
    splitLatestFields () {
      const keyNames = ['time', 'packet_time', 'board_temp', 'air_temp', 'air_humid', 'atmosphere', 'wind_speed', 'wind_direct', 'lat', 'lon', 'latitude', 'longitude', 'board_voltage']
      this.keyFieldList = this.latestFieldList.filter(item => keyNames.includes(item.field)).slice(0, 6)
      this.otherFieldList = this.latestFieldList.filter(item => !this.keyFieldList.some(k => k.field === item.field))
    },
    showValue (val) {
      return val === undefined || val === null || val === '' ? '-' : val
    },
    formatFieldLabel (label) {
      if (!label) return label
      // 特定字段名称映射（使用 Map 避免 ESLint quote-props 问题）
      const labelMap = new Map([
        ['数据库入库时间，自动生成', '入库时间'],
        ['本地是否同步标志位，0：未同步；1：已经同步', '本地同步标志']
      ])
      if (labelMap.has(label)) return labelMap.get(label)
      // 通用规则：去除逗号（中文和英文）及后面的说明
      let formatted = label.split('，')[0].split(',')[0].trim()
      // 去除开头的"y"等异常字符（可能是数据问题）
      formatted = formatted.replace(/^[yY]\s*/, '')
      // 特殊处理：铱星序列号 -> 铱星编号
      if (formatted === '铱星序列号') return '铱星编号'
      // 如果包含冒号说明（但不是标志类字段），去除说明部分
      // 标志类字段保留（如"纬度标志，0：北纬；1：南纬" -> "纬度标志"）
      if (formatted.includes('：') && !formatted.includes('标志')) {
        formatted = formatted.split('：')[0].trim()
      }
      return formatted || label
    },
    async getTableData () {
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

    /**
     * 显示设备详情
     * 企业级特性：错误处理、加载状态、数据校验
     */
    async showData (row) {
      try {
        // 1. 重置状态
        this.currentDevice = row
        this.latestFieldList = []
        this.keyFieldList = []
        this.otherFieldList = []
        this.trendColumns = []
        this.trendPoints = []
        this.trendPage = 1
        this.trendPageSize = 100
        this.trendTotal = 0
        this.trendRangeType = '1y'
        this.trackPoints = []
        this.mapViewMode = '3d' // 默认3D视图
        this.mapLoading = false
        this.mapError = false
        this.mapReady = false
        this.map2dReady = false
        this.playbackState = 'paused'
        this.playbackIndex = 0
        this.playbackProgress = 0
        this.playbackTimeLabel = '-'

        // 2. 显示对话框
        this.dataVisible = true
        this.updateTrendDateRange()

        // 3. 并行加载数据（提升性能）
        const [latestRes, trackRes] = await Promise.all([
          this.$axios.get('/device/data/latest/', { params: { device_id: row.device_id } }),
          this.$axios.get('/device/track/', { params: { device_id: row.device_id, limit: 1000 } })
        ])

        // 4. 处理最新数据
        if (latestRes.data.code === 200) {
          const d = latestRes.data.data || {}
          this.latestFieldList = d.field_list || []
          this.splitLatestFields()
        }

        // 5. 处理轨迹数据
        if (trackRes.data.code === 200) {
          this.trackPoints = (trackRes.data.data && trackRes.data.data.points) ? trackRes.data.data.points : []
        }

        // 6. 加载趋势数据
        await this.loadTrendData()

        // 7. 渲染地图（等待DOM更新）
        this.$nextTick(() => {
          this.initMaps()
        })
      } catch (error) {
        console.error('[showData] 加载设备详情失败:', error)
        this.$message.error('加载设备详情失败，请稍后重试')
      }
    },
    async loadTrendData () {
      if (!this.currentDevice.device_id) return
      let startDate = ''
      let endDate = ''
      if (this.trendRangeType === 'custom') {
        startDate = this.trendDateRange && this.trendDateRange[0] ? this.trendDateRange[0] : ''
        endDate = this.trendDateRange && this.trendDateRange[1] ? this.trendDateRange[1] : ''
      } else {
        this.updateTrendDateRange()
        startDate = this.trendDateRange && this.trendDateRange[0] ? this.trendDateRange[0] : ''
        endDate = this.trendDateRange && this.trendDateRange[1] ? this.trendDateRange[1] : ''
      }
      const { data: res } = await this.$axios.get('/device/data/trend/', {
        params: {
          device_id: this.currentDevice.device_id,
          range_type: 'year',
          start_date: startDate,
          end_date: endDate,
          page: this.trendPage,
          page_size: this.trendPageSize
        }
      })
      if (res.code === 200) {
        const d = res.data || {}
        this.trendColumns = d.columns || []
        this.trendPoints = d.points || []
        this.trendTotal = d.total || 0
      } else {
        this.trendColumns = []
        this.trendPoints = []
        this.trendTotal = 0
      }
    },
    handleTrendSizeChange (size) {
      this.trendPageSize = size
      this.trendPage = 1
      this.loadTrendData()
    },
    handleTrendPageChange (page) {
      this.trendPage = page
      this.loadTrendData()
    },

    /**
     * ========== 地图初始化 ==========
     * 企业级特性：统一初始化入口、错误处理、状态管理
     */
    initMaps () {
      if (!this.trackPoints.length) {
        console.warn('[initMaps] 没有轨迹数据，跳过地图初始化')
        return
      }

      // 根据视图模式初始化对应地图
      if (this.mapViewMode === '3d') {
        this.initMap3D()
      } else {
        this.initMap2D()
      }
    },

    /**
     * ========== 视图模式切换 ==========
     */
    handleMapViewModeChange (mode) {
      this.pausePlayback() // 切换视图时暂停播放
      if (mode === '3d') {
        if (!this.mapReady) {
          this.initMap3D()
        }
      } else {
        if (!this.map2dReady) {
          this.initMap2D()
        }
      }
    },

    /**
     * ========== 播放控制 ==========
     */
    togglePlayback () {
      if (this.playbackState === 'playing') {
        this.pausePlayback()
      } else {
        this.startPlayback()
      }
    },

    resetPlayback () {
      this.pausePlayback()
      this.resetPlaybackMarker()
    },

    /**
     * ========== 更新播放速度 ==========
     * 基于Cesium官方最佳实践：通过时钟multiplier控制播放速度
     */
    updatePlaybackSpeed (speed) {
      this.playbackSpeed = speed
      // 如果正在播放，更新Cesium时钟multiplier（Cesium官方推荐）
      if (this.map && this.map.clock && this.playbackState === 'playing') {
        this.map.clock.multiplier = speed
      }
    },

    formatSpeedTooltip (val) {
      return `${val}x`
    },

    formatTimelineTooltip (val) {
      // 严格检查：防止访问undefined
      if (!this.trackPoints || !this.trackPoints.length) return '-'
      if (val < 0 || val >= this.trackPoints.length) return '-'
      const point = this.trackPoints[val]
      if (!point) return '-'
      return point.time || '-'
    },

    viewPointDetail (point) {
      this.$alert(
        `<div style="line-height: 1.8;">
          <p><strong>时间：</strong>${point.time || '-'}</p>
          <p><strong>纬度：</strong>${point.lat ? Number(point.lat).toFixed(6) : '-'}</p>
          <p><strong>经度：</strong>${point.lng ? Number(point.lng).toFixed(6) : '-'}</p>
        </div>`,
        '轨迹点详情',
        {
          dangerouslyUseHTMLString: true,
          confirmButtonText: '确定'
        }
      )
    },

    flyToTrack () {
      if (this.mapViewMode === '3d' && this.map && this.trackPoints.length) {
        const Cesium = window.Cesium
        const viewer = this.map
        const centerLng = this.trackPoints.reduce((sum, p) => sum + p.lng, 0) / this.trackPoints.length
        const centerLat = this.trackPoints.reduce((sum, p) => sum + p.lat, 0) / this.trackPoints.length
        const heightOffset = 200000
        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(centerLng, centerLat, heightOffset * 3),
          orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-45),
            roll: 0.0
          },
          duration: 2.0
        })
      }
    },

    fitBounds2D () {
      if (this.map2d && this.trackPoints.length) {
        const latlngs = this.trackPoints.map(p => [p.lat, p.lng])
        const L = window.L
        const bounds = L.latLngBounds(latlngs)
        this.map2d.fitBounds(bounds, { padding: [30, 30] })
      }
    },

    /**
     * ========== 3D地图初始化 ==========
     * 企业级特性：
     * 1. 错误处理：网络异常、库加载失败、数据异常
     * 2. 状态管理：加载状态、错误状态、就绪状态
     * 3. 性能优化：延迟渲染、资源清理、实体管理
     * 4. 用户体验：加载提示、错误提示、平滑动画
     */
    async initMap3D () {
      const Cesium = window.Cesium

      // 1. 前置检查
      if (!Cesium) {
        console.error('[initMap3D] Cesium 未加载，无法渲染3D地图')
        this.mapLoading = false
        this.mapReady = false
        this.mapError = true
        this.$message.warning('3D地图模块加载失败，请检查网络连接或刷新页面重试')
        return
      }

      if (!this.trackPoints.length) {
        console.warn('[initMap3D] 没有轨迹点数据，跳过3D地图渲染')
        this.mapLoading = false
        this.mapReady = false
        this.mapError = false
        return
      }

      // 2. 设置加载状态
      this.mapLoading = true
      this.mapError = false
      this.mapReady = false

      // 3. 清理旧地图实例
      this.destroyMap3D(false)

      try {
        const lastPoint = this.trackPoints[this.trackPoints.length - 1]

        // 4. 配置 Cesium Ion Access Token
        Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5ZmFkZjhlNS03NWY3LTRjZGItYmM2Mi03NThmYzgwYmJjMDEiLCJpZCI6Mzk2MTI1LCJpYXQiOjE3NzIzNjEzMDN9.SL2bhNxRIv-qd2oid8yQojfsdg4-SdQYwEaIUaAMBVA'

        // 5. 多层备用底图方案（企业级容错）
        let imageryProvider = null
        let providerName = ''
        try {
          imageryProvider = await Cesium.IonImageryProvider.fromAssetId(2)
          providerName = 'Cesium Ion Bing Maps'
          console.log('✓ [initMap3D] 使用 Cesium Ion Bing Maps 底图（高质量）')
        } catch (e) {
          console.warn('[initMap3D] Cesium Ion 底图加载失败，尝试备用方案', e)
          try {
            imageryProvider = new Cesium.OpenStreetMapImageryProvider({
              url: 'https://a.tile.openstreetmap.org/',
              credit: '© OpenStreetMap contributors'
            })
            providerName = 'OpenStreetMap'
            console.log('✓ [initMap3D] 使用 OpenStreetMap 底图（开源）')
          } catch (e2) {
            try {
              imageryProvider = new Cesium.ArcGisMapServerImageryProvider({
                url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer',
                credit: '© Esri'
              })
              providerName = 'Esri World Imagery'
              console.log('✓ [initMap3D] 使用 Esri World Imagery 底图')
            } catch (e3) {
              imageryProvider = new Cesium.SingleTileImageryProvider({
                url: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
                rectangle: Cesium.Rectangle.MAX_VALUE
              })
              providerName = '离线单色底图'
              console.warn('⚠ [initMap3D] 使用离线单色底图（无网络连接）')
            }
          }
        }

        // 6. 初始化 Cesium Viewer - 产品级优化配置
        this.map = new Cesium.Viewer('track-map-3d', {
          imageryProvider: imageryProvider,
          terrainProvider: new Cesium.EllipsoidTerrainProvider(),
          animation: false,
          timeline: false,
          baseLayerPicker: false,
          geocoder: false,
          homeButton: false,
          navigationHelpButton: false,
          sceneModePicker: false,
          fullscreenButton: false,
          vrButton: false
        })
        const viewer = this.map

        // ========== 核心视觉优化：深色宇宙背景 + 真实地球效果 ==========
        // 1. 深色宇宙背景（类似 Google Earth）
        viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#000000') // 纯黑背景，营造深邃宇宙感

        // 2. 地球渲染优化（真实、美观）
        viewer.scene.globe.enableLighting = true
        viewer.scene.globe.dynamicAtmosphereLighting = true
        viewer.scene.globe.dynamicAtmosphereLightingFromSun = true
        viewer.scene.globe.atmosphereLighting = true
        viewer.scene.globe.atmosphereBrightnessShift = 0.08 // 降低亮度偏移，更自然
        viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString('#0a1929') // 深蓝色海洋基础色
        viewer.scene.globe.oceanNormalMapUrl = Cesium.buildModuleUrl('Assets/Textures/waterNormalsSmall.jpg')
        viewer.scene.globe.enableWaterEffect = true
        viewer.scene.globe.showWaterEffect = true
        viewer.scene.globe.showGroundAtmosphere = true
        viewer.scene.globe.depthTestAgainstTerrain = true
        viewer.scene.globe.terrainExaggeration = 1.3 // 增强地形立体感

        // 3. 雾效优化（增强空间感）
        viewer.scene.fog.enabled = true
        viewer.scene.fog.density = 0.00003 // 降低雾效，保持清晰

        // 4. 影像图层优化（提升画质）
        const mainImageryLayer = viewer.imageryLayers.get(0)
        if (mainImageryLayer && providerName !== '离线单色底图') {
          mainImageryLayer.brightness = 1.15 // 提亮
          mainImageryLayer.contrast = 1.25 // 增强对比度
          mainImageryLayer.saturation = 1.3 // 增强饱和度
          mainImageryLayer.gamma = 1.2 // 提升细节
        }

        // 5. 相机控制优化（流畅交互）
        viewer.scene.screenSpaceCameraController.enableRotate = true
        viewer.scene.screenSpaceCameraController.enableTranslate = true
        viewer.scene.screenSpaceCameraController.enableZoom = true
        viewer.scene.screenSpaceCameraController.enableTilt = true
        viewer.scene.screenSpaceCameraController.enableLook = true
        viewer.scene.screenSpaceCameraController.minimumZoomDistance = 1000
        viewer.scene.screenSpaceCameraController.maximumZoomDistance = 40000000
        viewer.scene.screenSpaceCameraController.inertiaSpin = 0.9
        viewer.scene.screenSpaceCameraController.inertiaTranslate = 0.9
        viewer.scene.screenSpaceCameraController.inertiaZoom = 0.8

        // ========== Cesium官方最佳实践：使用SampledPositionProperty实现时间驱动的轨迹动画 ==========
        const centerLng = this.trackPoints.reduce((sum, p) => sum + p.lng, 0) / this.trackPoints.length
        const centerLat = this.trackPoints.reduce((sum, p) => sum + p.lat, 0) / this.trackPoints.length

        // 轨迹高度：200公里，明显悬浮在地球上方
        const heightOffset = 200000

        // 1. 创建时间序列位置属性（Cesium官方推荐方式）
        // 参考：Cesium Sandcastle "Path" 示例
        const positionProperty = new Cesium.SampledPositionProperty()
        const startTime = Cesium.JulianDate.fromDate(new Date(this.trackPoints[0].time || Date.now()))
        const stopTime = Cesium.JulianDate.fromDate(new Date(lastPoint.time || Date.now()))

        // 将轨迹点转换为时间序列位置
        this.trackPoints.forEach((point, index) => {
          const time = Cesium.JulianDate.addSeconds(
            startTime,
            (index / (this.trackPoints.length - 1)) * Cesium.JulianDate.secondsDifference(stopTime, startTime),
            new Cesium.JulianDate()
          )
          const position = Cesium.Cartesian3.fromRadians(
            Cesium.Math.toRadians(point.lng),
            Cesium.Math.toRadians(point.lat),
            heightOffset
          )
          positionProperty.addSample(time, position)
        })

        // 设置插值算法（Hermite插值，平滑轨迹）
        positionProperty.setInterpolationOptions({
          interpolationDegree: 2,
          interpolationAlgorithm: Cesium.HermitePolynomialApproximation
        })

        // 2. 创建轨迹路径实体（使用PathGraphics，Cesium官方推荐）
        // 参考：Cesium Sandcastle "Path" 示例
        const trackEntity = viewer.entities.add({
          name: 'trackPolyline',
          availability: new Cesium.TimeIntervalCollection([
            new Cesium.TimeInterval({
              start: startTime,
              stop: stopTime
            })
          ]),
          position: positionProperty,
          // 使用PathGraphics显示轨迹路径（带时间信息）
          path: {
            resolution: 1,
            material: new Cesium.PolylineGlowMaterialProperty({
              glowPower: 0.4,
              color: Cesium.Color.fromCssColorString('#60a5fa').withAlpha(0.95)
            }),
            width: 8,
            leadTime: 0,
            trailTime: Cesium.JulianDate.secondsDifference(stopTime, startTime), // 显示完整轨迹
            show: true
          },
          // 轨迹线（静态显示完整路径）
          polyline: {
            positions: this.trackPoints.map(p => {
              return Cesium.Cartesian3.fromRadians(
                Cesium.Math.toRadians(p.lng),
                Cesium.Math.toRadians(p.lat),
                heightOffset
              )
            }),
            width: 8,
            material: new Cesium.PolylineGlowMaterialProperty({
              glowPower: 0.4,
              color: Cesium.Color.fromCssColorString('#60a5fa').withAlpha(0.95)
            }),
            clampToGround: false,
            heightReference: Cesium.HeightReference.NONE,
            arcType: Cesium.ArcType.GEODESIC,
            depthFailMaterial: Cesium.Color.fromCssColorString('#60a5fa').withAlpha(0.7)
          }
        })

        // 3. 创建动态播放点实体（使用时间驱动的位置）
        // 参考：Cesium Sandcastle "Path" 示例中的动态点
        const playbackEntity = viewer.entities.add({
          name: 'trackPlayback',
          availability: new Cesium.TimeIntervalCollection([
            new Cesium.TimeInterval({
              start: startTime,
              stop: stopTime
            })
          ]),
          position: positionProperty,
          // 动态点：橙色，明显
          point: {
            pixelSize: 22,
            color: Cesium.Color.fromCssColorString('#f59e0b'),
            heightReference: Cesium.HeightReference.NONE,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 4,
            scaleByDistance: new Cesium.NearFarScalar(1.5e2, 3.0, 1.5e7, 0.6),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          // 方向属性：让点朝向运动方向（Cesium官方推荐）
          orientation: new Cesium.VelocityOrientationProperty(positionProperty),
          // 标签：显示时间、经纬度
          label: {
            text: '',
            font: '13px "Microsoft YaHei", sans-serif',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            showBackground: false,
            fillColor: Cesium.Color.fromCssColorString('#ffffff'),
            outlineColor: Cesium.Color.fromCssColorString('#000000'),
            outlineWidth: 3,
            pixelOffset: new Cesium.Cartesian2(28, -14),
            horizontalOrigin: Cesium.HorizontalOrigin.LEFT,
            scale: 1.3,
            scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.3, 1.5e7, 0.3),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          }
        })

        // 4. 起点/终点标记（静态位置）
        const first = this.trackPoints[0]
        const startPos = Cesium.Cartesian3.fromRadians(
          Cesium.Math.toRadians(first.lng),
          Cesium.Math.toRadians(first.lat),
          heightOffset
        )
        const endPos = Cesium.Cartesian3.fromRadians(
          Cesium.Math.toRadians(lastPoint.lng),
          Cesium.Math.toRadians(lastPoint.lat),
          heightOffset
        )

        // 起点：绿色
        viewer.entities.add({
          name: 'trackStart',
          position: startPos,
          point: {
            pixelSize: 20,
            color: Cesium.Color.fromCssColorString('#22c55e'),
            heightReference: Cesium.HeightReference.NONE,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 4,
            scaleByDistance: new Cesium.NearFarScalar(1.5e2, 2.5, 1.5e7, 0.6),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          label: {
            text: '起点',
            font: '14px "Microsoft YaHei", sans-serif',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            showBackground: false,
            fillColor: Cesium.Color.fromCssColorString('#ffffff'),
            outlineColor: Cesium.Color.fromCssColorString('#000000'),
            outlineWidth: 3,
            pixelOffset: new Cesium.Cartesian2(0, -40),
            scale: 1.1,
            scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.1, 1.5e7, 0.3),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          }
        })

        // 终点：红色
        viewer.entities.add({
          name: 'trackEnd',
          position: endPos,
          point: {
            pixelSize: 20,
            color: Cesium.Color.fromCssColorString('#ef4444'),
            heightReference: Cesium.HeightReference.NONE,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 4,
            scaleByDistance: new Cesium.NearFarScalar(1.5e2, 2.5, 1.5e7, 0.6),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          label: {
            text: '终点',
            font: '14px "Microsoft YaHei", sans-serif',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            showBackground: false,
            fillColor: Cesium.Color.fromCssColorString('#ffffff'),
            outlineColor: Cesium.Color.fromCssColorString('#000000'),
            outlineWidth: 3,
            pixelOffset: new Cesium.Cartesian2(0, -40),
            scale: 1.1,
            scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.1, 1.5e7, 0.3),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          }
        })

        // 5. 保存时间范围和位置属性（用于播放控制）
        this.trackTimeRange = {
          start: startTime,
          stop: stopTime
        }
        this.trackPositionProperty = positionProperty

        // ========== 初始视角：地球全貌 ==========
        viewer.camera.setView({
          destination: Cesium.Cartesian3.fromDegrees(centerLng, centerLat, 35000000), // 3.5万公里，看完整地球
          orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-75), // 稍微斜视，更有空间感
            roll: 0.0
          }
        })

        // ========== 自动飞行到轨迹区域 ==========
        setTimeout(() => {
          if (viewer && viewer.entities) {
            viewer.flyTo(viewer.entities, {
              duration: 3.0, // 3秒平滑动画
              offset: new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-50), heightOffset * 2.5)
            })
          }
        }, 2000)

        // 6. 保存实体引用（便于统一管理）
        this.cesiumEntities.polyline = trackEntity
        this.cesiumEntities.playbackMarker = playbackEntity
        this.cesiumEntities.startPoint = viewer.entities.getById('trackStart')
        this.cesiumEntities.endPoint = viewer.entities.getById('trackEnd')

        // 8. 更新状态
        this.mapLoading = false
        this.mapReady = true
        this.mapError = false

        console.log(`[initMap3D] 当前底图方案: ${providerName}`)
        console.log('[initMap3D] Cesium Viewer 初始化完成')

        // 9. 初始化播放标记
        this.resetPlaybackMarker()
      } catch (error) {
        console.error('[initMap3D] 3D地图初始化失败:', error)
        this.mapLoading = false
        this.mapReady = false
        this.mapError = true
        this.$message.error('3D地图初始化失败，请刷新页面重试')
      }
    },

    /**
     * ========== 清理3D地图 ==========
     */
    destroyMap3D (clearData = true) {
      this.pausePlayback()
      if (this.map) {
        try {
          this.map.destroy()
        } catch (e) {
          console.warn('[destroyMap3D] 销毁Cesium Viewer时出错:', e)
        }
        this.map = null
      }
      // 清理实体引用
      this.cesiumEntities = {
        polyline: null,
        startPoint: null,
        endPoint: null,
        playbackMarker: null
      }
      // 清理时间属性
      this.trackTimeRange = null
      this.trackPositionProperty = null
      this.mapReady = false
      if (clearData) {
        this.trackPoints = []
      }
    },
    /**
     * ========== 重置播放标记 ==========
     * 基于Cesium官方最佳实践：使用时钟系统控制时间驱动的实体
     */
    resetPlaybackMarker () {
      const Cesium = window.Cesium
      if (!Cesium || !this.map || !this.trackPoints.length || !this.trackTimeRange) return
      const viewer = this.map

      // 使用Cesium时钟系统：重置时钟到开始时间
      // 参考：Cesium Sandcastle "Path" 示例
      viewer.clock.currentTime = this.trackTimeRange.start.clone()
      viewer.clock.startTime = this.trackTimeRange.start.clone()
      viewer.clock.stopTime = this.trackTimeRange.stop.clone()
      viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP // 播放到结束停止
      viewer.clock.multiplier = 0 // 暂停状态

      // 更新当前播放位置（用于UI显示）
      const first = this.trackPoints[0]
      this.playbackIndex = 0
      this.playbackProgress = 0
      this.playbackTimeLabel = first.time || '-'

      // 更新播放点标签（如果实体已创建）
      if (this.cesiumEntities.playbackMarker) {
        this.updatePlaybackTooltip(first)
      }

      // 重置 2D 地图播放点
      if (this.leafletLayers.playbackMarker && this.map2d && first) {
        this.leafletLayers.playbackMarker.setLatLng([first.lat, first.lng])
        this.updatePlaybackTooltip2D(first)
      }

      // 相机回到轨迹起点
      if (this.trackPositionProperty) {
        const startPosition = this.trackPositionProperty.getValue(this.trackTimeRange.start)
        if (startPosition) {
          viewer.camera.flyTo({
            destination: startPosition,
            orientation: {
              heading: Cesium.Math.toRadians(0),
              pitch: Cesium.Math.toRadians(-45),
              roll: 0.0
            },
            duration: 1.5
          })
        }
      }
    },

    /**
     * ========== 2D地图初始化 ==========
     * 企业级特性：错误处理、状态管理、图层管理
     */
    initMap2D () {
      const L = window.L

      // 1. 前置检查
      if (!L) {
        console.error('[initMap2D] Leaflet 未加载，无法渲染2D地图')
        this.mapLoading = false
        this.map2dReady = false
        this.mapError = true
        this.$message.warning('2D地图模块加载失败，请检查网络连接或刷新页面重试')
        return
      }

      if (!this.trackPoints.length) {
        console.warn('[initMap2D] 没有轨迹点数据，跳过2D地图渲染')
        this.mapLoading = false
        this.map2dReady = false
        this.mapError = false
        return
      }

      // 2. 设置加载状态
      this.mapLoading = true
      this.mapError = false
      this.map2dReady = false

      // 3. 清理旧地图实例
      this.destroyMap2D(false)

      try {
        const centerLng = this.trackPoints.reduce((sum, p) => sum + p.lng, 0) / this.trackPoints.length
        const centerLat = this.trackPoints.reduce((sum, p) => sum + p.lat, 0) / this.trackPoints.length

        // ========== 2D 地图初始化：产品级优化 ==========
        const map2d = L.map('track-map-2d', {
          center: [centerLat, centerLng],
          zoom: 3,
          worldCopyJump: true,
          attributionControl: false,
          zoomControl: true, // 启用缩放控件
          scrollWheelZoom: true // 启用滚轮缩放
        })
        this.map2d = map2d

        // ========== 使用高德地图带标注底图（显示地名、道路、行政区划）==========
        L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scl=1&style=8&x={x}&y={y}&z={z}', {
          subdomains: '1234',
          maxZoom: 18,
          attribution: '© 高德地图'
        }).addTo(map2d)

        const latlngs = this.trackPoints.map(p => [p.lat, p.lng])
        if (!latlngs.length) return

        // 4. 轨迹线：清晰、醒目
        this.leafletLayers.polyline = L.polyline(latlngs, {
          color: '#3b82f6', // 蓝色
          weight: 4, // 加粗
          opacity: 0.95,
          smoothFactor: 1.0
        }).addTo(map2d)

        // 5. 起点标记：绿色，明显
        const first = latlngs[0]
        this.leafletLayers.startMarker = L.circleMarker(first, {
          radius: 8, // 更大
          color: '#22c55e',
          weight: 3,
          fillColor: '#22c55e',
          fillOpacity: 1.0
        }).bindTooltip('起点', {
          permanent: true,
          direction: 'top',
          offset: [0, -8],
          className: 'start-end-tooltip'
        }).addTo(map2d)

        // 6. 终点标记：红色，明显
        const last = latlngs[latlngs.length - 1]
        this.leafletLayers.endMarker = L.circleMarker(last, {
          radius: 8,
          color: '#ef4444',
          weight: 3,
          fillColor: '#ef4444',
          fillOpacity: 1.0
        }).bindTooltip('终点', {
          permanent: true,
          direction: 'top',
          offset: [0, -8],
          className: 'start-end-tooltip'
        }).addTo(map2d)

        // 7. 播放点标记：橙色，明显
        const firstPoint = this.trackPoints[0]
        this.leafletLayers.playbackMarker = L.circleMarker([firstPoint.lat, firstPoint.lng], {
          radius: 10, // 更大
          color: '#f59e0b',
          weight: 4,
          fillColor: '#f59e0b',
          fillOpacity: 1.0
        }).addTo(map2d)

        // 8. 播放点数据标签：时间、经纬度
        this.updatePlaybackTooltip2D(firstPoint)

        // 9. 自适应视野：完整显示轨迹
        map2d.fitBounds(this.leafletLayers.polyline.getBounds(), { padding: [30, 30] })

        // 10. 更新状态
        this.mapLoading = false
        this.map2dReady = true
        this.mapError = false

        console.log('[initMap2D] Leaflet 地图初始化完成')
      } catch (error) {
        console.error('[initMap2D] 2D地图初始化失败:', error)
        this.mapLoading = false
        this.map2dReady = false
        this.mapError = true
        this.$message.error('2D地图初始化失败，请刷新页面重试')
      }
    },

    /**
     * ========== 清理2D地图 ==========
     */
    destroyMap2D (clearData = true) {
      this.pausePlayback()
      if (this.map2d) {
        try {
          this.map2d.remove()
        } catch (e) {
          console.warn('[destroyMap2D] 销毁Leaflet地图时出错:', e)
        }
        this.map2d = null
      }
      // 清理图层引用
      this.leafletLayers = {
        polyline: null,
        startMarker: null,
        endMarker: null,
        playbackMarker: null
      }
      this.map2dReady = false
      if (clearData) {
        this.trackPoints = []
      }
    },
    updatePlaybackTooltip2D (point) {
      if (!this.leafletLayers.playbackMarker || !point) return
      const hasLatLng = point.lat !== undefined && point.lat !== null && point.lng !== undefined && point.lng !== null
      const latStr = hasLatLng ? Number(point.lat).toFixed(4) : '-'
      const lngStr = hasLatLng ? Number(point.lng).toFixed(4) : '-'
      const timeStr = point.time || '-'
      // 格式：字段名：字段值（与3D地图一致）
      const tooltipContent = `
        <div style="font-size: 12px; line-height: 1.8; color: #1f2937; font-family: 'Microsoft YaHei', sans-serif;">
          <div style="margin-bottom: 2px;"><strong>时间：</strong>${timeStr}</div>
          <div style="margin-bottom: 2px;"><strong>纬度：</strong>${latStr}</div>
          <div><strong>经度：</strong>${lngStr}</div>
        </div>
      `
      // 如果已有 tooltip，先解绑再重新绑定
      if (this.leafletLayers.playbackMarker.getTooltip()) {
        this.leafletLayers.playbackMarker.unbindTooltip()
      }
      this.leafletLayers.playbackMarker.bindTooltip(tooltipContent, {
        permanent: true,
        direction: 'right',
        offset: [12, 0],
        className: 'playback-tooltip-2d'
      }).openTooltip()
    },
    /**
     * ========== 时间轴拖动 ==========
     * 基于Cesium官方最佳实践：通过时钟时间控制播放位置
     */
    onTimelineChange (val) {
      const Cesium = window.Cesium
      if (!Cesium || !this.map || !this.trackPoints.length || !this.trackTimeRange) return
      const viewer = this.map

      this.pausePlayback()
      this.playbackIndex = val

      // 计算对应的时间（基于索引比例）
      const progress = val / (this.trackPoints.length - 1)
      const currentTime = Cesium.JulianDate.addSeconds(
        this.trackTimeRange.start,
        progress * Cesium.JulianDate.secondsDifference(this.trackTimeRange.stop, this.trackTimeRange.start),
        new Cesium.JulianDate()
      )

      // 设置Cesium时钟到指定时间（Cesium官方推荐方式）
      viewer.clock.currentTime = currentTime.clone()

      // 获取当前位置并更新UI
      if (this.trackPositionProperty) {
        const position = this.trackPositionProperty.getValue(currentTime)
        if (position && this.trackPoints[val]) {
          const p = this.trackPoints[val]
          this.updatePlaybackTooltip(p)

          // 更新 2D 地图播放点
          if (this.leafletLayers.playbackMarker && this.map2d) {
            this.leafletLayers.playbackMarker.setLatLng([p.lat, p.lng])
            this.updatePlaybackTooltip2D(p)
          }
        }
      }

      this.playbackProgress = this.playbackIndex
      this.playbackTimeLabel = this.trackPoints[val].time || '-'
    },

    /**
     * ========== 开始播放 ==========
     * 基于Cesium官方最佳实践：使用时钟系统控制时间驱动的动画
     * 参考：Cesium Sandcastle "Path" 示例
     */
    startPlayback () {
      const Cesium = window.Cesium
      if (!Cesium || !this.map || !this.trackTimeRange) return
      const viewer = this.map

      this.pausePlayback()
      this.playbackState = 'playing'

      // 配置Cesium时钟（Cesium官方推荐方式）
      viewer.clock.startTime = this.trackTimeRange.start.clone()
      viewer.clock.stopTime = this.trackTimeRange.stop.clone()
      viewer.clock.currentTime = viewer.clock.currentTime || this.trackTimeRange.start.clone()
      viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP // 播放到结束停止
      viewer.clock.multiplier = this.playbackSpeed // 播放速度（1-10倍速）

      // 启用时钟动画（Cesium官方推荐）
      viewer.clock.shouldAnimate = true

      // 监听时钟tick事件，更新UI（Cesium官方推荐）
      // 参考：Cesium Sandcastle "Path" 示例中的时钟监听
      this.clockTickListener = viewer.clock.onTick.addEventListener(() => {
        const currentTime = viewer.clock.currentTime
        const totalSeconds = Cesium.JulianDate.secondsDifference(
          this.trackTimeRange.stop,
          this.trackTimeRange.start
        )
        const elapsedSeconds = Cesium.JulianDate.secondsDifference(
          currentTime,
          this.trackTimeRange.start
        )
        const progress = Math.min(Math.max(elapsedSeconds / totalSeconds, 0), 1)

        // 更新播放进度
        this.playbackIndex = Math.floor(progress * (this.trackPoints.length - 1))
        this.playbackProgress = this.playbackIndex

        // 更新当前时间标签
        if (this.trackPoints[this.playbackIndex]) {
          this.playbackTimeLabel = this.trackPoints[this.playbackIndex].time || '-'
        }

        // 更新2D地图播放点位置
        if (this.trackPositionProperty && this.leafletLayers.playbackMarker && this.map2d) {
          const position = this.trackPositionProperty.getValue(currentTime)
          if (position) {
            const cartographic = Cesium.Cartographic.fromCartesian(position)
            const lat = Cesium.Math.toDegrees(cartographic.latitude)
            const lng = Cesium.Math.toDegrees(cartographic.longitude)
            this.leafletLayers.playbackMarker.setLatLng([lat, lng])
            if (this.trackPoints[this.playbackIndex]) {
              this.updatePlaybackTooltip2D(this.trackPoints[this.playbackIndex])
            }
          }
        }

        // 相机跟随（Cesium官方推荐：使用Camera.follow）
        if (this.mapViewMode === '3d' && this.trackPositionProperty && viewer.camera) {
          const position = this.trackPositionProperty.getValue(currentTime)
          if (position) {
            // 使用lookAt实现平滑跟随（Cesium官方推荐）
            viewer.camera.lookAt(
              position,
              new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-45), 200000 * 3)
            )
          }
        }

        // 检查是否播放完成
        if (Cesium.JulianDate.compare(currentTime, this.trackTimeRange.stop) >= 0) {
          this.pausePlayback()
        }
      })
    },

    /**
     * ========== 暂停播放 ==========
     * 基于Cesium官方最佳实践：停止时钟动画
     */
    pausePlayback () {
      if (this.map && this.map.clock) {
        this.map.clock.shouldAnimate = false
      }
      if (this.clockTickListener) {
        this.clockTickListener() // 移除监听器
        this.clockTickListener = null
      }
      if (this.playbackTimer) {
        clearInterval(this.playbackTimer)
        this.playbackTimer = null
      }
      this.playbackState = 'paused'
    },
    updatePlaybackTooltip (point) {
      if (!this.cesiumEntities.playbackMarker || !point) return
      const hasLatLng = point.lat !== undefined && point.lat !== null && point.lng !== undefined && point.lng !== null
      const latStr = hasLatLng ? Number(point.lat).toFixed(4) : '-'
      const lngStr = hasLatLng ? Number(point.lng).toFixed(4) : '-'
      const timeStr = point.time || '-'
      const text = `时间：${timeStr}\n纬度：${latStr}\n经度：${lngStr}`
      if (this.cesiumEntities.playbackMarker.label) {
        this.cesiumEntities.playbackMarker.label.text = text
      }
    },

    /**
     * ========== 清理所有地图 ==========
     */
    destroyMap (clearData = true) {
      this.pausePlayback()
      this.destroyMap3D(clearData)
      this.destroyMap2D(clearData)
    }
  }
}
</script>

<style scoped>
.device-page { padding: 22px; min-height: 100vh; font-size: 14px; background: #f1f5f9; }
.page-hero { background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%); border: 1px solid #dbeafe; border-radius: 14px; padding: 18px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 22px; font-weight: 700; color: #0f172a; }
.page-subtitle { margin: 6px 0 0; color: #64748b; font-size: 13px; }
.mode-tag { border-radius: 999px; }
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
.desc-box { margin-bottom: 0; }
.detail-meta ::v-deep .el-descriptions-item__label,
.detail-meta ::v-deep .el-descriptions-item__content { font-size: 12px; }
.inner-card { margin-bottom: 12px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06); }
.latest-header { display: flex; justify-content: space-between; align-items: center; }
.latest-header span:first-child { font-size: 13px; font-weight: 600; color: #1f2937; }
.latest-subtitle { color: #94a3b8; font-size: 11px; }
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
.trend-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.trend-header span:first-child { font-size: 13px; font-weight: 600; color: #1f2937; }
.trend-tools { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.trend-table ::v-deep .el-table__body-wrapper .el-table__body td { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.trend-table ::v-deep .el-table__body-wrapper .el-table__body td .cell { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.map-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.map-title-wrap { display: flex; flex-direction: column; gap: 4px; }
.map-title-wrap span:first-child { font-size: 13px; font-weight: 600; color: #1f2937; }
.map-controls { display: flex; align-items: center; gap: 8px; }
.map-tip { color: #909399; font-size: 11px; }
.map-box { width: 100%; height: 360px; border-radius: 10px; overflow: hidden; box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2); }
.map-box-2d { margin-top: 4px; }
.timeline-wrap { margin-top: 10px; }
.timeline-top { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #64748b; margin-bottom: 6px; }
.track-tooltip { background: #ffffff; border-radius: 6px; padding: 2px 6px; color: #0f172a; border: 1px solid #e2e8f0; font-size: 11px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12); }
/* 2D 地图播放点标签样式 */
::v-deep .playback-tooltip-2d {
  background: rgba(255, 255, 255, 0.98) !important;
  border: 2px solid #f59e0b !important;
  border-radius: 8px !important;
  padding: 10px 12px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
  font-family: "Microsoft YaHei", sans-serif !important;
  white-space: nowrap !important;
}
/* 2D 地图起点终点标签样式 */
::v-deep .start-end-tooltip {
  background: rgba(255, 255, 255, 0.95) !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 4px !important;
  padding: 4px 8px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
}
</style>
