<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div>
        <h1>数据概览</h1>
        <p>气象监测系统整体数据情况</p>
      </div>
      <el-button type="primary" icon="el-icon-refresh" @click="refresh">刷新数据</el-button>
    </div>

    <el-row :gutter="24" class="kpi-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="item in kpiList" :key="item.title">
        <div class="kpi-card">
          <div class="kpi-left">
            <p class="kpi-title">{{ item.title }}</p>
            <h2 class="kpi-value">{{ item.value }}</h2>
            <span class="kpi-desc">{{ item.desc }}</span>
          </div>
          <i :class="item.icon" class="kpi-icon"></i>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="24" class="middle-row">
      <el-col :span="12">
        <div class="panel panel-orange">
          <h3 class="panel-title">设备类型分布</h3>
          <div class="panel-value">浮标 {{ stats.buoy_count }} / 气象站 {{ stats.station_count }}</div>
          <span class="panel-desc">台</span>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="panel panel-blue">
          <h3 class="panel-title">区域设备分布</h3>
          <div class="panel-value">南极 {{ areaStats.south }} · 北极 {{ areaStats.north }} · 亚太 {{ areaStats.apac }}</div>
          <span class="panel-desc">台</span>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="24" class="quick-row">
      <el-col :span="6" v-for="item in quickList" :key="item.path">
        <div class="quick-card" @click="go(item.path)">
          <i :class="item.icon"></i>
          <span>{{ item.title }}</span>
        </div>
      </el-col>
    </el-row>

    <el-card class="quality-card" shadow="never">
      <div slot="header">阶段一数据质量看板（POC）</div>
      <el-row :gutter="16">
        <el-col :span="6">总数据包：{{ dataQuality.total_data_packets }}</el-col>
        <el-col :span="6">有效定位包：{{ dataQuality.valid_position_packets }}</el-col>
        <el-col :span="6">定位有效率：{{ dataQuality.position_valid_rate }}%</el-col>
        <el-col :span="6">最新包时间：{{ dataQuality.latest_packet_time || '-' }}</el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
export default {
  name: 'Dashboard',
  data () {
    return {
      stats: {
        total_devices: 0,
        online_devices: 0,
        offline_devices: 0,
        total_users: 0,
        buoy_count: 0,
        station_count: 0
      },
      areaStats: {
        south: 0,
        north: 0,
        apac: 0
      },
      dataQuality: {
        total_data_packets: 0,
        valid_position_packets: 0,
        position_valid_rate: 0,
        latest_packet_time: ''
      },
      kpiList: [
        { title: '设备总数', value: 0, desc: '台', icon: 'el-icon-s-platform' },
        { title: '在线设备', value: 0, desc: '台', icon: 'el-icon-connection' },
        { title: '离线设备', value: 0, desc: '台', icon: 'el-icon-warning-outline' },
        { title: '用户总数', value: 0, desc: '人', icon: 'el-icon-user-solid' }
      ],
      quickList: [
        { title: '用户管理', icon: 'el-icon-user', path: '/user_list' },
        { title: '设备管理', icon: 'el-icon-s-platform', path: '/device_list' }
      ]
    }
  },
  created () {
    this.getDashboardData()
  },
  methods: {
    async getDashboardData () {
      try {
        const { data: res } = await this.$axios.get('/device/overview/')
        if (res.code !== 200) throw new Error(res.msg || '获取概览失败')

        const d = res.data || {}
        this.stats = {
          total_devices: d.total_devices || 0,
          online_devices: d.online_devices || 0,
          offline_devices: d.offline_devices || 0,
          total_users: d.total_users || 0,
          buoy_count: d.buoy_count || 0,
          station_count: d.station_count || 0
        }

        this.areaStats = {
          south: (d.area_stats && d.area_stats.南极) || 0,
          north: (d.area_stats && d.area_stats.北极) || 0,
          apac: (d.area_stats && d.area_stats.亚太) || 0
        }

        this.dataQuality = {
          total_data_packets: (d.data_quality && d.data_quality.total_data_packets) || 0,
          valid_position_packets: (d.data_quality && d.data_quality.valid_position_packets) || 0,
          position_valid_rate: (d.data_quality && d.data_quality.position_valid_rate) || 0,
          latest_packet_time: (d.data_quality && d.data_quality.latest_packet_time) || ''
        }

        this.kpiList[0].value = this.stats.total_devices
        this.kpiList[1].value = this.stats.online_devices
        this.kpiList[2].value = this.stats.offline_devices
        this.kpiList[3].value = this.stats.total_users
      } catch (e) {
        this.$message.error('概览数据加载失败')
      }
    },
    refresh () {
      this.getDashboardData()
      this.$message.success('数据已刷新')
    },
    go (path) {
      this.$router.push(path)
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 24px;
  min-height: calc(100vh - 120px);
  background: #f1f5f9;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-header h1 {
  font-size: 24px;
  color: #1e293b;
  margin-bottom: 4px;
}

.dashboard-header p {
  font-size: 14px;
  color: #64748b;
}

.kpi-row { margin-bottom: 24px; }

.kpi-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.kpi-title { color: #64748b; font-size: 14px; }
.kpi-value { font-size: 26px; color: #1e293b; margin: 8px 0; }
.kpi-desc { color: #94a3b8; font-size: 13px; }
.kpi-icon { font-size: 36px; color: #3b82f6; }

.middle-row { margin-bottom: 24px; }

.panel {
  border-radius: 12px;
  padding: 24px;
  min-height: 120px;
  color: #fff;
}

.panel-orange { background: linear-gradient(135deg, #f97316, #ea580c); }
.panel-blue { background: linear-gradient(135deg, #3b82f6, #2563eb); }

.panel-title { font-size: 14px; opacity: 0.9; margin-bottom: 8px; }
.panel-value { font-size: 24px; font-weight: 600; line-height: 34px; }
.panel-desc { font-size: 14px; opacity: 0.9; }

.quick-row { margin-top: 24px; }
.quick-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.quick-card i { font-size: 28px; color: #3b82f6; display: block; margin-bottom: 8px; }
.quick-card span { font-size: 14px; color: #334155; }

.quality-card {
  margin-top: 20px;
  border-radius: 12px;
}
</style>
