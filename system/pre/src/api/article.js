import request from '@/utils/request.js'

export const getArticles = (skip = 0, limit = 20) => {
  return request({ url: '/articles', method: 'GET', params: { skip, limit } })
}

export const getArticleById = (articleId) => {
  return request({ url: `/articles/${articleId}`, method: 'GET' })
}

export const createArticle = (data) => {
  return request({ url: '/articles', method: 'POST', data })
}

export const updateArticle = (articleId, data) => {
  return request({ url: `/articles/${articleId}`, method: 'PUT', data })
}

export const deleteArticle = (articleId) => {
  return request({ url: `/articles/${articleId}`, method: 'DELETE' })
}
