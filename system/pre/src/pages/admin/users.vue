<template>
  <div class="page-container aurora-bg">
    <div class="content-wrapper">
      <div class="header">
        <div class="title">
          <span class="emoji">✨</span> 
          <span class="text-gradient">用户管理</span>
        </div>
        <button class="action-btn" @click="openAddModal">
          <span class="btn-icon">➕</span> 添加用户
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="search-section">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input 
            v-model="searchKeyword" 
            placeholder="搜索用户名..." 
            class="search-input"
            @input="handleSearch"
          />
          <button v-if="searchKeyword" class="clear-btn" @click="clearSearch">✕</button>
        </div>
      </div>

      <div class="user-list">
        <div 
          v-for="(user, index) in users" 
          :key="user.id" 
          class="user-card glass-effect"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="user-avatar">
            <img v-if="user.avatar" :src="`data:image/jpeg;base64,${user.avatar}`" class="avatar-img" />
            <span v-else>{{ (user.nickname || user.username).charAt(0).toUpperCase() }}</span>
          </div>
          <div class="user-info">
            <div class="username">{{ user.nickname || user.username }}</div>
            <div class="user-meta">
              <span class="role-badge" :class="user.role">
                {{ user.role === 'admin' ? '👑 管理员' : '🌸 普通用户' }}
              </span>
              <span class="email" v-if="user.email">📧 {{ user.email }}</span>
            </div>
            <div class="user-extra">
              <span v-if="user.nickname && user.nickname !== user.username" class="extra-item">
                用户名: {{ user.username }}
              </span>
              <span class="extra-item">ID: {{ user.id }}</span>
            </div>
          </div>
          <div class="actions">
            <button class="icon-btn edit" @click="editUser(user)" title="编辑">
              ✏️
            </button>
            <button class="icon-btn delete" @click="deleteUser(user)" title="删除">
              🗑️
            </button>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="users.length === 0" class="empty-state">
          <span class="empty-icon">📭</span>
          <div class="empty-text">{{ searchKeyword ? '没有找到匹配的用户' : '暂无用户数据' }}</div>
        </div>
      </div>
    </div>

    <!-- Modal for Add/Edit -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal glass-effect bounce-in">
        <div class="modal-header">
          {{ isEditing ? '📝 编辑用户' : '✨ 添加新用户' }}
        </div>
        
        <div class="modal-content">
          <!-- 头像区域 -->
          <div class="avatar-section" @click="handleAvatarClick">
            <div class="avatar-preview">
              <img v-if="formData.avatarPreview" :src="formData.avatarPreview" class="preview-img" />
              <div v-else class="avatar-placeholder">
                <span>{{ formData.username ? formData.username.charAt(0).toUpperCase() : '?' }}</span>
              </div>
              <div class="avatar-edit-icon">📷</div>
            </div>
            <div class="avatar-tip">点击更换头像</div>
          </div>
          
          <!-- 表单 -->
          <div class="form">
            <div class="input-group">
              <span class="input-icon">👤</span>
              <input 
                v-model="formData.username" 
                placeholder="用户名" 
                class="cute-input" 
                :disabled="isEditing"
                :class="{ disabled: isEditing }"
              />
            </div>
            <div class="input-group">
              <span class="input-icon">🎀</span>
              <input v-model="formData.nickname" placeholder="昵称 (可选)" class="cute-input" />
            </div>
            <div class="input-group">
              <span class="input-icon">💌</span>
              <input v-model="formData.email" placeholder="邮箱 (可选)" class="cute-input" />
            </div>
            <div class="input-group">
              <span class="input-icon">🔑</span>
              <input 
                v-model="formData.password" 
                :placeholder="isEditing ? '密码 (留空不修改)' : '密码'" 
                class="cute-input" 
                type="password"
              />
            </div>
            
            <div class="role-select">
              <div class="label">🎀 选择角色：</div>
              <div class="radio-group">
                <label class="cute-radio">
                  <input type="radio" value="user" v-model="formData.role">
                  <span class="radio-label">🌸 用户</span>
                </label>
                <label class="cute-radio">
                  <input type="radio" value="admin" v-model="formData.role">
                  <span class="radio-label">👑 管理员</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="modal-btn cancel" @click="closeModal">👋 取消</button>
          <button class="modal-btn confirm" @click="submitForm" :disabled="submitting">
            {{ submitting ? '处理中...' : '💖 确定' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 隐藏的文件选择输入 -->
    <input 
      ref="fileInput" 
      type="file" 
      accept="image/*" 
      style="display: none" 
      @change="handleFileChange"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { uni } from '@/utils/uni-adapter.js';

const users = ref([]);
const searchKeyword = ref('');
const showModal = ref(false);
const isEditing = ref(false);
const editingId = ref(null);
const submitting = ref(false);
const fileInput = ref(null);

const formData = reactive({
  username: '',
  nickname: '',
  email: '',
  password: '',
  role: 'user',
  avatar: null,
  avatarPreview: null
});

import { BASE_URL } from '@/utils/request.js';
const API_URL = BASE_URL;

let searchTimer = null;

const fetchUsers = async (keyword = '') => {
  const token = uni.getStorageSync('token');
  try {
    let url = `${API_URL}/users`;
    if (keyword) {
      url += `?username=${encodeURIComponent(keyword)}`;
    }
    
    const res = await uni.request({
      url,
      header: { 'Authorization': `Bearer ${token}` }
    });
    
    if (res.statusCode === 200) {
      const responseData = res.data?.data || res.data;
      // 后端返回 {items: [...], total: N}，提取 items 数组
      users.value = Array.isArray(responseData) ? responseData : (responseData.items || []);
    }
  } catch (e) {
    console.error('获取用户列表失败:', e);
  }
};

const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    fetchUsers(searchKeyword.value);
  }, 300);
};

const clearSearch = () => {
  searchKeyword.value = '';
  fetchUsers();
};

const openAddModal = () => {
  isEditing.value = false;
  editingId.value = null;
  resetFormData();
  showModal.value = true;
};

const editUser = (user) => {
  isEditing.value = true;
  editingId.value = user.id;
  formData.username = user.username;
  formData.nickname = user.nickname || '';
  formData.email = user.email || '';
  formData.role = user.role;
  formData.password = '';
  formData.avatar = null;
  
  if (user.avatar) {
    formData.avatarPreview = `data:image/jpeg;base64,${user.avatar}`;
    formData.avatar = user.avatar;
  } else {
    formData.avatarPreview = null;
  }
  
  showModal.value = true;
};

const deleteUser = async (user) => {
  uni.showModal({
    title: '💔 确认删除',
    content: `确定要删除用户 "${user.nickname || user.username}" 吗？`,
    confirmColor: '#FF9A9E',
    success: async (res) => {
      if (res.confirm) {
        const token = uni.getStorageSync('token');
        try {
          await uni.request({
            url: `${API_URL}/users/${user.id}`,
            method: 'DELETE',
            header: { 'Authorization': `Bearer ${token}` }
          });
          uni.showToast({ title: '删除成功 ✨', icon: 'success' });
          fetchUsers(searchKeyword.value);
        } catch (e) {
          console.error('删除失败:', e);
        }
      }
    }
  });
};

const handleAvatarClick = () => {
  fileInput.value.click();
};

const handleFileChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
  if (!allowedTypes.includes(file.type)) {
    uni.showToast({ title: '仅支持 jpg、jpeg、png 格式', icon: 'none' });
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    uni.showToast({ title: '图片大小不能超过5MB', icon: 'none' });
    return;
  }

  try {
    const result = await compressImage(file);
    formData.avatarPreview = result.preview;
    formData.avatar = result.base64;
  } catch (error) {
    uni.showToast({ title: '图片处理失败', icon: 'none' });
  }

  event.target.value = '';
};

const compressImage = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        const maxDimension = 300;
        if (width > height) {
          if (width > maxDimension) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          }
        } else {
          if (height > maxDimension) {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        const mimeType = file.type || 'image/jpeg';
        const base64WithPrefix = canvas.toDataURL(mimeType, 0.8);
        const base64Data = base64WithPrefix.split(',')[1];

        resolve({
          base64: base64Data,
          preview: base64WithPrefix
        });
      };
      img.onerror = reject;
      img.src = e.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};

const submitForm = async () => {
  if (submitting.value) return;
  
  if (!formData.username.trim()) {
    uni.showToast({ title: '请输入用户名', icon: 'none' });
    return;
  }
  
  if (!isEditing.value && !formData.password) {
    uni.showToast({ title: '请输入密码', icon: 'none' });
    return;
  }

  submitting.value = true;
  const token = uni.getStorageSync('token');
  const url = isEditing.value ? `${API_URL}/users/${editingId.value}` : `${API_URL}/users`;
  const method = isEditing.value ? 'PUT' : 'POST';

  const data = {};
  
  // 添加用户时需要 username
  if (!isEditing.value) {
    data.username = formData.username;
  }
  
  // 可选字段
  if (formData.nickname) {
    data.nickname = formData.nickname;
  }
  if (formData.email) {
    data.email = formData.email;
  }
  data.role = formData.role;
  
  if (formData.password) {
    data.password = formData.password;
  }
  
  if (formData.avatar) {
    data.avatar = formData.avatar;
  }

  try {
    const res = await uni.request({
      url,
      method,
      data,
      header: { 'Authorization': `Bearer ${token}` }
    });

    if (res.statusCode === 200 || res.statusCode === 201) {
      uni.showToast({ 
        title: isEditing.value ? '修改成功 💖' : '添加成功 🎉', 
        icon: 'success' 
      });
      closeModal();
      fetchUsers(searchKeyword.value);
    }
  } catch (e) {
    console.error('提交失败:', e);
  } finally {
    submitting.value = false;
  }
};

const resetFormData = () => {
  formData.username = '';
  formData.nickname = '';
  formData.email = '';
  formData.password = '';
  formData.role = 'user';
  formData.avatar = null;
  formData.avatarPreview = null;
};

const closeModal = () => {
  showModal.value = false;
  isEditing.value = false;
  editingId.value = null;
  resetFormData();
};

onMounted(() => {
  fetchUsers();
});
</script>

<style scoped>
/* Aurora Background Animation */
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

.content-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 10px;
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
  letter-spacing: 1px;
}

.emoji {
  font-size: 28px;
}

.action-btn {
  background: linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 50px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(255, 154, 158, 0.4);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 25px rgba(255, 154, 158, 0.5);
}

/* Search Section */
.search-section {
  margin-bottom: 20px;
  padding: 0 10px;
}

.search-box {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 25px;
  padding: 0 16px;
  box-shadow: 0 4px 15px rgba(255, 154, 158, 0.15);
}

.search-icon {
  font-size: 18px;
  margin-right: 10px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 14px 0;
  font-size: 15px;
  color: #555;
  outline: none;
}

.search-input::placeholder {
  color: #aaa;
}

.clear-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 16px;
  cursor: pointer;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-btn:hover {
  color: #666;
}

/* User List & Cards */
.user-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.glass-effect {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05);
}

.user-card {
  padding: 20px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  animation: slideIn 0.5s ease-out backwards;
}

.user-card:hover {
  transform: translateY(-3px);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 15px 35px rgba(255, 154, 158, 0.15);
}

.user-avatar {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 800;
  font-size: 22px;
  margin-right: 20px;
  box-shadow: 0 4px 10px rgba(255, 154, 158, 0.3);
  border: 3px solid white;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.username {
  font-size: 18px;
  font-weight: 700;
  color: #4a4a4a;
  margin-bottom: 6px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.role-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
}

.role-badge.admin {
  background-color: #ffe0e6;
  color: #ff6b6b;
}

.role-badge.user {
  background-color: #e0f0ff;
  color: #5ca1ff;
}

.email {
  font-size: 13px;
  color: #888;
}

.user-extra {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.extra-item {
  font-size: 12px;
  color: #aaa;
}

.actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s ease;
  background: transparent;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: scale(1.1);
}

.icon-btn.edit:hover { color: #FF9A9E; background: #fff0f1; }
.icon-btn.delete:hover { color: #ff4757; background: #ffe0e0; }

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: #999;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 230, 240, 0.4);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  width: 100%;
  max-width: 400px;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: 32px;
  border: 2px solid rgba(255, 255, 255, 0.8);
}

.bounce-in {
  animation: bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.modal-header {
  font-size: 22px;
  font-weight: 800;
  padding: 25px 30px 0;
  text-align: center;
  color: #4a4a4a;
  background: linear-gradient(45deg, #ff9a9e, #fad0c4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.modal-content {
  padding: 20px 30px;
}

/* Avatar Section in Modal */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
  cursor: pointer;
}

.avatar-preview {
  position: relative;
  width: 80px;
  height: 80px;
}

.preview-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #ff9a9e;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
  font-weight: bold;
  border: 3px solid #ffb3c1;
}

.avatar-edit-icon {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.avatar-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

/* Form */
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.input-group {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  z-index: 1;
  font-size: 16px;
}

.cute-input {
  width: 100%;
  padding: 14px 14px 14px 44px;
  background: rgba(255, 255, 255, 0.6);
  border: 2px solid transparent;
  border-radius: 20px;
  font-size: 15px;
  color: #555;
  transition: all 0.3s;
  box-sizing: border-box;
}

.cute-input:focus {
  outline: none;
  background: white;
  border-color: #ff9a9e;
  box-shadow: 0 0 0 4px rgba(255, 154, 158, 0.2);
}

.cute-input.disabled {
  background: rgba(230, 230, 230, 0.5);
  color: #999;
  cursor: not-allowed;
}

.role-select {
  margin-top: 6px;
}

.role-select .label {
  margin-bottom: 10px;
  font-weight: 600;
  color: #666;
  font-size: 14px;
}

.radio-group {
  display: flex;
  gap: 20px;
}

.cute-radio {
  cursor: pointer;
  display: flex;
  align-items: center;
}

.cute-radio input {
  display: none;
}

.radio-label {
  padding: 8px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.6);
  border: 2px solid transparent;
  transition: all 0.3s;
  font-size: 14px;
  font-weight: 600;
  color: #888;
}

.cute-radio input:checked + .radio-label {
  background: #fff;
  border-color: #ff9a9e;
  color: #ff9a9e;
  box-shadow: 0 4px 10px rgba(255, 154, 158, 0.3);
  transform: scale(1.05);
}

.modal-actions {
  display: flex;
  gap: 15px;
  padding: 0 30px 25px;
}

.modal-btn {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 20px;
  font-weight: 700;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
}

.modal-btn.cancel {
  background: #f0f0f5;
  color: #888;
}

.modal-btn.cancel:hover {
  background: #e0e0e5;
}

.modal-btn.confirm {
  background: linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%);
  color: white;
  box-shadow: 0 8px 20px rgba(255, 154, 158, 0.3);
}

.modal-btn.confirm:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 25px rgba(255, 154, 158, 0.4);
}

.modal-btn.confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Animations */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes bounceIn {
  0% { transform: scale(0.3); opacity: 0; }
  50% { transform: scale(1.05); opacity: 1; }
  70% { transform: scale(0.9); }
  100% { transform: scale(1); }
}
</style>
