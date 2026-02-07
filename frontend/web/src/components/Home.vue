<template>
  <el-container class="home-container">
    <!-- Header -->
    <el-header class="header">
      <div class="header-left">
        <img src="../assets/logo.png" class="logo" />
        <span class="title">电商管理系统</span>
      </div>

      <div class="header-right">
        <span class="user">{{ username }}</span>
        <el-divider direction="vertical"></el-divider>
        <el-button type="text" class="logout-btn" @click="logout">
          退出
        </el-button>
      </div>
    </el-header>

    <el-container>
      <!-- Aside -->
      <el-aside class="aside" width="220px">
        <el-menu
          router
          :default-active="$route.path"
          :collapse="isCollapse"
          background-color="transparent"
          text-color="#cbd5e1"
          active-text-color="#38bdf8"
        >
          <el-submenu
            v-for="item in menuList"
            :key="item.id"
            :index="String(item.id)"
          >
            <!-- 一级菜单 -->
            <template slot="title">
              <i :class="getIcon(item.id)" class="menu-icon"></i>
              <span>{{ item.name }}</span>
            </template>

            <!-- 二级菜单 -->
            <el-menu-item
              v-for="subItem in item.children"
              :key="subItem.id"
              :index="String(subItem.path)"
            >
              <i :class="getIcon(subItem.id)" class="submenu-icon"></i>
              <span>{{ subItem.name }}</span>
            </el-menu-item>
          </el-submenu>
        </el-menu>
      </el-aside>

      <!-- Main -->
      <el-main class="main">
        <!-- 有白卡 -->
        <div v-if="showCard" class="content-card">
          <router-view />
        </div>

        <!-- 无白卡（Dashboard 等） -->
        <router-view v-else />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
export default {
  name: 'Home',
  created () {
    this.getMenuList()
  },
  data () {
    return {
      username: window.sessionStorage.getItem('username'),
      isCollapse: false,
      menuList: [],
      /**
       * ⭐ 菜单图标映射（通过 id 控制）
       * key = 后端返回的 id
       * value = Element UI 图标类名
       */
      iconMap: {
        // 一级菜单
        2: 'el-icon-user-solid', // 用户管理
        3: 'el-icon-s-check', // 权限管理
        4: 'el-icon-goods', // 商品管理
        5: 'el-icon-s-order', // 订单管理
        6: 'el-icon-data-analysis', // 数据统计
        21: 'el-icon-user', // 用户列表
        31: 'el-icon-s-custom', // 角色列表
        32: 'el-icon-lock' // 权限列表
      }
    }
  },
  computed: {
    /**
     * 是否显示白色内容卡
     * 默认显示，只有 meta.noCard = true 才隐藏
     */
    showCard () {
      return !this.$route.meta.noCard
    }
  },
  methods: {
    getMenuList () {
      this.$axios.get('/menu/').then(res => {
        this.menuList = res.data.data
      })
    },
    /**
     * 根据菜单 id 获取图标
     */
    getIcon (id) {
      return this.iconMap[id] || 'el-icon-menu'
    },
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
/* ======================
   全局
====================== */
html,
body,
#app {
  height: 100%;
  margin: 0;
  background-color: #020617;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
    "Helvetica Neue", Arial;
}

/* ======================
   容器
====================== */
.home-container {
  height: 100%;
  background-color: #020617;
}

/* ======================
   Header
====================== */
.header {
  height: 120px;
  background: linear-gradient(90deg, #020617, #020617);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 36px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.6);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  height: 48px;
  margin-right: 14px;
}

.title {
  font-size: 22px;
  font-weight: 600;
  color: #e5e7eb;
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user {
  color: #cbd5e1;
}

.logout-btn {
  color: #94a3b8;
  padding: 0;
}

.logout-btn:hover {
  color: #38bdf8;
}

/* ======================
   Aside
====================== */
.aside {
  background-color: #020617;
  padding-top: 12px;
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.06);
}

/* ======================
   Menu 基础
====================== */
.el-menu {
  background-color: transparent !important;
  border-right: none;
}

/* ======================
   一级菜单
====================== */
.el-submenu__title {
  height: 48px;
  line-height: 48px;
  margin: 8px 12px;
  padding-left: 18px !important;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #e5e7eb !important;
  transition: all 0.25s ease;
}

.el-submenu__title:hover {
  background: linear-gradient(
    90deg,
    rgba(56, 189, 248, 0.3),
    rgba(56, 189, 248, 0.08)
  ) !important;
  color: #ffffff !important;
}

/* ======================
   二级菜单
====================== */
.el-menu .el-menu-item {
  height: 42px;
  line-height: 42px;
  margin: 4px 20px;
  padding-left: 42px !important;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 400;
  color: #cbd5e1 !important;
  transition: all 0.25s ease;
}

.el-menu .el-menu-item:hover {
  background: linear-gradient(
    90deg,
    rgba(56, 189, 248, 0.18),
    rgba(56, 189, 248, 0.04)
  ) !important;
  color: #ffffff !important;
}

.el-menu .el-menu-item.is-active {
  background: linear-gradient(
    90deg,
    rgba(56, 189, 248, 0.45),
    rgba(56, 189, 248, 0.12)
  ) !important;
  color: #ffffff !important;
  box-shadow: 0 0 14px rgba(56, 189, 248, 0.4);
}

/* ======================
   图标
====================== */
.menu-icon {
  margin-right: 10px;
  font-size: 18px;
  color: #38bdf8;
}

.submenu-icon {
  margin-right: 10px;
  font-size: 15px;
  color: #94a3b8;
}

.el-menu-item.is-active .submenu-icon,
.el-submenu.is-active .menu-icon {
  color: #ffffff;
}

/* ======================
   Main
====================== */
.main {
  background-color: #f1f5f9;
  padding: 24px;
}

/* ======================
   内容白卡
====================== */
.content-card {
  background-color: #ffffff;
  border-radius: 14px;
  padding: 28px;
  min-height: 300px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.12);
}
</style>
