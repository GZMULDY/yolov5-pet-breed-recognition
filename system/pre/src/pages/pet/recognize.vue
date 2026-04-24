<template>
  <div class="page-container aurora-bg">
    <div class="content-wrapper">
      <div class="header">
        <div class="title">
          <span class="emoji">📸</span>
          <span class="text-gradient">宠物识别</span>
        </div>
      </div>

      <div class="upload-section glass-effect">
        <!-- 未选择文件时 -->
        <div class="upload-area" @click="showActionSheet" v-if="!filePath">
          <span class="upload-icon">📤</span>
          <p class="upload-text">点击上传图片或视频</p>
        </div>
        
        <!-- 预览区域 -->
        <div class="preview-area" v-else>
          <!-- 图片预览 -->
          <img v-if="fileType === 'image'" :src="filePath" class="preview-img" alt="预览图" />
          <!-- 视频预览 -->
          <video v-else :src="filePath" class="preview-video" controls></video>
          
          <div class="preview-actions">
            <button class="action-btn re-upload" @click="reset">🔄 重选</button>
            <button class="action-btn analyze" @click="analyzeFile" :disabled="loading">
              {{ loading ? '识别中...' : '🔍 开始识别' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Result Section -->
      <div v-if="result" class="result-section glass-effect slide-up">
        <div class="result-header">
          <h3>识别结果</h3>
        </div>
        
        <!-- 结果展示：图片或视频 -->
        <div class="result-media-box">
          <img 
            v-if="result.type === 'image'" 
            :src="result.image_url" 
            class="result-img" 
            alt="识别结果"
            @click="previewResult"
          />
          <video 
            v-else 
            :src="result.image_url" 
            class="result-video" 
            controls
          ></video>
        </div>

        <div class="result-list">
          <!-- 图片结果详情 -->
          <template v-if="result.type === 'image'">
            <div v-for="(item, index) in result.results" :key="index" class="result-item">
              <div class="result-label">
                <span class="badge">{{ item.label }}</span>
              </div>
              <div class="result-conf">
                置信度: {{ (item.confidence * 100).toFixed(1) }}%
              </div>
            </div>
          </template>
          
          <!-- 视频结果摘要 -->
          <template v-else>
            <div class="video-summary-title">视频中出现的宠物统计：</div>
            <div v-for="(item, index) in result.results" :key="index" class="result-item">
              <div class="result-label">
                <span class="badge">{{ item.label }}</span>
              </div>
              <div class="result-conf">
                出现帧数: {{ item.count }}
              </div>
            </div>
          </template>
          
          <div v-if="!result.results || result.results.length === 0" class="no-result">
            未检测到常见宠物 🐶🐱
          </div>
        </div>
      </div>

      <!-- 品种知识展示区域 -->
      <div v-if="breedKnowledge" class="knowledge-section glass-effect slide-up">
        <div class="knowledge-header">
          <h3>📖 品种知识</h3>
          <span class="breed-name-tag">{{ breedKnowledge.name }}</span>
        </div>
        
        <div class="knowledge-content">
          <!-- 品种图片 -->
          <div v-if="breedKnowledge.image" class="knowledge-image-box">
            <img :src="breedKnowledge.image" class="knowledge-image" alt="品种图片" />
          </div>
          
          <!-- 基本信息 -->
          <div class="info-grid">
            <div class="info-item" v-if="breedKnowledge.origin">
              <span class="info-icon">🌍</span>
              <div class="info-content">
                <span class="info-label">原产地</span>
                <span class="info-value">{{ breedKnowledge.origin }}</span>
              </div>
            </div>
            <div class="info-item" v-if="breedKnowledge.size">
              <span class="info-icon">📏</span>
              <div class="info-content">
                <span class="info-label">体型</span>
                <span class="info-value">{{ breedKnowledge.size }}</span>
              </div>
            </div>
            <div class="info-item" v-if="breedKnowledge.lifespan">
              <span class="info-icon">⏳</span>
              <div class="info-content">
                <span class="info-label">寿命</span>
                <span class="info-value">{{ breedKnowledge.lifespan }}</span>
              </div>
            </div>
            <div class="info-item" v-if="breedKnowledge.exercise_needs">
              <span class="info-icon">🏃</span>
              <div class="info-content">
                <span class="info-label">运动需求</span>
                <span class="info-value">{{ breedKnowledge.exercise_needs }}</span>
              </div>
            </div>
          </div>
          
          <!-- 详细描述 -->
          <div class="knowledge-detail" v-if="breedKnowledge.description">
            <h4 class="detail-title">📝 品种介绍</h4>
            <p class="detail-text">{{ breedKnowledge.description }}</p>
          </div>
          
          <div class="knowledge-detail" v-if="breedKnowledge.personality">
            <h4 class="detail-title">💝 性格特点</h4>
            <p class="detail-text">{{ breedKnowledge.personality }}</p>
          </div>
          
          <div class="knowledge-detail" v-if="breedKnowledge.care_tips">
            <h4 class="detail-title">🛁 护理建议</h4>
            <p class="detail-text">{{ breedKnowledge.care_tips }}</p>
          </div>
          
          <div class="knowledge-detail" v-if="breedKnowledge.diet_needs">
            <h4 class="detail-title">🍖 饮食需求</h4>
            <p class="detail-text">{{ breedKnowledge.diet_needs }}</p>
          </div>
          
          <div class="knowledge-detail" v-if="breedKnowledge.health_issues">
            <h4 class="detail-title">🏥 健康注意</h4>
            <p class="detail-text">{{ breedKnowledge.health_issues }}</p>
          </div>
        </div>
      </div>
      
      <!-- 知识加载中提示 -->
      <div v-if="loadingKnowledge" class="knowledge-loading glass-effect slide-up">
        <span class="loading-icon">📚</span>
        <span class="loading-text">正在加载品种知识...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { uni } from '@/utils/uni-adapter.js';

const filePath = ref('');
const fileType = ref('image'); // 'image' or 'video'
const loading = ref(false);
const result = ref(null);
const breedKnowledge = ref(null);  // 存储品种知识数据
const loadingKnowledge = ref(false);  // 知识加载状态

import { BASE_URL } from '@/utils/request.js';
const API_URL = BASE_URL;

/**
 * 根据识别结果中的品种英文名称获取品种详细知识
 * @param {string} nameEn - 品种英文名称
 * @returns {Promise<Object|null>} 品种知识数据或null
 */
const fetchBreedKnowledge = async (nameEn) => {
  if (!nameEn) return null;
  
  const requestUrl = `${API_URL}/breeds/by-name/${encodeURIComponent(nameEn)}`;
  
  try {
    const response = await new Promise((resolve, reject) => {
      uni.request({
        url: requestUrl,
        method: 'GET',
        header: {
          'Content-Type': 'application/json'
        },
        success: (res) => resolve(res),
        fail: (err) => reject(err)
      });
    });
    
    if (response.statusCode === 200 && response.data) {
      const responseData = response.data;
      if (responseData.code === '200' && responseData.data) {
        return responseData.data;
      } else if (responseData.code === '404') {
        // 品种不存在
      }
    }
    return null;
  } catch (error) {
    console.error('获取品种知识失败:', error);
    return null;
  }
};

/**
 * 处理识别结果，获取所有识别到的品种的知识
 * @param {Object} resultData - 识别结果数据
 */
const processBreedKnowledge = async (resultData) => {
  breedKnowledge.value = null;
  
  if (!resultData || !resultData.results || resultData.results.length === 0) {
    loadingKnowledge.value = false;
    return;
  }
  
  let targetBreed = null;
  
  if (resultData.type === 'image') {
    targetBreed = resultData.results.reduce((max, item) => 
      (item.confidence > (max?.confidence || 0)) ? item : max, null);
  } else {
    targetBreed = resultData.results.reduce((max, item) => 
      (item.count > (max?.count || 0)) ? item : max, null);
  }
  
  if (targetBreed && targetBreed.label) {
    loadingKnowledge.value = true;
    try {
      const knowledge = await fetchBreedKnowledge(targetBreed.label);
      breedKnowledge.value = knowledge;
    } catch (error) {
      console.error('processBreedKnowledge 错误:', error);
    } finally {
      loadingKnowledge.value = false;
    }
  } else {
    loadingKnowledge.value = false;
  }
};

// 监听识别结果变化，自动获取品种知识
watch(result, (newResult) => {
  if (newResult) {
    processBreedKnowledge(newResult);
  } else {
    breedKnowledge.value = null;
    loadingKnowledge.value = false;
  }
}, { deep: true });

const showActionSheet = () => {
  uni.showActionSheet({
    itemList: ['拍摄照片', '从相册选择照片', '拍摄视频', '从相册选择视频'],
    success: (res) => {
      switch (res.tapIndex) {
        case 0: chooseImage('camera'); break;
        case 1: chooseImage('album'); break;
        case 2: chooseVideo('camera'); break;
        case 3: chooseVideo('album'); break;
      }
    }
  });
};

const chooseImage = (sourceType) => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: [sourceType],
    success: (res) => {
      filePath.value = res.tempFilePaths[0];
      fileType.value = 'image';
      result.value = null;
    }
  });
};

const chooseVideo = (sourceType) => {
  uni.chooseVideo({
    sourceType: [sourceType],
    compressed: true,
    success: (res) => {
      filePath.value = res.tempFilePath;
      fileType.value = 'video';
      result.value = null;
    }
  });
};

const reset = () => {
  filePath.value = '';
  result.value = null;
};

const analyzeFile = async () => {
  if (!filePath.value) return;
  
  loading.value = true;
  const token = uni.getStorageSync('token');
  
  uni.uploadFile({
    url: `${API_URL}/predict`,
    filePath: filePath.value,
    name: 'file',
    header: {
      'Authorization': `Bearer ${token}`
    },
    success: (uploadFileRes) => {
      loading.value = false;
      if (uploadFileRes.statusCode === 200) {
        try {
          const response = JSON.parse(uploadFileRes.data);
          // 后端返回格式是 { code, message, data: { type, results, image_url }, timestamp }
          // 需要取 response.data 来获取实际的识别结果
          if (response.data) {
            result.value = response.data;
            uni.showToast({ title: '识别完成 ✨', icon: 'success' });
            // 直接调用品种知识获取，不依赖 watch
            processBreedKnowledge(response.data);
          } else {
            uni.showToast({ title: '识别结果为空', icon: 'none' });
          }
        } catch (e) {
          console.error('解析响应失败:', e);
          uni.showToast({ title: '解析失败', icon: 'none' });
        }
      } else {
        uni.showToast({ title: '识别失败 😭', icon: 'none' });
      }
    },
    fail: (err) => {
      loading.value = false;
      // 错误已在 request.js 中统一处理
      console.error(err);
    }
  });
};

const previewResult = () => {
  if (result.value && result.value.type === 'image' && result.value.image_url) {
    uni.previewImage({
      urls: [result.value.image_url]
    });
  }
};
</script>

<style scoped>
/* Inherit Aurora Background */
.aurora-bg {
  background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #ffd1ff, #a18cd1);
  background-size: 400% 400%;
  animation: aurora 15s ease infinite;
}

@keyframes aurora {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.page-container {
  padding: 20px;
  min-height: 100vh;
  font-family: 'Nunito', 'Rounded Mplus 1c', 'PingFang SC', sans-serif;
  box-sizing: border-box;
}

.content-wrapper { max-width: 600px; margin: 0 auto; }

.header {
  margin-bottom: 30px;
  display: flex;
  align-items: center;
}

.title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.text-gradient {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(45deg, #ff6b6b, #ff8e53);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.emoji { font-size: 28px; }

.glass-effect {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05);
  border-radius: 24px;
  padding: 20px;
}

/* Upload Section */
.upload-area {
  height: 250px;
  border: 3px dashed rgba(255, 154, 158, 0.5);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(255, 255, 255, 0.5);
}

.upload-area:active {
  background: rgba(255, 255, 255, 0.8);
  border-color: #ff9a9e;
}

.upload-icon { font-size: 48px; margin-bottom: 16px; }
.upload-text { color: #888; font-weight: 600; }

.preview-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.preview-img, .preview-video {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}

.preview-video { height: 200px; }

.preview-actions {
  display: flex;
  gap: 16px;
  width: 100%;
}

.action-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 50px;
  font-weight: 700;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
}

.action-btn.re-upload {
  background: #f0f0f5;
  color: #888;
}

.action-btn.analyze {
  background: linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%);
  color: white;
  box-shadow: 0 8px 20px rgba(255, 154, 158, 0.3);
}

.action-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Result Section */
.result-section {
  margin-top: 24px;
  animation: slideUp 0.6s ease-out;
}

.result-header {
  border-bottom: 1px solid rgba(0,0,0,0.05);
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.result-header h3 {
  margin: 0;
  color: #2d3436;
  font-size: 18px;
}

.result-media-box {
  margin-bottom: 16px;
  border-radius: 16px;
  overflow: hidden;
}

.result-img, .result-video { width: 100%; display: block; }
.result-video { height: 200px; }

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-summary-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 600;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.6);
  padding: 12px 16px;
  border-radius: 12px;
}

.badge {
  background: #ffe0e6;
  color: #ff6b6b;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 14px;
}

.result-conf {
  color: #888;
  font-size: 14px;
}

.no-result {
  text-align: center;
  color: #888;
  padding: 20px;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 品种知识展示区域样式 */
.knowledge-section {
  margin-top: 24px;
  animation: slideUp 0.6s ease-out;
}

.knowledge-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.knowledge-header h3 {
  margin: 0;
  color: #2d3436;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.breed-name-tag {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.knowledge-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.knowledge-image-box {
  width: 100%;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.knowledge-image {
  width: 100%;
  height: auto;
  display: block;
  max-height: 200px;
  object-fit: cover;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.6);
  padding: 12px;
  border-radius: 12px;
}

.info-icon {
  font-size: 24px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-label {
  font-size: 12px;
  color: #888;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: #2d3436;
}

.knowledge-detail {
  background: rgba(255, 255, 255, 0.5);
  padding: 14px;
  border-radius: 12px;
  border-left: 3px solid #ff9a9e;
}

.detail-title {
  margin: 0 0 8px 0;
  font-size: 15px;
  font-weight: 700;
  color: #2d3436;
}

.detail-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #555;
}

/* 知识加载中样式 */
.knowledge-loading {
  margin-top: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  animation: slideUp 0.6s ease-out;
}

.loading-icon {
  font-size: 24px;
  animation: bounce 1s ease infinite;
}

.loading-text {
  color: #666;
  font-size: 14px;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
</style>
