import { createRouter, createWebHistory } from 'vue-router'

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

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard },
  { path: '/dashboard/dashboard', name: 'Dashboard2', component: Dashboard },
  { path: '/admin/users', name: 'Users', component: Users },
  { path: '/admin/articles', name: 'Articles', component: Articles },
  { path: '/articles/list', name: 'ArticleList', component: ArticleList },
  { path: '/articles/detail', name: 'ArticleDetail', component: ArticleDetail },
  { path: '/pet/recognize', name: 'Recognize', component: Recognize },
  { path: '/pets/encyclopedia', name: 'Encyclopedia', component: Encyclopedia },
  { path: '/pets/detail', name: 'PetDetail', component: PetDetail },
  { path: '/user/profile', name: 'Profile', component: Profile }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

function isTokenExpired(token) {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
    const payload = JSON.parse(jsonPayload)
    return payload.exp * 1000 < Date.now()
  } catch (e) {
    return true
  }
}

router.beforeEach((to, from, next) => {
  const whiteList = ['/login']
  const token = localStorage.getItem('token')

  if (!token || isTokenExpired(token)) {
    localStorage.removeItem('token')
    if (!whiteList.includes(to.path)) {
      next('/login')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
