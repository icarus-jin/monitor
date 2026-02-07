<template>
  <div class="dashboard">

    <!-- 顶部欢迎 -->
    <div class="dashboard-header">
      <div>
        <h1>欢迎回来，{{ username }}</h1>
        <p>今天是 {{ today }}，祝你工作顺利 😄</p>
      </div>

      <el-button type="primary" icon="el-icon-refresh" @click="refresh">
        刷新数据
      </el-button>
    </div>

    <!-- 指标卡 -->
    <el-row :gutter="24" class="kpi-row">
      <el-col :span="6" v-for="item in kpiList" :key="item.title">
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

    <!-- 中部区域 -->
    <el-row :gutter="24" class="middle-row">
      <!-- 快捷入口 -->
      <el-col :span="12">
        <div class="panel">
          <h3 class="panel-title">快捷操作</h3>

          <div class="quick-actions">
            <div
              class="quick-item"
              v-for="item in quickList"
              :key="item.title"
              @click="go(item.path)"
            >
              <i :class="item.icon"></i>
              <span>{{ item.title }}</span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 系统信息 -->
      <el-col :span="12">
        <div class="panel">
          <h3 class="panel-title">系统提示</h3>

          <ul class="notice-list">
            <li v-for="(item, index) in noticeList" :key="index">
              <i class="el-icon-warning-outline"></i>
              <span>{{ item }}</span>
            </li>
          </ul>
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
      username: window.sessionStorage.getItem('username') || '管理员',
      today: '',
      kpiList: [
        { title: '今日订单', value: 0, desc: '单', icon: 'el-icon-s-order' },
        { title: '今日销售额', value: '￥0.00', desc: '元', icon: 'el-icon-s-finance' },
        { title: '用户总数', value: 0, desc: '人', icon: 'el-icon-user-solid' },
        { title: '商品总数', value: 0, desc: '件', icon: 'el-icon-goods' }
      ],
      quickList: [
        { title: '订单管理', icon: 'el-icon-s-order', path: '/orders' },
        { title: '商品管理', icon: 'el-icon-goods', path: '/goods' },
        { title: '用户管理', icon: 'el-icon-user', path: '/users' },
        { title: '数据报表', icon: 'el-icon-data-analysis', path: '/reports' }
      ],
      noticeList: [
        '今日还存在待发货订单',
        '库存低于警戒线的商品有 2 件',
        '系统将于今晚 02:00 进行例行维护',
        '慢慢进步中...................'
      ]
    }
  },
  created () {
    this.today = this.formatDate(new Date())
    // this.getDashboardData()
  },
  methods: {
    formatDate (date) {
      const y = date.getFullYear()
      const m = String(date.getMonth() + 1).padStart(2, '0')
      const d = String(date.getDate()).padStart(2, '0')
      return `${y}-${m}-${d}`
    },
    refresh () {
      this.$message.success('数据已刷新')
      // this.getDashboardData()
    },
    go (path) {
      this.$router.push(path)
    }
    // 后续对接接口
    // getDashboardData () {
    //   this.$axios.get('/dashboard').then(res => {
    //     const data = res.data.data
    //     this.kpiList[0].value = data.todayOrder
    //     ...
    //   })
    // }
  }
}
</script>

<style scoped>
.dashboard {
  background: #020617;
  padding: 28px;
  min-height: calc(100vh - 120px);
  border-radius: 12px;
}

/* ======================
   Header
====================== */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.dashboard-header h1 {
  color: #f8fafc;
  font-size: 26px;
  margin-bottom: 6px;
}

.dashboard-header p {
  color: #94a3b8;
  font-size: 14px;
}

/* ======================
   KPI
====================== */
.kpi-row {
  margin-bottom: 28px;
}

.kpi-card {
  background: linear-gradient(145deg, #020617, #020617);
  border-radius: 18px;
  padding: 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow:
    0 12px 36px rgba(0, 0, 0, 0.65),
    inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  transition: transform 0.25s ease;
}

.kpi-card:hover {
  transform: translateY(-6px);
}

.kpi-title {
  color: #94a3b8;
  font-size: 14px;
}

.kpi-value {
  color: #f8fafc;
  font-size: 28px;
  margin: 6px 0;
}

.kpi-desc {
  color: #64748b;
  font-size: 13px;
}

.kpi-icon {
  font-size: 36px;
  color: #38bdf8;
  opacity: 0.9;
}

/* ======================
   Panel
====================== */
.panel {
  background: #020617;
  border-radius: 18px;
  padding: 22px;
  height: 100%;
  box-shadow:
    0 18px 48px rgba(0, 0, 0, 0.65),
    inset 0 0 0 1px rgba(255, 255, 255, 0.06);
}

.panel-title {
  color: #e5e7eb;
  font-size: 18px;
  margin-bottom: 18px;
}

/* ======================
   Quick
====================== */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
}

.quick-item {
  background: rgba(15, 23, 42, 0.8);
  border-radius: 14px;
  padding: 18px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
}

.quick-item i {
  font-size: 26px;
  color: #38bdf8;
  margin-bottom: 10px;
}

.quick-item span {
  color: #cbd5e1;
  font-size: 14px;
}

.quick-item:hover {
  background: linear-gradient(
    145deg,
    rgba(56, 189, 248, 0.3),
    rgba(56, 189, 248, 0.08)
  );
  transform: translateY(-4px);
}

/* ======================
   Notice
====================== */
.notice-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.notice-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #cbd5e1;
  font-size: 14px;
  padding: 10px 0;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
}

.notice-list li:last-child {
  border-bottom: none;
}

.notice-list i {
  color: #f59e0b;
}
</style>
