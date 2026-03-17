/**
 * 应用入口文件
 * 负责创建 Vue 应用实例并挂载到 DOM
 */
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import uni, { setRouter } from './utils/uni-adapter'

// 创建应用实例
const app = createApp(App)

// 设置 Vue Router 实例到 uni-adapter
setRouter(router)

// 全局挂载 uni 对象，使所有组件都可以使用 uni-app API
app.config.globalProperties.uni = uni

// 使用路由
app.use(router)

// 挂载应用到 #app 元素
app.mount('#app')