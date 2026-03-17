/**
 * 图片上传 Composable
 * 提供图片选择、验证、压缩、Base64编码等功能
 * 支持跨平台：H5、小程序、App
 */

import { ref, computed } from 'vue';
import { toastState, hideToast } from './useToast.js';

let uni = null;
let showToastFn = null;

const initUni = (uniObj) => {
  uni = uniObj;
  showToastFn = (options) => {
    if (uni && uni.showToast) {
      uni.showToast(options);
    } else {
      // 使用自定义 toast
      const message = options.title || '';
      const icon = options.icon || 'none';
      let toastType = 'info';
      if (icon === 'success') toastType = 'success';
      else if (icon === 'error') toastType = 'error';
      
      toastState.title = message;
      toastState.message = '';
      toastState.type = toastType;
      toastState.visible = true;
      
      setTimeout(() => hideToast(), 3000);
    }
  };
};

const defaultShowToast = (options) => {
  if (showToastFn) {
    showToastFn(options);
  } else {
    // 使用自定义 toast
    const message = options.title || '';
    const icon = options.icon || 'none';
    let toastType = 'info';
    if (icon === 'success') toastType = 'success';
    else if (icon === 'error') toastType = 'error';
    
    toastState.title = message;
    toastState.message = '';
    toastState.type = toastType;
    toastState.visible = true;
    
    setTimeout(() => hideToast(), 3000);
  }
};

const IMAGE_CONFIG = {
  ALLOWED_TYPES: ['image/jpeg', 'image/jpg', 'image/png'],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png'],
  MAX_FILE_SIZE: 5 * 1024 * 1024,
  MAX_DIMENSION: 800,
  COMPRESS_QUALITY: 0.7,
  MAX_BASE64_SIZE: 4 * 1024 * 1024
};

export function useImageUpload(options = {}) {
  const config = {
    maxSize: options.maxSize || IMAGE_CONFIG.MAX_FILE_SIZE,
    maxDimension: options.maxDimension || IMAGE_CONFIG.MAX_DIMENSION,
    quality: options.quality || IMAGE_CONFIG.COMPRESS_QUALITY,
    allowedTypes: options.allowedTypes || IMAGE_CONFIG.ALLOWED_TYPES
  };

  const imagePreview = ref('');
  const imageBase64 = ref('');
  const isProcessing = ref(false);
  const uploadProgress = ref(0);
  const errorMessage = ref('');
  const originalSize = ref(0);
  const compressedSize = ref(0);
  const imageChanged = ref(false);

  const hasImage = computed(() => !!imageBase64.value || !!imagePreview.value);
  const compressionRatio = computed(() => {
    if (!originalSize.value || !compressedSize.value) return 0;
    return Math.round((1 - compressedSize.value / originalSize.value) * 100);
  });

  const getMimeType = (filePath) => {
    const extension = filePath.toLowerCase().substring(filePath.lastIndexOf('.'));
    const mimeMap = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png' };
    return mimeMap[extension] || 'image/jpeg';
  };

  const validateImageFormat = (filePath, fileType) => {
    // 优先使用 File 对象的 type 属性验证
    if (fileType) {
      const isValidType = IMAGE_CONFIG.ALLOWED_TYPES.includes(fileType);
      if (!isValidType) {
        errorMessage.value = `不支持的图片格式，仅支持 jpg、jpeg、png 格式`;
        return false;
      }
      return true;
    }
    // 备用：通过文件扩展名验证
    const extension = filePath.toLowerCase().substring(filePath.lastIndexOf('.'));
    const isValidExtension = IMAGE_CONFIG.ALLOWED_EXTENSIONS.includes(extension);
    if (!isValidExtension) {
      errorMessage.value = `不支持的图片格式，仅支持 ${IMAGE_CONFIG.ALLOWED_EXTENSIONS.join('、')} 格式`;
      return false;
    }
    return true;
  };

  const validateImageSize = (size) => {
    if (size > config.maxSize) {
      const maxMB = (config.maxSize / 1024 / 1024).toFixed(1);
      errorMessage.value = `图片大小超过限制，最大允许 ${maxMB}MB`;
      return false;
    }
    return true;
  };

  const compressImageH5 = (filePath, fileType = '') => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;

          if (width > config.maxDimension || height > config.maxDimension) {
            if (width > height) {
              height = Math.round((height * config.maxDimension) / width);
              width = config.maxDimension;
            } else {
              width = Math.round((width * config.maxDimension) / height);
              height = config.maxDimension;
            }
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          // 优先使用原始文件的 MIME 类型，如果没有则从文件扩展名推断
          const mimeType = fileType || getMimeType(filePath);
          const base64WithPrefix = canvas.toDataURL(mimeType, config.quality);
          const base64Data = base64WithPrefix.split(',')[1];
          const base64Size = base64Data.length * 0.75;

          if (base64Size > IMAGE_CONFIG.MAX_BASE64_SIZE) {
            reject(new Error('压缩后图片仍然过大，请选择更小的图片'));
            return;
          }

          resolve({ base64: base64Data, preview: base64WithPrefix, compressedSize: base64Size });
        } catch (error) {
          reject(new Error('图片压缩失败：' + error.message));
        }
      };
      img.onerror = () => reject(new Error('图片加载失败'));
      img.src = filePath;
    });
  };

  const chooseImageH5 = (options = {}) => {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = options.count > 1;
    
    input.onchange = (e) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        const tempFilePaths = [];
        for (let i = 0; i < files.length; i++) {
          tempFilePaths.push(URL.createObjectURL(files[i]));
        }
        resolve({
          tempFilePaths: tempFilePaths,
          tempFiles: Array.from(files)
        });
      } else {
        reject(new Error('取消选择图片'));
      }
    };
    
    input.onerror = () => reject(new Error('选择图片失败'));
    input.click();
  });
};

const chooseAndProcessImage = async (chooseOptions = {}) => {
    errorMessage.value = '';
    uploadProgress.value = 0;

    try {
      isProcessing.value = true;
      uploadProgress.value = 10;

      const chooseResult = await chooseImageH5({
        count: chooseOptions.count || 1,
        sourceType: chooseOptions.sourceType || ['album', 'camera']
      });

      uploadProgress.value = 30;
      const filePath = chooseResult.tempFilePaths[0];
      const file = chooseResult.tempFiles?.[0];
      const fileSize = file?.size || 0;
      const fileType = file?.type || '';

      if (!validateImageFormat(filePath, fileType)) throw new Error(errorMessage.value);
      if (fileSize && !validateImageSize(fileSize)) throw new Error(errorMessage.value);

      originalSize.value = fileSize;
      uploadProgress.value = 50;

      let result;
      // H5 环境使用浏览器原生 API，传入原始 MIME 类型
      result = await compressImageH5(filePath, fileType);

      uploadProgress.value = 90;
      imagePreview.value = result.preview;
      imageBase64.value = result.base64;
      compressedSize.value = result.compressedSize;
      imageChanged.value = true;
      uploadProgress.value = 100;

      showToastFn({ title: '图片已选择', icon: 'success' });

      return { success: true, preview: result.preview, base64: result.base64, originalSize: originalSize.value, compressedSize: result.compressedSize, compressionRatio: compressionRatio.value };
    } catch (error) {
      errorMessage.value = error.message || '图片处理失败';
      showToastFn({ title: errorMessage.value, icon: 'none', duration: 2000 });
      return { success: false, error: errorMessage.value };
    } finally {
      isProcessing.value = false;
    }
  };

  const setExistingImage = (previewUrl) => {
    imagePreview.value = previewUrl || '';
    imageBase64.value = '';
    originalSize.value = 0;
    compressedSize.value = 0;
    errorMessage.value = '';
    imageChanged.value = false;
  };

  const clearImage = () => {
    imagePreview.value = '';
    imageBase64.value = '';
    originalSize.value = 0;
    compressedSize.value = 0;
    errorMessage.value = '';
    uploadProgress.value = 0;
    imageChanged.value = true;
  };

  const reset = () => {
    clearImage();
    isProcessing.value = false;
    imageChanged.value = false;
  };

  const getImageData = () => {
    if (!imageChanged.value) return null;
    return imageBase64.value || '';
  };

  return {
    imagePreview,
    imageBase64,
    isProcessing,
    uploadProgress,
    errorMessage,
    originalSize,
    compressedSize,
    imageChanged,
    hasImage,
    compressionRatio,
    chooseAndProcessImage,
    setExistingImage,
    clearImage,
    reset,
    getImageData,
    validateImageFormat,
    validateImageSize,
    initUni
  };
}

export default useImageUpload;