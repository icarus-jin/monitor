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

    <el-card shadow="never" class="table-card">
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

    <el-dialog :visible.sync="dataVisible" width="1200px" top="3vh" class="device-detail-dialog">
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
  </div>
</template>

<script>
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
      trendDateRange: [],
      trendRangeType: '1y',
      trendPage: 1,
      trendPageSize: 100,
      trendTotal: 0
    }
  },
  computed: {
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
        return
      }
      const now = new Date()
      const endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
      const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000)
      this.trendDateRange = [
        this.formatDate(startDate),
        this.formatDate(endDate)
      ]
    },
    handleCustomDateChange (value) {
      if (value && value.length === 2) {
        this.loadTrendData()
      }
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
      if (formatted.includes('：') && !formatted.includes('标志')) {
        formatted = formatted.split('：')[0].trim()
      }
      return formatted || label
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
      this.trendPage = 1
      this.trendPageSize = 100
      this.trendTotal = 0
      this.trendRangeType = '1y'
      this.dataVisible = true
      this.updateTrendDateRange()
    },
    getTrendDateParams () {
      if (this.trendRangeType !== 'custom') {
        this.updateTrendDateRange()
      }
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

        await this.loadTrendData()
      } catch (error) {
        console.error('[showData] 加载设备详情失败:', error)
        this.$message.error('加载设备详情失败，请稍后重试')
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
.trend-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.trend-header span:first-child { font-size: 13px; font-weight: 600; color: #1f2937; }
.trend-tools { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.trend-table ::v-deep .el-table__body-wrapper .el-table__body td { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.trend-table ::v-deep .el-table__body-wrapper .el-table__body td .cell { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
