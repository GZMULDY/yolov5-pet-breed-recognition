import { reactive, readonly } from 'vue'
import { getCurrentUser } from '@/api/auth.js'

const state = reactive({
  username: '',
  nickname: '',
  avatar: null,
  role: 'user',
  loaded: false
})

export function useUserStore() {
  const fetchUser = async () => {
    try {
      const res = await getCurrentUser()
      if (res && res.data) {
        let avatarUrl = null
        if (res.data.avatar) {
          avatarUrl = `data:image/jpeg;base64,${res.data.avatar}`
        }
        state.username = res.data.username || ''
        state.nickname = res.data.nickname || ''
        state.avatar = avatarUrl
        state.role = res.data.role || 'user'
        state.loaded = true
      }
    } catch (e) {
      console.error('Fetch user info error:', e)
    }
  }

  const setUserFromToken = (token) => {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      }).join(''))
      const payload = JSON.parse(jsonPayload)
      state.username = payload.sub || ''
      state.role = payload.role || 'user'
    } catch (e) {
      // ignore
    }
  }

  const clearUser = () => {
    state.username = ''
    state.nickname = ''
    state.avatar = null
    state.role = 'user'
    state.loaded = false
  }

  return {
    state: readonly(state),
    fetchUser,
    setUserFromToken,
    clearUser
  }
}
