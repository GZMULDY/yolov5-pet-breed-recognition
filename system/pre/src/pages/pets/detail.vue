<template>
  <div class="page-container aurora-bg">
    <div class="content-wrapper">
      <div class="header">
        <div class="back-btn" @click="goBack">‹</div>
        <div class="title">
          <span class="text-gradient">{{ breedName }}</span>
        </div>
        <div v-if="isAdmin" class="edit-btn" @click="showEditModal">✏️</div>
      </div>

      <div v-if="breed" class="detail-content">
        <div class="breed-hero glass-effect">
          <img 
            v-if="breed.image" 
            :src="breed.image" 
            class="hero-image"
            :alt="breedName"
          />
          <div v-else class="hero-placeholder">
            <span class="placeholder-emoji">🐾</span>
            <span class="placeholder-text">{{ breedName }}</span>
          </div>
        </div>

        <div class="info-cards">
          <div class="info-card glass-effect">
            <div class="info-icon">📍</div>
            <div class="info-label">原产地</div>
            <div class="info-value">{{ breed.origin || '未知' }}</div>
          </div>
          <div class="info-card glass-effect">
            <div class="info-icon">📏</div>
            <div class="info-label">体型</div>
            <div class="info-value">{{ breed.size || '未知' }}</div>
          </div>
          <div class="info-card glass-effect">
            <div class="info-icon">⏰</div>
            <div class="info-label">寿命</div>
            <div class="info-value">{{ breed.lifespan || '未知' }}</div>
          </div>
        </div>

        <div class="section glass-effect">
          <div class="section-title">
            <span class="section-icon">📖</span>
            品种介绍
          </div>
          <div class="section-content">{{ breed.description || '暂无介绍' }}</div>
        </div>

        <div class="section glass-effect">
          <div class="section-title">
            <span class="section-icon">💕</span>
            性格特点
          </div>
          <div class="section-content">{{ breed.personality || '暂无描述' }}</div>
        </div>

        <div class="section glass-effect">
          <div class="section-title">
            <span class="section-icon">🛁</span>
            护理建议
          </div>
          <div class="section-content">{{ breed.care_tips || '暂无建议' }}</div>
        </div>

        <div class="section glass-effect">
          <div class="section-title">
            <span class="section-icon">🍖</span>
            饮食需求
          </div>
          <div class="section-content">{{ breed.diet_needs || '暂无信息' }}</div>
        </div>

        <div class="section glass-effect">
          <div class="section-title">
            <span class="section-icon">⚠️</span>
            健康注意
          </div>
          <div class="section-content">{{ breed.health_issues || '暂无信息' }}</div>
        </div>

        <div v-if="breed.exercise_needs" class="section glass-effect">
          <div class="section-title">
            <span class="section-icon">🏃</span>
            运动需求
          </div>
          <div class="section-content">{{ breed.exercise_needs }}</div>
        </div>
      </div>

      <div v-if="!breed && !loading" class="empty-state">
        <p>未找到该品种信息</p>
      </div>

      <div v-if="showModal" class="modal-overlay" @click="hideEditModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <span class="modal-title">编辑宠物知识</span>
            <span class="modal-close" @click="hideEditModal">✕</span>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <span class="form-label">图片</span>
              <div class="image-upload" @click="handleChooseImage">
                <img 
                  v-if="imagePreview" 
                  :src="imagePreview" 
                  class="uploaded-image"
                  alt="预览图"
                />
                <div v-else class="upload-placeholder">
                  <span class="upload-icon">📷</span>
                  <span class="upload-text">点击上传图片</span>
                  <span class="upload-hint">支持 jpg、png、jpeg 格式，最大 5MB</span>
                </div>
                <!-- 上传进度遮罩 -->
                <div v-if="isProcessing" class="upload-overlay">
                  <div class="progress-container">
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        :style="{ width: uploadProgress + '%' }"
                      ></div>
                    </div>
                    <span class="progress-text">{{ uploadProgress }}%</span>
                  </div>
                </div>
              </div>
              <!-- 图片信息提示 -->
              <div v-if="imagePreview && !isProcessing" class="image-info">
                <span v-if="compressionRatio > 0" class="info-text">
                  已压缩 {{ compressionRatio }}%
                </span>
                <span class="info-text link" @click.stop="clearImage">清除图片</span>
              </div>
              <!-- 错误提示 -->
              <div v-if="imageError" class="error-tip">
                <span class="error-text">{{ imageError }}</span>
              </div>
            </div>
            <div class="form-group">
              <span class="form-label">原产地</span>
              <input class="form-input" v-model="editForm.origin" placeholder="请输入原产地" />
            </div>
            <div class="form-group">
              <span class="form-label">体型</span>
              <input class="form-input" v-model="editForm.size" placeholder="请输入体型" />
            </div>
            <div class="form-group">
              <span class="form-label">寿命</span>
              <input class="form-input" v-model="editForm.lifespan" placeholder="请输入寿命" />
            </div>
            <div class="form-group">
              <span class="form-label">品种介绍</span>
              <textarea class="form-textarea" v-model="editForm.description" placeholder="请输入品种介绍" />
            </div>
            <div class="form-group">
              <span class="form-label">性格特点</span>
              <textarea class="form-textarea" v-model="editForm.personality" placeholder="请输入性格特点" />
            </div>
            <div class="form-group">
              <span class="form-label">护理建议</span>
              <textarea class="form-textarea" v-model="editForm.care_tips" placeholder="请输入护理建议" />
            </div>
            <div class="form-group">
              <span class="form-label">饮食需求</span>
              <textarea class="form-textarea" v-model="editForm.diet_needs" placeholder="请输入饮食需求" />
            </div>
            <div class="form-group">
              <span class="form-label">健康注意</span>
              <textarea class="form-textarea" v-model="editForm.health_issues" placeholder="请输入健康注意" />
            </div>
            <div class="form-group">
              <span class="form-label">运动需求</span>
              <textarea class="form-textarea" v-model="editForm.exercise_needs" placeholder="请输入运动需求" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="hideEditModal">取消</button>
            <button 
              class="btn-save" 
              @click="saveBreed" 
              :disabled="saving || isProcessing"
            >
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, getCurrentInstance, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const { proxy } = getCurrentInstance();
const uni = proxy.uni;
const route = useRoute();
const router = useRouter();
import { useImageUpload } from '@/composables/useImageUpload';

// 使用图片上传 composable
const {
  imagePreview,
  imageBase64,
  isProcessing,
  uploadProgress,
  errorMessage: imageError,
  compressionRatio,
  imageChanged,
  chooseAndProcessImage,
  setExistingImage,
  clearImage,
  reset: resetImageUpload,
  getImageData,
  initUni: initImageUploadUni
} = useImageUpload({
  maxSize: 5 * 1024 * 1024,
  maxDimension: 800,
  quality: 0.7
});

// 初始化图片上传的 uni 对象
initImageUploadUni(uni);

const breedId = ref(0);
const breedName = ref('');
const breed = ref(null);
const loading = ref(false);
const isAdmin = ref(false);
const showModal = ref(false);
const saving = ref(false);
const editForm = ref({
  origin: '',
  size: '',
  lifespan: '',
  description: '',
  personality: '',
  care_tips: '',
  diet_needs: '',
  health_issues: '',
  exercise_needs: ''
});
const API_URL = 'http://127.0.0.1:8000/api/v1';

function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

const checkUserRole = () => {
  const token = uni.getStorageSync('token');
  if (token) {
    const payload = parseJwt(token);
    if (payload && payload.role === 'admin') {
      isAdmin.value = true;
    }
  }
};

onMounted(() => {
  // 从路由参数获取 id 和 name
  breedId.value = parseInt(route.query.id) || 0;
  breedName.value = decodeURIComponent(route.query.name || '');
  fetchBreedDetail();
  checkUserRole();
});

const fetchBreedDetail = async () => {
  loading.value = true;
  try {
    const token = uni.getStorageSync('token');
    const response = await uni.request({
      url: `${API_URL}/breeds/${breedId.value}`,
      method: 'GET',
      header: { 'Authorization': `Bearer ${token}` }
    });

    let res = response;
    if (Array.isArray(response)) {
      res = response[1] || response[0];
    }
    
    if (!res) {
      // 错误已在 request.js 中统一处理
      return;
    }

    if (res.statusCode === 200) {
      // 后端返回格式是 { code, message, data: {...}, timestamp }
      const breedData = res.data?.data || res.data;
      breed.value = breedData;
    } else if (res.statusCode === 401) {
      uni.showToast({ title: '请先登录', icon: 'none' });
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/login/login' });
      }, 1500);
    } else {
      uni.showToast({ title: '加载失败: ' + res.statusCode, icon: 'none' });
    }
  } catch (e) {
    console.error('Failed to fetch breed detail:', e);
    uni.showToast({ title: '加载失败: ' + e.message, icon: 'none' });
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  router.replace('/pets/encyclopedia');
};

const showEditModal = () => {
  if (!breed.value || !breed.value.id) {
    uni.showToast({ title: '数据加载中，请稍后', icon: 'none' });
    return;
  }
  const b = breed.value;
  
  // 设置表单数据
  editForm.value = {
    origin: b.origin || '',
    size: b.size || '',
    lifespan: b.lifespan || '',
    description: b.description || '',
    personality: b.personality || '',
    care_tips: b.care_tips || '',
    diet_needs: b.diet_needs || '',
    health_issues: b.health_issues || '',
    exercise_needs: b.exercise_needs || ''
  };
  
  // 设置已有图片预览（不设置base64，因为已有图片不需要重新上传）
  setExistingImage(b.image || '');
  
  showModal.value = true;
};

/**
 * 处理图片选择
 */
const handleChooseImage = async () => {
  if (isProcessing.value) return;
  await chooseAndProcessImage({
    count: 1,
    sourceType: ['album', 'camera']
  });
};

const hideEditModal = () => {
  showModal.value = false;
  resetImageUpload();
};

const saveBreed = async () => {
  if (saving.value || isProcessing.value) return;
  
  try {
    saving.value = true;
    const token = uni.getStorageSync('token');
    uni.showLoading({ title: '保存中...' });
    
    const requestData = {
      origin: editForm.value.origin || null,
      size: editForm.value.size || null,
      lifespan: editForm.value.lifespan || null,
      description: editForm.value.description || null,
      personality: editForm.value.personality || null,
      care_tips: editForm.value.care_tips || null,
      diet_needs: editForm.value.diet_needs || null,
      health_issues: editForm.value.health_issues || null,
      exercise_needs: editForm.value.exercise_needs || null
    };
    
    const imageData = getImageData();
    if (imageData !== null) {
      requestData.image_base64 = imageData;
    }
    
    const res = await uni.request({
      url: `${API_URL}/breeds/${breedId.value}`,
      method: 'PUT',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: requestData
    });
    
    let response = res;
    if (Array.isArray(res)) {
      response = res[1] || res[0];
    }
    
    uni.hideLoading();
    
    if (response.statusCode === 200) {
      uni.showToast({ title: '保存成功', icon: 'success' });
      showModal.value = false;
      resetImageUpload();
      // 刷新当前详细界面
      fetchBreedDetail();
    } else if (response.statusCode === 403) {
      uni.showToast({ title: '权限不足', icon: 'none' });
    } else {
      uni.showToast({ title: '保存失败: ' + (response.data?.detail || response.statusCode), icon: 'none' });
    }
  } catch (e) {
    uni.hideLoading();
    console.error('Save error:', e);
    uni.showToast({ title: '保存失败: ' + (e.errMsg || e.message || '未知错误'), icon: 'none' });
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
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
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.back-btn {
  font-size: 32px;
  color: #666;
  margin-right: 12px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.text-gradient {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(45deg, #ff6b6b, #ff8e53);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.breed-hero {
  border-radius: 20px;
  overflow: hidden;
}

.hero-image {
  width: 100%;
  display: block;
}

.hero-placeholder {
  height: 200px;
  background: linear-gradient(135deg, #ffe0e6 0%, #fff5f7 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.placeholder-emoji {
  font-size: 60px;
}

.placeholder-text {
  font-size: 18px;
  color: #666;
  font-weight: 600;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.info-card {
  padding: 16px 12px;
  border-radius: 16px;
  text-align: center;
}

.info-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.info-label {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
}

.info-value {
  font-size: 14px;
  font-weight: 700;
  color: #2d3436;
}

.section {
  padding: 20px;
  border-radius: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: #2d3436;
  margin-bottom: 12px;
}

.section-icon {
  font-size: 20px;
}

.section-content {
  font-size: 14px;
  line-height: 1.8;
  color: #555;
}

.glass-effect {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05);
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 40px;
}

.edit-btn {
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 20px;
  width: 90%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-title {
  font-size: 18px;
  font-weight: 700;
  color: #333;
}

.modal-close {
  font-size: 20px;
  color: #999;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  max-height: 65vh;
  overflow-y: auto;
  box-sizing: border-box;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 10px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 10px;
  font-size: 14px;
  min-height: 80px;
  box-sizing: border-box;
}

.image-upload {
  width: 100%;
  height: 150px;
  border: 2px dashed #ddd;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  cursor: pointer;
  position: relative;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 40px;
}

.upload-text {
  font-size: 14px;
  color: #999;
}

.upload-hint {
  font-size: 12px;
  color: #bbb;
}

.uploaded-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 上传进度遮罩 */
.upload-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  width: 80%;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff9a9e, #fecfef);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

/* 图片信息 */
.image-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 0 4px;
}

.info-text {
  font-size: 12px;
  color: #888;
}

.info-text.link {
  color: #ff6b6b;
  cursor: pointer;
}

/* 错误提示 */
.error-tip {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fff5f5;
  border-radius: 6px;
}

.error-text {
  font-size: 12px;
  color: #ff4757;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.btn-cancel, .btn-save {
  flex: 1;
  padding: 12px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-save {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  color: #fff;
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
