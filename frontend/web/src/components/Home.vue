<template>
  <el-container class="home-container">
    <el-header class="header">
      <div class="header-left">
        <img src="../assets/logo.png" class="logo" />
        <div>
          <div class="title">气象监测管理系统</div>
          <div class="subtitle">设备数据可视化平台</div>
        </div>
      </div>
      <div class="header-right">
        <div class="user-meta">
          <div class="user-name">{{ username || '未登录用户' }}</div>
        </div>
        <el-button type="text" class="logout-btn" @click="logout">安全退出</el-button>
      </div>
    </el-header>

    <el-container>
      <el-aside class="aside" :width="asideWidth">
        <el-menu
          router
          :default-active="$route.path"
          :collapse="isCollapse"
          background-color="#ffffff"
          text-color="#475569"
          active-text-color="#2563eb"
        >
          <el-submenu v-for="item in menuList" :key="item.id" :index="String(item.id)">
            <template slot="title">
              <i :class="getIcon(item.id)" class="menu-icon"></i>
              <span>{{ item.name }}</span>
            </template>
            <el-menu-item v-for="subItem in item.children" :key="subItem.id" :index="String(subItem.path)">
              <i :class="getIcon(subItem.id)" class="submenu-icon"></i>
              <span>{{ subItem.name }}</span>
            </el-menu-item>
          </el-submenu>
        </el-menu>
      </el-aside>

      <el-main class="main">
        <div v-if="showCard" class="content-card">
          <router-view />
        </div>
        <router-view v-else />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
export default {
  name: 'Home',
  created () { this.getMenuList() },
  data () {
    return {
      username: window.sessionStorage.getItem('username'),
      isCollapse: true,
      menuList: [],
      iconMap: {
        2: 'el-icon-user-solid',
        3: 'el-icon-s-platform',
        21: 'el-icon-user',
        31: 'el-icon-s-platform'
      }
    }
  },
  computed: {
    showCard () { return !this.$route.meta.noCard },
    asideWidth () { return this.isCollapse ? '72px' : '220px' }
  },
  methods: {
    getMenuList () {
      this.menuList = [
        { id: 2, name: '用户管理', children: [{ id: 21, name: '用户列表', path: '/user_list' }] },
        { id: 3, name: '设备管理', children: [{ id: 31, name: '设备列表', path: '/device_list' }] }
      ]
    },
    getIcon (id) { return this.iconMap[id] || 'el-icon-menu' },
    logout () {
      window.sessionStorage.removeItem('token')
      window.sessionStorage.removeItem('username')
      this.$router.push('/login')
      this.$message.success('已退出登录')
    }
  }
}
</script>

<style>
.home-container { height: 100%; background: #edf2f7; }

.header {
  height: 64px;
  background: linear-gradient(90deg, #ffffff 0%, #f8fbff 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
}

.header-left { display: flex; align-items: center; gap: 10px; }
.logo { height: 34px; }
.title { font-size: 17px; font-weight: 700; color: #0f172a; line-height: 1; }
.subtitle { font-size: 12px; color: #64748b; margin-top: 4px; }

.header-right { display: flex; align-items: center; gap: 14px; }
.user-meta { line-height: 1.15; text-align: right; }
.user-name { color: #1e293b; font-size: 13px; font-weight: 600; }
.user-role { color: #94a3b8; font-size: 11px; margin-top: 2px; }
.logout-btn { color: #64748b; padding: 0; }
.logout-btn:hover { color: #2563eb; }

.aside {
  background: #fff;
  padding-top: 12px;
  border-right: 1px solid #e2e8f0;
  transition: width 0.2s ease;
}
.el-menu { border-right: none !important; }

.el-submenu__title {
  height: 46px;
  line-height: 46px;
  margin: 4px 10px;
  padding-left: 16px !important;
  border-radius: 10px;
}
.el-submenu__title:hover { background: #f1f5f9 !important; }

.el-menu .el-menu-item {
  height: 40px;
  line-height: 40px;
  margin: 4px 14px;
  padding-left: 40px !important;
  border-radius: 10px;
}
.el-menu .el-menu-item:hover { background: #f1f5f9 !important; }
.el-menu .el-menu-item.is-active { background: #eff6ff !important; color: #2563eb !important; }

.menu-icon { margin-right: 10px; font-size: 17px; color: #64748b; }
.submenu-icon { margin-right: 10px; font-size: 14px; color: #94a3b8; }
.el-menu-item.is-active .submenu-icon { color: #2563eb; }

.main { background-color: #edf2f7; padding: 18px; }

.content-card {
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  border-radius: 14px;
  padding: 20px;
  min-height: 420px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}
</style>
