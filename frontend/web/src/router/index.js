import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../components/Login.vue')
  },
  {
    path: '/home',
    name: 'home',
    component: () => import('../components/Home.vue'),
    redirect: '/home/welcome',
    children: [
      {
        path: 'welcome',
        name: 'welcome',
        component: () => import('../components/Welcome.vue'),
        meta: { noCard: true }
      },
      {
        path: '/user_list',
        name: 'user_list',
        component: () => import('../components/user/User.vue'),
        meta: { title: '用户管理', icon: 'el-icon-user-solid' }
      },
      {
        path: '/device_list',
        name: 'device_list',
        component: () => import('../components/device/DeviceInfo.vue'),
        meta: { title: '设备管理', icon: 'el-icon-s-platform' }
      },
      {
        path: '/receive_log',
        name: 'receive_log',
        component: () => import('../components/data/Data.vue'),
        meta: { title: '数据接收', icon: 'el-icon-s-platform' }
      }
    ]
  }
]

const router = new VueRouter({
  routes
})

const LOGIN_PATH = '/login'
const TOKEN_KEY = 'token'

// 前端控制必须登录才能访问
router.beforeEach((to, from, next) => {
  if (to.path === LOGIN_PATH) return next()
  const token = window.sessionStorage.getItem(TOKEN_KEY)
  if (!token) return next(LOGIN_PATH)

  const userType = Number(window.sessionStorage.getItem('user_type') || 0)
  if (to.path === '/user_list' && userType !== 1) {
    return next('/device_list')
  }

  next()
})

export default router
