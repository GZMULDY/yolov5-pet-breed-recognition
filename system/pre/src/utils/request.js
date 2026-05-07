/**
 * HTTP 请求封装模块
 * 统一处理所有 API 请求，包括：
 * - 基础 URL 配置
 * - 请求头设置（包含 Token 认证）
 * - 响应状态处理（401 登录过期等）
 * - 统一响应格式解析
 * - 错误提示
 */
import axios from 'axios'
import { toastState, hideToast } from '../composables/useToast.js'

// 全局 toast 函数
const globalShowToast = (options) => {
  const message = typeof options === 'string' ? options : (options.title || options.message || '')
  const icon = typeof options === 'object' ? options.icon : 'none'
  
  let toastType = 'info'
  if (icon === 'success') toastType = 'success'
  else if (icon === 'error') toastType = 'error'
  
  toastState.title = message
  toastState.message = ''
  toastState.type = toastType
  toastState.visible = true
  
  setTimeout(() => {
    hideToast()
  }, 3000)
}

export const setGlobalShowToast = (fn) => {
  // 保留以保持 API 兼容
}

// 后端 API 基础地址
export const BASE_URL = 'http://127.0.0.1:8000/api/v1'

// 响应状态码
const RESPONSE_CODE = {
  SUCCESS: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500
}

/**
 * 创建 axios 实例
 * 可以配置默认超时时间、请求头等
 */
const instance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 请求拦截器
 * 在每次请求前添加 Token 到请求头
 */
instance.interceptors.request.use(
  (config) => {
    // 从本地存储获取 Token
    const token = localStorage.getItem('token')
    
    // 如果存在 Token，添加到请求头
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    // 请求错误处理
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 * 统一处理响应错误和解析统一响应格式
 */
instance.interceptors.response.use(
  (response) => {
    // 2xx 状态码范围内的响应
    const res = response.data
    
    // 检查是否使用统一响应格式
    if (res && res.code !== undefined) {
      // 统一响应格式
      if (res.code === RESPONSE_CODE.SUCCESS || res.code === RESPONSE_CODE.CREATED) {
        // 成功响应，返回 data 字段
        return res
      } else {
        // 业务错误
        const errorMsg = res.message || '请求失败'
        console.error(`[API Error] ${errorMsg}`, res)
        
        // 401 未授权（登录过期）
        if (res.code === RESPONSE_CODE.UNAUTHORIZED) {
          localStorage.removeItem('token')
          window.location.href = '/#/login'
        }
        
        return Promise.reject(new Error(errorMsg))
      }
    }
    
    // 非统一响应格式，直接返回
    return res
  },
  (error) => {
    // 处理错误响应
    if (error.response) {
      // 获取后端返回的错误信息
      let errorMsg = '请求失败'
      
      if (error.response.data) {
        // 尝试从统一响应格式获取错误信息
        if (error.response.data.message) {
          errorMsg = error.response.data.message
        } else if (error.response.data.detail) {
          errorMsg = error.response.data.detail
        }
      }
      
      // 优先从响应体中获取后端返回的错误信息
      const responseData = error.response.data
      if (responseData && responseData.detail) {
        // 后端返回的详细错误信息（如 "验证码错误，请重新输入"）
        errorMsg = responseData.detail
      } else if (responseData && responseData.message) {
        errorMsg = responseData.message
      } else if (typeof responseData === 'string') {
        errorMsg = responseData
      }
      
      // 401 未授权（登录过期）
      if (error.response.status === 401) {
        // 清除本地存储的 token
        localStorage.removeItem('token')
        // 提示用户登录已过期
        errorMsg = '登录已过期，请重新登录'
        // 跳转到登录页
        window.location.href = '/#/login'
      } 
      // 403 权限不足
      else if (error.response.status === 403) {
        errorMsg = errorMsg || '权限不足'
      }
      // 404 资源不存在
      else if (error.response.status === 404) {
        errorMsg = errorMsg || '资源不存在'
      }
      // 500 服务器错误
      else if (error.response.status === 500) {
        errorMsg = errorMsg || '服务器内部错误'
      }
      // 400 客户端错误（参数错误等）
      else if (error.response.status === 400) {
        errorMsg = errorMsg || '请求参数错误'
      }
      // 422 参数验证失败
      else if (error.response.status === 422) {
        errorMsg = errorMsg || '参数验证失败'
      }
      
      console.error(`[API Error] ${errorMsg}`, error.response)
      globalShowToast({ title: errorMsg, icon: 'none' })
    } else {
      // 网络错误
      globalShowToast({ title: '网络请求失败，请检查网络连接', icon: 'none' })
    }
    
    return Promise.reject(error)
  }
)

/**
 * 统一请求方法
 * @param {Object} options - 请求配置项
 * @param {string} options.url - 请求路径
 * @param {string} [options.method='GET'] - 请求方法
 * @param {Object} [options.data={}] - 请求数据
 * @param {Object} [options.header={}] - 自定义请求头
 * @param {Object} [options.params={}] - URL 查询参数
 * @returns {Promise} 返回 Promise 对象
 */
const request = (options) => {
  return instance({
    url: options.url,
    method: options.method || 'GET',
    data: options.data || {},
    params: options.params || {},
    headers: options.header || {}
  })
}

// 导出统一响应码常量
export { RESPONSE_CODE }

// 导出默认请求方法
export default request