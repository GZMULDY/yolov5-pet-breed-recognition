/**
 * uni-app API 适配器
 * 将 uni-app 的 API 适配到标准 Vue/H5 环境
 * 这样可以无需修改页面代码即可运行
 */

import { toastState, hideToast as hideGlobalToast } from '../composables/useToast.js';

// 存储相关
const storage = {
  getItem: (key) => localStorage.getItem(key),
  setItem: (key, value) => localStorage.setItem(key, value),
  removeItem: (key) => localStorage.removeItem(key),
  clear: () => localStorage.clear()
}

// 路由跳转适配 - 使用 Vue Router
let vueRouter = null

export const setRouter = (router) => {
  vueRouter = router
}

const convertUrl = (url) => {
  // 将 /pages/dashboard/dashboard 转换为 /dashboard
  // 将 /pages/admin/users 转换为 /admin/users
  // 将 /pages/pets/encyclopedia 转换为 /pets/encyclopedia
  // 将 /pages/pets/detail 转换为 /pets/detail
  // 将 /pages/pet/recognize 转换为 /pet/recognize
  // 将 /pages/articles/list 转换为 /articles/list
  // 将 /pages/articles/detail 转换为 /articles/detail
  let converted = url.replace('/pages', '')
  // 如果转换后是 /dashboard/dashboard，改为 /dashboard
  if (converted.match(/^\/dashboard\/dashboard$/)) {
    converted = '/dashboard'
  }
  return converted
}

const navigateTo = (options) => {
  const url = convertUrl(options.url)
  if (vueRouter) {
    vueRouter.push(url)
  } else {
    window.location.href = url
  }
}

const reLaunch = (options) => {
  const url = convertUrl(options.url)
  if (vueRouter) {
    vueRouter.push(url)
  } else {
    window.location.href = url
  }
}

const switchTab = (options) => {
  const url = convertUrl(options.url)
  if (vueRouter) {
    vueRouter.push(url)
  } else {
    window.location.href = url
  }
}

const redirectTo = (options) => {
  const url = convertUrl(options.url)
  if (vueRouter) {
    vueRouter.replace(url)
  } else {
    window.location.replace(url)
  }
}

const navigateBack = () => {
  if (vueRouter) {
    vueRouter.back()
  } else {
    window.history.back()
  }
}

// 提示信息适配 - 使用全局自定义弹窗组件
const showToast = (options) => {
  const message = typeof options === 'string' ? options : (options.title || '')
  const icon = typeof options === 'object' ? options.icon : 'none'
  const duration = typeof options === 'object' ? (options.duration || 3000) : 3000
  
  // 根据 icon 类型确定 toast 类型
  let toastType = 'info'
  if (icon === 'success') {
    toastType = 'success'
  } else if (icon === 'error') {
    toastType = 'error'
  } else if (icon === 'loading') {
    toastType = 'info'
  }
  
  // 使用全局 toast 状态
  toastState.title = message
  toastState.message = ''
  toastState.type = toastType
  toastState.duration = duration
  toastState.visible = true
  
  // 自动隐藏
  if (duration > 0) {
    setTimeout(() => {
      hideGlobalToast()
    }, duration)
  }
}

// 对话框适配 - 精美的自定义弹窗
const showModal = (options) => {
  // 创建遮罩层
  const overlay = document.createElement('div')
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    z-index: 9998;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: modalFadeIn 0.2s ease-out;
  `
  
  // 创建弹窗主体
  const modal = document.createElement('div')
  modal.style.cssText = `
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 24px;
    max-width: 300px;
    width: 85%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
    animation: modalPopIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif;
  `
  
  // 标题
  const title = document.createElement('div')
  title.textContent = options.title || '提示'
  title.style.cssText = `
    font-size: 18px;
    font-weight: 600;
    color: #333;
    text-align: center;
    margin-bottom: 12px;
  `
  
  // 内容
  const content = document.createElement('div')
  content.textContent = options.content || ''
  content.style.cssText = `
    font-size: 15px;
    color: #666;
    text-align: center;
    line-height: 1.5;
    margin-bottom: 24px;
  `
  
  // 按钮容器
  const btnContainer = document.createElement('div')
  btnContainer.style.cssText = `
    display: flex;
    gap: 12px;
    justify-content: center;
  `
  
  // 取消按钮
  const cancelBtn = document.createElement('button')
  cancelBtn.textContent = options.cancelText || '取消'
  cancelBtn.style.cssText = `
    flex: 1;
    padding: 12px 20px;
    border: none;
    border-radius: 12px;
    background: #f5f5f5;
    color: #666;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  `
  cancelBtn.onmouseover = () => { cancelBtn.style.background = '#e8e8e8' }
  cancelBtn.onmouseout = () => { cancelBtn.style.background = '#f5f5f5' }
  
  // 确认按钮
  const confirmBtn = document.createElement('button')
  confirmBtn.textContent = options.confirmText || '确定'
  confirmBtn.style.cssText = `
    flex: 1;
    padding: 12px 20px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    color: white;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 4px 12px rgba(255, 154, 158, 0.3);
  `
  confirmBtn.onmouseover = () => { confirmBtn.style.transform = 'scale(1.02)' }
  confirmBtn.onmouseout = () => { confirmBtn.style.transform = 'scale(1)' }
  
  // 添加按钮点击事件
  const handleConfirm = () => {
    modal.style.animation = 'modalPopOut 0.2s ease-out forwards'
    overlay.style.animation = 'modalFadeOut 0.2s ease-out forwards'
    setTimeout(() => {
      if (overlay.parentNode) {
        document.body.removeChild(overlay)
      }
      if (options.success) {
        options.success({ confirm: true, cancel: false })
      }
    }, 200)
  }
  
  const handleCancel = () => {
    modal.style.animation = 'modalPopOut 0.2s ease-out forwards'
    overlay.style.animation = 'modalFadeOut 0.2s ease-out forwards'
    setTimeout(() => {
      if (overlay.parentNode) {
        document.body.removeChild(overlay)
      }
      if (options.success) {
        options.success({ confirm: false, cancel: true })
      }
    }, 200)
  }
  
  confirmBtn.onclick = handleConfirm
  cancelBtn.onclick = handleCancel
  overlay.onclick = (e) => {
    if (e.target === overlay) handleCancel()
  }
  
  btnContainer.appendChild(cancelBtn)
  btnContainer.appendChild(confirmBtn)
  modal.appendChild(title)
  modal.appendChild(content)
  modal.appendChild(btnContainer)
  overlay.appendChild(modal)
  document.body.appendChild(overlay)
  
  // 添加动画样式
  const style = document.createElement('style')
  style.textContent = `
    @keyframes modalFadeIn {
      0% { opacity: 0; }
      100% { opacity: 1; }
    }
    @keyframes modalFadeOut {
      0% { opacity: 1; }
      100% { opacity: 0; }
    }
    @keyframes modalPopIn {
      0% { opacity: 0; transform: scale(0.8) translateY(20px); }
      100% { opacity: 1; transform: scale(1) translateY(0); }
    }
    @keyframes modalPopOut {
      0% { opacity: 1; transform: scale(1) translateY(0); }
      100% { opacity: 0; transform: scale(0.8) translateY(20px); }
    }
  `
  document.head.appendChild(style)
}

// 操作菜单适配 - 精美的底部弹出菜单
const showActionSheet = (options) => {
  const itemList = options.itemList || []
  
  // 创建遮罩层
  const overlay = document.createElement('div')
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    z-index: 9998;
    animation: actionSheetFadeIn 0.2s ease-out;
  `
  
  // 创建底部菜单面板
  const sheet = document.createElement('div')
  sheet.style.cssText = `
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px 20px 0 0;
    padding: 16px;
    padding-bottom: calc(16px + env(safe-area-inset-bottom));
    box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.15);
    animation: actionSheetSlideIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif;
  `
  
  // 取消按钮
  const cancelBtn = document.createElement('div')
  cancelBtn.textContent = options.cancelText || '取消'
  cancelBtn.style.cssText = `
    width: 100%;
    padding: 14px;
    text-align: center;
    font-size: 17px;
    color: #666;
    background: #f5f5f5;
    border-radius: 14px;
    margin-top: 8px;
    cursor: pointer;
    transition: background 0.2s;
  `
  cancelBtn.onmouseover = () => { cancelBtn.style.background = '#e8e8e8' }
  cancelBtn.onmouseout = () => { cancelBtn.style.background = '#f5f5f5' }
  
  // 创建菜单项
  const itemsContainer = document.createElement('div')
  itemsContainer.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
  `
  
  itemList.forEach((item, index) => {
    const itemBtn = document.createElement('div')
    itemBtn.textContent = item
    itemBtn.style.cssText = `
      width: 100%;
      padding: 14px;
      text-align: center;
      font-size: 17px;
      color: #333;
      background: white;
      border-radius: 14px;
      cursor: pointer;
      transition: all 0.2s;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    `
    itemBtn.onmouseover = () => { 
      itemBtn.style.background = '#f8f8f8'
      itemBtn.style.transform = 'scale(0.98)'
    }
    itemBtn.onmouseout = () => { 
      itemBtn.style.background = 'white'
      itemBtn.style.transform = 'scale(1)'
    }
    itemBtn.onclick = () => {
      sheet.style.animation = 'actionSheetSlideOut 0.2s ease-out forwards'
      overlay.style.animation = 'actionSheetFadeOut 0.2s ease-out forwards'
      setTimeout(() => {
        if (overlay.parentNode) {
          document.body.removeChild(overlay)
        }
        if (options.success) {
          options.success({ tapIndex: index })
        }
      }, 200)
    }
    itemsContainer.appendChild(itemBtn)
  })
  
  // 取消按钮点击事件
  const handleCancel = () => {
    sheet.style.animation = 'actionSheetSlideOut 0.2s ease-out forwards'
    overlay.style.animation = 'actionSheetFadeOut 0.2s ease-out forwards'
    setTimeout(() => {
      if (overlay.parentNode) {
        document.body.removeChild(overlay)
      }
      if (options.fail) {
        options.fail({ errMsg: 'cancel' })
      }
    }, 200)
  }
  
  cancelBtn.onclick = handleCancel
  overlay.onclick = handleCancel
  
  sheet.appendChild(itemsContainer)
  sheet.appendChild(cancelBtn)
  overlay.appendChild(sheet)
  document.body.appendChild(overlay)
  
  // 添加动画样式
  const style = document.createElement('style')
  style.textContent = `
    @keyframes actionSheetFadeIn {
      0% { opacity: 0; }
      100% { opacity: 1; }
    }
    @keyframes actionSheetFadeOut {
      0% { opacity: 1; }
      100% { opacity: 0; }
    }
    @keyframes actionSheetSlideIn {
      0% { transform: translateY(100%); }
      100% { transform: translateY(0); }
    }
    @keyframes actionSheetSlideOut {
      0% { transform: translateY(0); }
      100% { transform: translateY(100%); }
    }
  `
  document.head.appendChild(style)
}

// 网络请求适配
const request = (options) => {
  const headers = {
    'Content-Type': 'application/json',
    ...options.header
  }
  
  return new Promise((resolve, reject) => {
    fetch(options.url, {
      method: options.method || 'GET',
      headers: headers,
      body: options.data ? JSON.stringify(options.data) : undefined
    }).then(res => {
      const contentType = res.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return res.json().then(data => {
          const result = {
            statusCode: res.status,
            data: data
          }
          if (options.success) {
            options.success(result)
          }
          resolve(result)
        }).catch(err => {
          const result = {
            statusCode: res.status,
            data: { error: err.message }
          }
          if (options.fail) {
            options.fail({ errMsg: err.message, statusCode: res.status })
          }
          reject(err)
        })
      } else {
        return res.text().then(text => {
          const result = {
            statusCode: res.status,
            data: text
          }
          if (options.success) {
            options.success(result)
          }
          resolve(result)
        }).catch(err => {
          if (options.fail) {
            options.fail({ errMsg: err.message, statusCode: res.status })
          }
          reject(err)
        })
      }
    }).catch(err => {
      console.error('Request failed:', err)
      if (options.fail) {
        options.fail({ errMsg: err.message, statusCode: 500 })
      }
      reject(err)
    })
  })
}

// 导出模拟的 uni 对象
const uni = {
  // 存储 API
  getStorageSync: (key) => storage.getItem(key),
  setStorageSync: (key, value) => storage.setItem(key, value),
  removeStorageSync: (key) => storage.removeItem(key),
  clearStorageSync: () => storage.clear(),
  
  // 路由 API
  navigateTo: (options) => navigateTo(options),
  reLaunch: (options) => reLaunch(options),
  switchTab: (options) => switchTab(options),
  redirectTo: (options) => redirectTo(options),
  navigateBack: () => navigateBack(),
  
  // 提示 API
  showToast: (options) => showToast(options),
  showLoading: (options) => showToast(options),
  hideLoading: () => {},
  
  // 对话框 API
  showModal: (options) => showModal(options),
  showActionSheet: (options) => showActionSheet(options),
  
  // 文件选择 API
  chooseImage: (options) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.multiple = options.count > 1
    
    input.onchange = (e) => {
      const files = e.target.files
      if (files && files.length > 0) {
        const tempFilePaths = []
        for (let i = 0; i < files.length; i++) {
          tempFilePaths.push(URL.createObjectURL(files[i]))
        }
        if (options.success) {
          options.success({
            tempFilePaths: tempFilePaths,
            tempFiles: Array.from(files)
          })
        }
      }
    }
    
    input.click()
  },
  
  chooseVideo: (options) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'video/*'
    
    input.onchange = (e) => {
      const file = e.target.files[0]
      if (file) {
        if (options.success) {
          options.success({
            tempFilePath: URL.createObjectURL(file),
            size: file.size,
            name: file.name
          })
        }
      }
    }
    
    input.click()
  },
  
  uploadFile: (options) => {
    const { url, filePath, name, header, success, fail } = options

    const doUpload = (file) => {
      const formData = new FormData()
      formData.append(name || 'file', file)

      return fetch(url, {
        method: 'POST',
        headers: { ...header },
        body: formData
      })
    }

    const handleResponse = (res) => {
      return res.text().then(text => {
        return { statusCode: res.status, data: text, errMsg: 'uploadFile:ok' }
      })
    }

    // filePath 可能是 File 对象或 blob URL 字符串
    if (filePath instanceof File) {
      doUpload(filePath)
        .then(handleResponse)
        .then(result => {
          if (result.statusCode >= 200 && result.statusCode < 300) {
            if (success) success(result)
          } else {
            if (fail) fail(result)
          }
        })
        .catch(err => {
          if (fail) fail({ errMsg: err.message || '网络请求失败', statusCode: 500 })
        })
    } else {
      // blob URL 字符串，先 fetch 获取 blob 再上传
      fetch(filePath)
        .then(res => res.blob())
        .then(blob => {
          let extension = 'jpg'
          if (blob.type.includes('png')) extension = 'png'
          else if (blob.type.includes('gif')) extension = 'gif'
          else if (blob.type.includes('webp')) extension = 'webp'
          else if (blob.type.includes('jpeg') || blob.type.includes('jpg')) extension = 'jpg'
          else if (blob.type.includes('mp4')) extension = 'mp4'
          else if (blob.type.includes('webm')) extension = 'webm'

          const file = new File([blob], `file.${extension}`, { type: blob.type })
          return doUpload(file)
        })
        .then(handleResponse)
        .then(result => {
          if (result.statusCode >= 200 && result.statusCode < 300) {
            if (success) success(result)
          } else {
            if (fail) fail(result)
          }
        })
        .catch(err => {
          if (fail) fail({ errMsg: err.message || '网络请求失败', statusCode: 500 })
        })
    }
  },
  
  // 网络请求 API
  request: (options) => request(options)
}

// 导出
export { uni }
export default uni