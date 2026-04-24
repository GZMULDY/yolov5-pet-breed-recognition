import request from '@/utils/request.js'

export const getCategories = () => {
  return request({ url: '/categories', method: 'GET' })
}

export const getCategoryChildren = (categoryId) => {
  return request({ url: `/categories/${categoryId}/children`, method: 'GET' })
}

export const getBreeds = (categoryId) => {
  return request({ url: '/breeds', method: 'GET', params: { category_id: categoryId } })
}

export const getBreedById = (breedId) => {
  return request({ url: `/breeds/${breedId}`, method: 'GET' })
}

export const getBreedByName = (nameEn) => {
  return request({ url: `/breeds/by-name/${encodeURIComponent(nameEn)}`, method: 'GET' })
}

export const searchBreeds = (keyword) => {
  return request({ url: '/breeds', method: 'GET', params: { keyword } })
}

export const createCategory = (data) => {
  return request({ url: '/categories', method: 'POST', data })
}

export const createBreed = (data) => {
  return request({ url: '/breeds', method: 'POST', data })
}

export const updateBreed = (breedId, data) => {
  return request({ url: `/breeds/${breedId}`, method: 'PUT', data })
}
