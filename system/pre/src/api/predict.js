import { BASE_URL } from '@/utils/request.js'

export const predictImage = (filePath, token) => {
  return new Promise((resolve, reject) => {
    const uni = window.uni || uni
    uni.uploadFile({
      url: `${BASE_URL}/predict`,
      filePath: filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(res.data)
            resolve(response)
          } catch (e) {
            reject(new Error('解析响应失败'))
          }
        } else {
          reject(new Error('识别失败'))
        }
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}
