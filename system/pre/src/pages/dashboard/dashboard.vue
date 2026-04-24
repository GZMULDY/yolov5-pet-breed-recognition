<template>
  <div class="dashboard-container">
    <!-- Aurora Background -->
    <div class="aurora-bg">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
    </div>

    <div class="content-wrapper">
      <!-- Header Section -->
      <div class="header">
        <div class="user-profile" @click="navigateTo('/user/profile')">
          <div class="avatar-box">
            <img v-if="userInfo.avatar" :src="userInfo.avatar" class="avatar-img" />
            <span v-else class="avatar-text">{{ avatarLetter }}</span>
          </div>
          <div class="user-info">
            <span class="welcome-text">Hi, {{ userInfo.nickname || userInfo.username || '铲屎官' }} 👋</span>
            <div class="role-badge" :class="userInfo.role">
              <span class="role-text">{{ userInfo.role === 'admin' ? '管理员' : '普通用户' }}</span>
            </div>
          </div>
        </div>
        
        <!-- Logout Button -->
        <div class="logout-btn" @click="handleLogout">
          <span class="logout-icon">🚪</span>
          <span class="logout-text">退出</span>
        </div>
      </div>

      <!-- Admin Control Center (Only for Admin) -->
      <div v-if="userInfo.role === 'admin'" class="section-container">
        <div class="section-header">
          <span class="section-title">🛡️ 管理控制台</span>
        </div>
        <div class="grid-menu">
          <div class="menu-card admin-card" @click="navigateTo('/pages/admin/users')">
            <div class="card-icon-bg purple">
              <span class="card-icon">👥</span>
            </div>
            <div class="card-content">
              <span class="card-title">用户管理</span>
              <span class="card-desc">权限与账户设置</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Pet Services (Common for all) -->
      <div class="section-container">
        <div class="section-header">
          <span class="section-title">🐾 宠物服务</span>
        </div>
        <div class="grid-menu">
          <div class="menu-card service-card" @click="navigateTo('/pages/pet/recognize')">
            <div class="card-icon-bg pink">
              <span class="card-icon">📸</span>
            </div>
            <div class="card-content">
              <span class="card-title">宠物识别</span>
              <span class="card-desc">AI 智能识宠</span>
            </div>
          </div>
          <div class="menu-card service-card" @click="navigateTo('/pages/pets/encyclopedia')">
            <div class="card-icon-bg orange">
              <span class="card-icon">📖</span>
            </div>
            <div class="card-content">
              <span class="card-title">宠物百科</span>
              <span class="card-desc">养护知识大全</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { getCurrentUser } from '@/api/auth';
import { uni } from '@/utils/uni-adapter.js';

const userInfo = ref({
  username: '加载中...',
  nickname: '',
  avatar: null,
  role: 'user'
});

const avatarLetter = computed(() => {
  if (userInfo.value.username && userInfo.value.username !== '加载中...') {
    return userInfo.value.username.charAt(0).toUpperCase();
  }
  return '🐶';
});

// Helper to parse JWT (Base64 decode)
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

const getUserInfo = async () => {
  const token = uni.getStorageSync('token');
  if (!token) {
    uni.reLaunch({ url: '/pages/login/login' });
    return;
  }

  // 1. Try to get info from token first (Fastest)
  const tokenPayload = parseJwt(token);
  if (tokenPayload) {
    userInfo.value.username = tokenPayload.sub;
    userInfo.value.role = tokenPayload.role || 'user';
    console.log('User Info from Token:', userInfo.value);
  }

  // 2. Fetch latest info from API (Optional if token is trusted, but good for updates)
  try {
    // 使用封装的 getCurrentUser API，响应已自动解析统一格式
    const res = await getCurrentUser();
    
    // 统一响应格式: res.data 包含用户信息
    if (res && res.data) {
      // 处理头像 base64 数据
      let avatarUrl = null;
      if (res.data.avatar) {
        avatarUrl = `data:image/jpeg;base64,${res.data.avatar}`;
      }
      
      userInfo.value = { 
        ...userInfo.value, 
        username: res.data.username || userInfo.value.username,
        nickname: res.data.nickname || '',
        avatar: avatarUrl,
        role: res.data.role || userInfo.value.role
      };
      console.log('User Info Updated from API:', userInfo.value);
    }
  } catch (e) {
    console.error('Fetch user info error:', e);
    // 如果 API 调用失败但 token 有效，继续使用 token 中的信息
  }
};

const handleLogout = () => {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    confirmColor: '#FF9A9E',
    success: (res) => {
      if (res.confirm) {
        // 清除本地缓存
        uni.removeStorageSync('token');
        uni.removeStorageSync('userInfo');
        
        uni.showToast({
          title: '已安全退出',
          icon: 'none'
        });
        
        setTimeout(() => {
          uni.reLaunch({
            url: '/pages/login/login'
          });
        }, 800);
      }
    }
  });
};

const navigateTo = (url) => {
  uni.navigateTo({ url });
};

onMounted(() => {
  getUserInfo();
});
</script>

<style scoped>
/* Container & Background */
.dashboard-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: #fff5f7; /* Very light pink background */
}

.aurora-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.7;
  animation: float 10s infinite ease-in-out;
}

.blob-1 {
  width: 300px;
  height: 300px;
  background: #ffcdd2; /* Pink */
  top: -50px;
  left: -50px;
  animation-delay: 0s;
}

.blob-2 {
  width: 350px;
  height: 350px;
  background: #ffe0b2; /* Orange */
  top: 40%;
  right: -80px;
  animation-delay: -2s;
}

.blob-3 {
  width: 250px;
  height: 250px;
  background: #e1bee7; /* Purple */
  bottom: -50px;
  left: 20%;
  animation-delay: -4s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0, 0) scale(1); }
}

.content-wrapper {
  position: relative;
  z-index: 1;
  padding: 40px 24px;
}

/* Header */
.header {
  margin-bottom: 40px;
  animation: slideDown 0.8s ease-out;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.6);
  padding: 16px;
  border-radius: 24px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 8px 32px rgba(255, 105, 180, 0.1);
  flex: 1;
  margin-right: 16px;
}

.avatar-box {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(255, 154, 158, 0.4);
  border: 3px solid #fff;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-text {
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.welcome-text {
  font-size: 18px;
  font-weight: 700;
  color: #4a4a4a;
}

.role-badge {
  display: inline-flex;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  width: fit-content;
}

.role-badge.admin {
  background: #fff0f5;
  color: #ff6b6b;
  border: 1px solid #ffc9c9;
}

.role-badge.user {
  background: #f0f9ff;
  color: #54a0ff;
  border: 1px solid #c9e4ff;
}

/* Logout Button */
.logout-btn {
  width: 48px;
  height: 60px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:active {
  transform: scale(0.9);
  background: rgba(255, 200, 200, 0.6);
}

.logout-icon {
  font-size: 24px;
}

.logout-text {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* Sections */
.section-container {
  margin-bottom: 32px;
}

.section-header {
  margin-bottom: 16px;
  padding-left: 8px;
}

.section-title {
  font-size: 20px;
  font-weight: 800;
  color: #4a4a4a;
  letter-spacing: 0.5px;
}

/* Grid Menu */
.grid-menu {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

/* Cards */
.menu-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 28px;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  animation: slideUp 0.6s ease-out backwards;
}

/* Staggered animation delays */
.menu-card:nth-child(1) { animation-delay: 0.1s; }
.menu-card:nth-child(2) { animation-delay: 0.2s; }
.menu-card:nth-child(3) { animation-delay: 0.3s; }
.menu-card:nth-child(4) { animation-delay: 0.4s; }

.menu-card:active {
  transform: scale(0.95) translateY(2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.03);
}

/* Card Icons */
.card-icon-bg {
  width: 56px;
  height: 56px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
  transform: rotate(-5deg);
  transition: transform 0.3s ease;
}

.menu-card:hover .card-icon-bg {
  transform: rotate(5deg) scale(1.1);
}

.card-icon-bg.pink { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
.card-icon-bg.orange { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); }
.card-icon-bg.purple { background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); }
.card-icon-bg.blue { background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%); }

.card-icon {
  font-size: 28px;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #2d3436;
}

.card-desc {
  font-size: 12px;
  color: #888;
  font-weight: 500;
}

/* Animations */
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-30px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
