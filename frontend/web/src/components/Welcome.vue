<template>
  <div class="dashboard">
    <!-- 顶部 -->
    <div class="dashboard-header">
      <div>
        <h1>数据概览</h1>
        <p>气象监测系统整体数据情况</p>
      </div>
      <el-button type="primary" icon="el-icon-refresh" @click="refresh">刷新数据</el-button>
    </div>

    <!-- KPI 卡片（参考 style_demo 白卡+蓝橙配色）-->
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

    <!-- 中部：重点区域 -->
    <el-row :gutter="24" class="middle-row">
      <el-col :span="12">
        <div class="panel panel-orange">
          <h3 class="panel-title">在线设备数</h3>
          <div class="panel-value">{{ stats.online_devices }}</div>
          <span class="panel-desc">台</span>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="panel panel-blue">
          <h3 class="panel-title">用户总数</h3>
          <div class="panel-value">{{ stats.total_users }}</div>
          <span class="panel-desc">人</span>
        </div>
      </el-col>
    </el-row>

    <!-- 底部：快捷操作 -->
    <el-row :gutter="24" class="quick-row">
      <el-col :span="6" v-for="item in quickList" :key="item.path">
        <div class="quick-card" @click="go(item.path)">
          <i :class="item.icon"></i>
          <span>{{ item.title }}</span>
        </div>
      </el-col>
    </el-row>
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
        total_users: 0
      },
      kpiList: [
        { title: '设备总数', value: 0, desc: '台', icon: 'el-icon-s-platform' },
        { title: '在线设备', value: 0, desc: '台', icon: 'el-icon-connection' },
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
        const [devRes, userRes] = await Promise.all([
          this.$axios.get('/device/list/', { params: { page: 1, page_size: 500 } }),
          this.$axios.get('/user/user_list/', { params: { page: 1, page_size: 1 } })
        ])
        const devTotal = devRes.data?.data?.total ?? 0
        const userTotal = userRes.data?.data?.total ?? 0
        const online = (devRes.data?.data?.device_list || []).filter(d => d.status === 1).length
        this.stats = { total_devices: devTotal, online_devices: online, total_users: userTotal }
        this.kpiList[0].value = devTotal
        this.kpiList[1].value = online
        this.kpiList[2].value = userTotal
      } catch (e) {
        // 接口未就绪时使用模拟数据
        this.stats = { total_devices: 6, online_devices: 3, total_users: 5 }
        this.kpiList[0].value = 6
        this.kpiList[1].value = 3
        this.kpiList[2].value = 5
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
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
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
.panel-value { font-size: 32px; font-weight: 600; }
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
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.quick-card i { font-size: 28px; color: #3b82f6; display: block; margin-bottom: 8px; }
.quick-card span { font-size: 14px; color: #334155; }
</style>
