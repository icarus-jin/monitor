import Vue from 'vue'
import App from './App.vue'
import router from './router'
import './plugins/element.js'
import './assets/css/global.css'
import axios from 'axios'
import qs from 'qs'

Vue.config.productionTip = false
Vue.config.devtools = false // 禁用 Vue Devtools 提示
Vue.prototype.$axios = axios
Vue.prototype.$qs = qs

axios.defaults.baseURL = '/api'
axios.defaults.timeout = 30000

// 请求拦截器，设置token
axios.interceptors.request.use(config => {
  const token = window.sessionStorage.getItem('token')
  if (token) {
    config.headers.Authorization = token
  }
  return config
})

// 响应拦截器，验证token是否过期
axios.interceptors.response.use(
  response => {
    if (response.data?.code === 10016) {
      window.sessionStorage.clear()
      Vue.prototype.$message.warning('登录状态已失效，请重新登录')
      router.replace('/login')
      return Promise.reject(response)
    }
    return response
  },
  error => {
    Vue.prototype.$message.error('网络异常，请稍后重试')
    return Promise.reject(error)
  }
)

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
