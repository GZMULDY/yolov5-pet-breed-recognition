<template>
  <div class="profile-page">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="back-btn" @click="goBack">
        <span>←</span>
      </div>
      <div class="title">个人信息</div>
      <div class="placeholder"></div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content">
      <!-- 头像区域 -->
      <div class="avatar-section" @click="handleAvatarClick">
        <div class="avatar-wrapper">
          <img v-if="avatarPreview" :src="avatarPreview" class="avatar-img" />
          <div v-else class="avatar-placeholder">
            <span>{{ userInfo.nickname ? userInfo.nickname[0] : userInfo.username[0] }}</span>
          </div>
          <div class="avatar-edit-icon">
            <span>📷</span>
          </div>
        </div>
        <div class="avatar-tip">点击更换头像</div>
      </div>

      <!-- 表单区域 -->
      <div class="form-section">
        <!-- 用户名（不可编辑） -->
        <div class="form-item">
          <div class="form-label">用户名</div>
          <div class="form-value readonly">{{ userInfo.username }}</div>
        </div>

        <!-- 昵称 -->
        <div class="form-item">
          <div class="form-label">昵称</div>
          <input 
            v-model="formData.nickname" 
            class="form-input" 
            placeholder="请输入昵称"
            maxlength="50"
          />
        </div>

        <!-- 邮箱（不可编辑） -->
        <div class="form-item">
          <div class="form-label">邮箱</div>
          <div class="form-value readonly">{{ userInfo.email || '未设置' }}</div>
        </div>

        <!-- 角色 -->
        <div class="form-item">
          <div class="form-label">角色</div>
          <div class="form-value readonly">{{ userInfo.role === 'admin' ? '管理员' : '普通用户' }}</div>
        </div>

        <!-- 注册时间 -->
        <div class="form-item">
          <div class="form-label">注册时间</div>
          <div class="form-value readonly">{{ formatDate(userInfo.created_at) }}</div>
        </div>
      </div>

      <!-- 保存按钮 -->
      <div class="save-section">
        <button class="save-btn" :disabled="saving" @click="handleSave">
          {{ saving ? '保存中...' : '保存修改' }}
        </button>
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
import { ref, reactive, onMounted, getCurrentInstance } from 'vue';
import { useRouter } from 'vue-router';
import { getProfile, updateProfile } from '@/api/auth';

const { proxy } = getCurrentInstance();
const uni = proxy.uni;
const router = useRouter();

// 用户信息
const userInfo = reactive({
  id: 0,
  username: '',
  email: '',
  nickname: '',
  avatar: null,
  role: '',
  created_at: null
});

// 表单数据
const formData = reactive({
  nickname: ''
});

// 头像预览
const avatarPreview = ref(null);
// 头像 base64 数据
const avatarBase64 = ref(null);
// 保存中状态
const saving = ref(false);
// 文件输入引用
const fileInput = ref(null);

// 获取用户信息
const fetchProfile = async () => {
  try {
    const response = await getProfile();
    // 后端返回统一响应格式: { code: "200", message: "...", data: {...} }
    if (response && response.code === '200') {
      const data = response.data;
      userInfo.id = data.id;
      userInfo.username = data.username;
      userInfo.email = data.email;
      userInfo.nickname = data.nickname || '';
      userInfo.avatar = data.avatar;
      userInfo.role = data.role;
      userInfo.created_at = data.created_at;
      
      // 设置表单数据
      formData.nickname = userInfo.nickname || '';
      
      // 设置头像预览
      if (data.avatar) {
        avatarPreview.value = `data:image/jpeg;base64,${data.avatar}`;
        avatarBase64.value = data.avatar;
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
  }
};

// 点击头像
const handleAvatarClick = () => {
  fileInput.value.click();
};

// 处理文件选择
const handleFileChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
  if (!allowedTypes.includes(file.type)) {
    uni.showToast({ title: '仅支持 jpg、jpeg、png 格式的图片', icon: 'none' });
    return;
  }

  // 验证文件大小（5MB）
  if (file.size > 5 * 1024 * 1024) {
    uni.showToast({ title: '图片大小不能超过5MB', icon: 'none' });
    return;
  }

  // 压缩并转换为 base64
  try {
    const result = await compressImage(file);
    avatarPreview.value = result.preview;
    avatarBase64.value = result.base64;
  } catch (error) {
    uni.showToast({ title: '图片处理失败', icon: 'none' });
  }

  // 清空 input 以便重复选择同一文件
  event.target.value = '';
};

// 压缩图片
const compressImage = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        // 限制最大尺寸
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

// 保存修改
const handleSave = async () => {
  if (saving.value) return;

  // 检查是否有修改
  const nicknameChanged = formData.nickname !== userInfo.nickname;
  const avatarChanged = avatarBase64.value !== userInfo.avatar;

  if (!nicknameChanged && !avatarChanged) {
    uni.showToast({ title: '没有需要保存的修改', icon: 'none' });
    return;
  }

  saving.value = true;

  try {
    const updateData = {};
    
    if (nicknameChanged) {
      updateData.nickname = formData.nickname;
    }
    
    if (avatarChanged) {
      updateData.avatar = avatarBase64.value;
    }

    const response = await updateProfile(updateData);
    
    // 后端返回统一响应格式: { code: "200", message: "...", data: {...} }
    if (response && response.code === '200') {
      uni.showToast({ title: '保存成功', icon: 'success' });
      // 更新本地用户信息
      userInfo.nickname = formData.nickname;
      userInfo.avatar = avatarBase64.value;
    }
  } catch (error) {
    console.error('保存失败:', error);
  } finally {
    saving.value = false;
  }
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '未知';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 返回上一页
const goBack = () => {
  router.back();
};

onMounted(() => {
  fetchProfile();
});
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #fff5f7 0%, #ffeef2 100%);
}

/* 顶部导航栏 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  background: linear-gradient(135deg, #ff6b8a 0%, #ff8e9e 100%);
  color: white;
}

.back-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.placeholder {
  width: 40px;
}

/* 主要内容区域 */
.content {
  padding: 20px;
}

/* 头像区域 */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
  cursor: pointer;
}

.avatar-wrapper {
  position: relative;
  width: 100px;
  height: 100px;
}

.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #ff8e9e;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b8a 0%, #ff8e9e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  color: white;
  font-weight: bold;
  border: 3px solid #ffb3c1;
}

.avatar-edit-icon {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 32px;
  height: 32px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.avatar-tip {
  margin-top: 10px;
  font-size: 14px;
  color: #999;
}

/* 表单区域 */
.form-section {
  background: white;
  border-radius: 16px;
  padding: 10px 20px;
  margin-bottom: 30px;
  box-shadow: 0 2px 12px rgba(255, 107, 138, 0.1);
}

.form-item {
  padding: 15px 0;
  border-bottom: 1px solid #f5f5f5;
}

.form-item:last-child {
  border-bottom: none;
}

.form-label {
  font-size: 14px;
  color: #999;
  margin-bottom: 8px;
}

.form-value {
  font-size: 16px;
  color: #333;
}

.form-value.readonly {
  color: #666;
}

.form-input {
  width: 100%;
  font-size: 16px;
  color: #333;
  border: none;
  outline: none;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.form-input:focus {
  border-bottom-color: #ff8e9e;
}

/* 保存按钮 */
.save-section {
  padding: 0 20px;
}

.save-btn {
  width: 100%;
  height: 50px;
  background: linear-gradient(135deg, #ff6b8a 0%, #ff8e9e 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 107, 138, 0.4);
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
</style>
