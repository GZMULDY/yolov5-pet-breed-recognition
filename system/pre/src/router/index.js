/**
 * 路由配置文件
 * 定义所有页面路由及路由守卫
 */
import { createRouter, createWebHistory } from 'vue-router'

// 导入页面组件
import Login from '../pages/login/login.vue'
import Dashboard from '../pages/dashboard/dashboard.vue'
import Users from '../pages/admin/users.vue'
import Articles from '../pages/admin/articles.vue'
import ArticleList from '../pages/articles/list.vue'
import ArticleDetail from '../pages/articles/detail.vue'
import Recognize from '../pages/pet/recognize.vue'
import Encyclopedia from '../pages/pets/encyclopedia.vue'
import PetDetail from '../pages/pets/detail.vue'
import Profile from '../pages/user/profile.vue'

/**
 * 路由数组
 * 每个对象包含：
 * - path: 路由路径
 * - name: 路由名称
 * - component: 对应的页面组件
 */
const routes = [
  // 默认重定向到登录页
  { path: '/', redirect: '/login' },
  // 登录页
  { path: '/login', name: 'Login', component: Login },
  // 控制台/仪表盘（支持两种路径）
  { path: '/dashboard', name: 'Dashboard', component: Dashboard },
  { path: '/dashboard/dashboard', name: 'Dashboard2', component: Dashboard },
  // 用户管理
  { path: '/admin/users', name: 'Users', component: Users },
  // 文章管理
  { path: '/admin/articles', name: 'Articles', component: Articles },
  // 文章列表
  { path: '/articles/list', name: 'ArticleList', component: ArticleList },
  // 文章详情
  { path: '/articles/detail', name: 'ArticleDetail', component: ArticleDetail },
  // 宠物识别
  { path: '/pet/recognize', name: 'Recognize', component: Recognize },
  // 宠物百科
  { path: '/pets/encyclopedia', name: 'Encyclopedia', component: Encyclopedia },
  // 宠物详情
  { path: '/pets/detail', name: 'PetDetail', component: PetDetail },
  // 用户个人信息
  { path: '/user/profile', name: 'Profile', component: Profile }
]

// 创建路由实例
const router = createRouter({
  // 使用 HTML5 History 模式（URL 不带 # 号）
  history: createWebHistory(),
  // 路由配置
  routes
})

/**
 * 路由守卫 - 全局前置守卫
 * 在每次路由跳转前检查用户登录状态
 * @param {Object} to - 目标路由对象
 * @param {Object} from - 来源路由对象
 * @param {Function} next - 放行函数
 */
router.beforeEach((to, from, next) => {
  // 白名单：无需登录即可访问的页面路径
  const whiteList = ['/login']
  
  // 从本地存储获取 Token
  const token = localStorage.getItem('token')
  
  // 如果目标页面不在白名单且没有 Token，则跳转到登录页
  if (!token && !whiteList.includes(to.path)) {
    next('/login')
  } else {
    // 放行
    next()
  }
})

// 导出路由实例
export default router