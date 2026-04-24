import request from '@/utils/request.js'

// 用户管理
export const getUsers = (params) => {
  return request({ url: '/users', method: 'GET', params })
}

export const createUser = (data) => {
  return request({ url: '/users', method: 'POST', data })
}

export const updateUser = (userId, data) => {
  return request({ url: `/users/${userId}`, method: 'PUT', data })
}

export const deleteUser = (userId) => {
  return request({ url: `/users/${userId}`, method: 'DELETE' })
}

// 文章管理
export { getArticles, createArticle, updateArticle, deleteArticle } from './article.js'
