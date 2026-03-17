/**
 * 认证 API 模块
 * 提供用户登录、注册、验证码等接口
 */
import request from '@/utils/request';

/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @param {string} captchaKey - 验证码key
 * @param {string} captchaCode - 验证码
 * @returns {Promise} 返回包含 token 和用户信息的 Promise
 */
export function login(username, password, captchaKey = null, captchaCode = null) {
  const data = {
    username,
    password
  }
  
  // 如果有验证码，添加到请求参数
  if (captchaKey && captchaCode) {
    data.captcha_key = captchaKey
    data.captcha_code = captchaCode
  }
  
  return request({
    url: '/login', 
    method: 'POST',
    data
  });
}

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @param {string} email - 邮箱
 * @returns {Promise} 返回注册结果的 Promise
 */
export function register(username, password, email) {
  return request({
    url: '/register',
    method: 'POST',
    data: {
      username,
      password,
      email,
      role: 'user' 
    }
  });
}

/**
 * 发送邮箱验证码
 * @param {string} email - 邮箱地址
 * @returns {Promise} 返回发送结果的 Promise
 */
export function sendEmailCode(email) {
  return request({
    url: '/send-email-code',
    method: 'POST',
    data: {
      email: [email] // Backend expects a list
    }
  });
}

/**
 * 验证邮箱验证码
 * @param {string} email - 邮箱地址
 * @param {string} code - 验证码
 * @returns {Promise} 返回验证结果的 Promise
 */
export function verifyEmailCode(email, code) {
  return request({
    url: '/verify-email-code',
    method: 'POST',
    data: {
      email,
      code
    }
  });
}

/**
 * 获取当前用户信息
 * @returns {Promise} 返回用户信息的 Promise
 */
export function getCurrentUser() {
  return request({
    url: '/me',
    method: 'GET'
  });
}

/**
 * 获取用户列表（管理员）
 * @param {number} skip - 跳过条数
 * @param {number} limit - 限制条数
 * @returns {Promise} 返回用户列表的 Promise
 */
export function getUsers(skip = 0, limit = 100) {
  return request({
    url: '/users',
    method: 'GET',
    params: { skip, limit }
  });
}

/**
 * 创建用户（管理员）
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @param {string} email - 邮箱
 * @param {string} role - 角色
 * @returns {Promise} 返回创建结果的 Promise
 */
export function createUser(username, password, email, role = 'user') {
  return request({
    url: '/users',
    method: 'POST',
    data: { username, password, email, role }
  });
}

/**
 * 更新用户（管理员）
 * @param {number} userId - 用户ID
 * @param {Object} data - 更新数据
 * @returns {Promise} 返回更新结果的 Promise
 */
export function updateUser(userId, data) {
  return request({
    url: `/users/${userId}`,
    method: 'PUT',
    data
  });
}

/**
 * 删除用户（管理员）
 * @param {number} userId - 用户ID
 * @returns {Promise} 返回删除结果的 Promise
 */
export function deleteUser(userId) {
  return request({
    url: `/users/${userId}`,
    method: 'DELETE'
  });
}

/**
 * 获取当前用户个人信息
 * @returns {Promise} 返回用户个人信息的 Promise
 */
export function getProfile() {
  return request({
    url: '/profile',
    method: 'GET'
  });
}

/**
 * 更新当前用户个人信息
 * @param {Object} data - 更新数据 { nickname, avatar }
 * @returns {Promise} 返回更新结果的 Promise
 */
export function updateProfile(data) {
  return request({
    url: '/profile',
    method: 'PUT',
    data
  });
}