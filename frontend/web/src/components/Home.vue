<template>
  <el-container class="home-container">
    <el-header class="header">
      <div class="header-left">
        <img src="../assets/logo.png" class="logo" />
        <span class="title">气象监测管理系统</span>
      </div>
      <div class="header-right">
        <span class="user">{{ username }}</span>
        <el-divider direction="vertical"></el-divider>
        <el-button type="text" class="logout-btn" @click="logout">退出</el-button>
      </div>
    </el-header>

    <el-container>
      <el-aside class="aside" width="220px">
        <el-menu
          router
          :default-active="$route.path"
          :collapse="isCollapse"
          background-color="#ffffff"
          text-color="#475569"
          active-text-color="#3b82f6"
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
      isCollapse: false,
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
    showCard () { return !this.$route.meta.noCard }
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
      this.$message.success('退出成功')
    }
  }
}
</script>

<style>
html, body, #app { height: 100%; margin: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial; }

.home-container { height: 100%; background-color: #f1f5f9; }

.header {
  height: 60px;
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid #e2e8f0;
}

.header-left { display: flex; align-items: center; }
.logo { height: 36px; margin-right: 12px; }
.title { font-size: 18px; font-weight: 600; color: #1e293b; }

.header-right { display: flex; align-items: center; gap: 12px; }
.user { color: #475569; font-size: 14px; }
.logout-btn { color: #64748b; padding: 0; }
.logout-btn:hover { color: #3b82f6; }

.aside {
  background: #fff;
  padding-top: 12px;
  border-right: 1px solid #e2e8f0;
}

.el-menu { border-right: none !important; }

.el-submenu__title {
  height: 48px;
  line-height: 48px;
  margin: 4px 12px;
  padding-left: 18px !important;
  border-radius: 8px;
  font-size: 14px;
  color: #475569 !important;
}

.el-submenu__title:hover { background: #f1f5f9 !important; color: #1e293b !important; }

.el-menu .el-menu-item {
  height: 42px;
  line-height: 42px;
  margin: 4px 16px;
  padding-left: 42px !important;
  border-radius: 8px;
  font-size: 14px;
  color: #64748b !important;
}

.el-menu .el-menu-item:hover { background: #f1f5f9 !important; color: #1e293b !important; }
.el-menu .el-menu-item.is-active { background: #eff6ff !important; color: #3b82f6 !important; }

.menu-icon { margin-right: 10px; font-size: 18px; color: #64748b; }
.submenu-icon { margin-right: 10px; font-size: 14px; color: #94a3b8; }
.el-menu-item.is-active .submenu-icon { color: #3b82f6; }

.main { background-color: #f1f5f9; padding: 20px; }

.content-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  min-height: 400px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
</style>
