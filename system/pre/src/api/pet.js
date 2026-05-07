import request from '@/utils/request.js'

export const getCategories = () => {
  return request({ url: '/pets/categories', method: 'GET' })
}

export const getCategoryChildren = (categoryId) => {
  return request({ url: `/pets/categories/${categoryId}/children`, method: 'GET' })
}

export const getBreeds = (categoryId) => {
  return request({ url: '/pets/breeds', method: 'GET', params: { category_id: categoryId } })
}

export const getBreedById = (breedId) => {
  return request({ url: `/pets/breeds/${breedId}`, method: 'GET' })
}

export const getBreedByName = (nameEn) => {
  return request({ url: `/pets/breeds/by-name/${encodeURIComponent(nameEn)}`, method: 'GET' })
}

export const searchBreeds = (keyword) => {
  return request({ url: '/pets/breeds', method: 'GET', params: { keyword } })
}

export const createCategory = (data) => {
  return request({ url: '/pets/categories', method: 'POST', data })
}

export const createBreed = (data) => {
  return request({ url: '/pets/breeds', method: 'POST', data })
}

export const updateBreed = (breedId, data) => {
  return request({ url: `/pets/breeds/${breedId}`, method: 'PUT', data })
}
