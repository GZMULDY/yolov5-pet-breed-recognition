<template>
  <div class="login-container">
    <!-- Dynamic Pet Background -->
    <div class="pet-bg">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
      <div class="blob blob-4"></div>
      
      <!-- Floating Paw Prints -->
      <div class="paw-print paw-1">🐾</div>
      <div class="paw-print paw-2">🐾</div>
      <div class="paw-print paw-3">🐾</div>
      <div class="paw-print paw-4">🐾</div>
    </div>

    <!-- Login/Register Card -->
    <div class="login-card">
      <div class="card-content">
        <div class="header">
          <div class="logo-container">
            <svg class="pet-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C10.3431 2 9 3.34315 9 5C9 6.65685 10.3431 8 12 8C13.6569 8 15 6.65685 15 5C15 3.34315 13.6569 2 12 2Z" fill="currentColor"/>
              <path d="M5 6C3.34315 6 2 7.34315 2 9C2 10.6569 3.34315 12 5 12C6.65685 12 8 10.6569 8 9C8 7.34315 6.65685 6 5 6Z" fill="currentColor"/>
              <path d="M19 6C17.3431 6 16 7.34315 16 9C16 10.6569 17.3431 12 19 12C20.6569 12 22 10.6569 22 9C22 7.34315 20.6569 6 19 6Z" fill="currentColor"/>
              <path d="M7.64044 14.5658C6.18222 15.0061 5.03403 16.3248 5.00164 17.848C4.9575 19.9238 6.74682 21.6881 8.82522 21.5036C10.0381 21.396 11.134 20.6861 11.75 19.645C11.8953 19.3995 12.1047 19.3995 12.25 19.645C12.866 20.6861 13.9619 21.396 15.1748 21.5036C17.2532 21.6881 19.0425 19.9238 18.9984 17.848C18.966 16.3248 17.8178 15.0061 16.3596 14.5658C14.9554 14.1419 13.4836 13.9984 12.0001 13.9996C10.5165 13.9984 9.04469 14.1419 7.64044 14.5658Z" fill="currentColor"/>
            </svg>
          </div>
          <h1 class="title">{{ isRegister ? '欢迎加入' : '宠物识别系统' }}</h1>
          <p class="subtitle">{{ isRegister ? '注册成为新铲屎官' : 'AI 智能识别 · 关爱每一个生命' }}</p>
        </div>
        
        <div class="form-group">
          <div class="input-wrapper">
            <input 
              v-model="formData.username" 
              class="input-field" 
              type="text" 
              placeholder="请输入用户名" 
              placeholder-class="input-placeholder"
            />
          </div>
          
          <div class="input-wrapper">
            <input 
              v-model="formData.password" 
              class="input-field" 
              type="password" 
              placeholder="请输入密码" 
              placeholder-class="input-placeholder"
            />
          </div>

          <!-- 注册时显示的邮箱输入框 -->
          <div class="input-wrapper" v-if="isRegister">
            <input 
              v-model="formData.email" 
              class="input-field" 
              type="text" 
              placeholder="请输入邮箱" 
              placeholder-class="input-placeholder"
            />
          </div>

          <!-- 注册时的邮箱验证码 -->
          <div class="input-wrapper captcha-wrapper" v-if="isRegister">
            <input 
              v-model="formData.emailCode" 
              class="input-field captcha-input" 
              type="text" 
              placeholder="邮箱验证码" 
              placeholder-class="input-placeholder"
            />
            <button 
              class="send-code-btn" 
              :disabled="countdown > 0 || !formData.email" 
              @click="sendEmailCode"
            >
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </button>
          </div>

          <!-- 登录时显示的图形验证码 -->
          <div class="input-wrapper captcha-wrapper" v-if="!isRegister">
            <input 
              v-model="formData.captchaCode" 
              class="input-field captcha-input" 
              type="text" 
              placeholder="验证码" 
              placeholder-class="input-placeholder"
            />
            <div class="captcha-img-box" @click="refreshCaptcha">
              <img :src="captchaUrl" class="captcha-img" alt="验证码" />
            </div>
          </div>
        </div>
        
        <button 
          class="login-btn" 
          :class="{ 'btn-loading': loading }" 
          @click="handleSubmit" 
          :disabled="loading"
        >
          <span v-if="loading" class="spinner"></span>
          <span v-else>{{ isRegister ? '立即注册' : '立即登录' }}</span>
        </button>

        <div class="toggle-mode" @click="toggleMode">
          {{ isRegister ? '已有账号？去登录' : '还没有账号？去注册' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, getCurrentInstance } from 'vue';
import { login, register, sendEmailCode as apiSendEmailCode, verifyEmailCode } from '@/api/auth';

const { proxy } = getCurrentInstance();
const uni = proxy.uni;

const isRegister = ref(false);
const formData = reactive({
  username: '',
  password: '',
  email: '',
  captchaCode: '',
  emailCode: ''
});

const captchaUrl = ref('');
const captchaKey = ref('');
const loading = ref(false);
const countdown = ref(0);
const isEmailVerified = ref(false);

const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

const refreshCaptcha = () => {
  const key = generateUUID();
  captchaKey.value = key;
  // 添加时间戳防止缓存
  captchaUrl.value = `http://127.0.0.1:8000/api/v1/captcha/${key}?t=${new Date().getTime()}`;
};

const toggleMode = () => {
  isRegister.value = !isRegister.value;
  // 清空表单
  formData.username = '';
  formData.password = '';
  formData.email = '';
  formData.captchaCode = '';
  formData.emailCode = '';
  isEmailVerified.value = false;
  
  if (!isRegister.value) {
    refreshCaptcha();
  }
};

const sendEmailCode = async () => {
  if (!formData.email) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' });
    return;
  }
  // 简单的邮箱格式验证
  if (!/^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/.test(formData.email)) {
    uni.showToast({ title: '邮箱格式不正确', icon: 'none' });
    return;
  }

  try {
    uni.showLoading({ title: '发送中...' });
    await apiSendEmailCode(formData.email);
    uni.hideLoading();
    uni.showToast({ title: '验证码已发送', icon: 'success' });
    
    // 倒计时
    countdown.value = 60;
    const timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0) {
        clearInterval(timer);
      }
    }, 1000);
  } catch (e) {
    uni.hideLoading();
    console.error(e);
    // 错误处理已在 request.js 中
  }
};

const handleSubmit = async () => {
  if (!formData.username || !formData.password) {
    uni.showToast({ title: '请输入用户名和密码', icon: 'none' });
    return;
  }

  loading.value = true;
  try {
    if (isRegister.value) {
      // 注册流程
      if (!formData.email || !formData.emailCode) {
        uni.showToast({ title: '请完成邮箱验证', icon: 'none' });
        loading.value = false;
        return;
      }

      // 先验证邮箱验证码
      try {
        await verifyEmailCode(formData.email, formData.emailCode);
      } catch (e) {
        loading.value = false;
        return; // 验证失败，停止注册
      }

      const res = await register(formData.username, formData.password, formData.email);
      // 统一响应格式: res.data 包含实际数据
      if (res && res.data && res.data.id) {
        uni.showToast({ title: '注册成功，请登录', icon: 'success' });
        setTimeout(() => { toggleMode(); }, 1500);
      } else {
        uni.showToast({ title: '注册失败', icon: 'none' });
      }
    } else {
      // 登录流程
      if (!formData.captchaCode) {
        uni.showToast({ title: '请输入验证码', icon: 'none' });
        loading.value = false;
        return;
      }

      // 使用封装的 login 方法，传入验证码参数
      const loginRes = await login(formData.username, formData.password, captchaKey.value, formData.captchaCode);
      
      // 统一响应格式: loginRes.data 包含 token 和用户信息
      if (loginRes && loginRes.data && loginRes.data.access_token) {
        uni.setStorageSync('token', loginRes.data.access_token);
        uni.showToast({ title: '登录成功', icon: 'success' });
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/dashboard/dashboard' });
        }, 1000);
      } else {
        uni.showToast({ title: '登录失败', icon: 'none' });
        refreshCaptcha(); // 失败刷新验证码
      }
    }
  } catch (error) {
    console.error('Auth error:', error);
    // 错误已在 request.js 中统一处理并显示 toast，这里不再重复显示
    if (!isRegister.value) {
      refreshCaptcha(); // 失败刷新验证码
    }
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  refreshCaptcha();
});
</script>

<style scoped>
/* Font & Layout */
.login-container {
  position: relative;
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #fdf6e3;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif;
}

/* Dynamic Pet Background (Same as before) */
.pet-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; overflow: hidden; }
.blob { position: absolute; border-radius: 50%; filter: blur(60px); opacity: 0.7; animation: float 20s infinite ease-in-out alternate; }
.blob-1 { width: 450px; height: 450px; background: radial-gradient(circle, #ff9a9e 0%, #fecfef 100%); top: -100px; left: -50px; animation-duration: 25s; }
.blob-2 { width: 400px; height: 400px; background: radial-gradient(circle, #a18cd1 0%, #fbc2eb 100%); bottom: -50px; right: -100px; animation-duration: 30s; animation-direction: alternate-reverse; }
.blob-3 { width: 350px; height: 350px; background: radial-gradient(circle, #ffd194 0%, #70e1f5 100%); top: 40%; left: 30%; animation-duration: 22s; opacity: 0.6; }
.blob-4 { width: 250px; height: 250px; background: #84fab0; bottom: 20%; left: 10%; filter: blur(50px); animation-duration: 18s; opacity: 0.5; }
@keyframes float { 0% { transform: translate(0, 0) rotate(0deg); } 50% { transform: translate(30px, 50px) rotate(10deg); } 100% { transform: translate(-20px, 20px) rotate(-10deg); } }

.paw-print { position: absolute; font-size: 40px; opacity: 0.15; color: #ff9a9e; animation: floatPaw 15s infinite linear; user-select: none; }
.paw-1 { top: 15%; left: 10%; animation-duration: 12s; transform: rotate(-20deg); }
.paw-2 { top: 75%; left: 15%; animation-duration: 18s; transform: rotate(10deg); }
.paw-3 { top: 20%; right: 15%; animation-duration: 15s; transform: rotate(15deg); }
.paw-4 { bottom: 10%; right: 25%; animation-duration: 20s; transform: rotate(-10deg); }
@keyframes floatPaw { 0% { transform: translateY(0) rotate(0deg) scale(1); opacity: 0.1; } 50% { transform: translateY(-20px) rotate(10deg) scale(1.1); opacity: 0.2; } 100% { transform: translateY(0) rotate(0deg) scale(1); opacity: 0.1; } }

/* Glassmorphism Card */
.login-card {
  position: relative;
  z-index: 10;
  width: 90%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(25px) saturate(180%);
  border-radius: 30px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.1), 0 10px 20px rgba(0, 0, 0, 0.05), inset 0 0 0 1px rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.6);
  overflow: hidden;
  animation: floatUp 1s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
  opacity: 0;
  transform: translateY(30px);
}
@keyframes floatUp { to { opacity: 1; transform: translateY(0); } }

.card-content { padding: 50px 36px; }

.header { text-align: center; margin-bottom: 40px; }
.logo-container { display: inline-flex; justify-content: center; align-items: center; width: 64px; height: 64px; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); border-radius: 20px; margin-bottom: 16px; box-shadow: 0 8px 16px rgba(255, 154, 158, 0.3); color: white; }
.pet-icon { width: 36px; height: 36px; }
.title { font-size: 26px; font-weight: 700; color: #333; margin-bottom: 8px; }
.subtitle { font-size: 14px; color: #888; font-weight: 500; }

.form-group { margin-bottom: 32px; }
.input-wrapper { margin-bottom: 20px; }
.input-field { width: 100%; height: 56px; background: rgba(255, 255, 255, 0.9); border: 2px solid transparent; border-radius: 16px; padding: 0 20px; font-size: 16px; color: #333; box-sizing: border-box; transition: all 0.3s ease; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02); }
.input-field:focus { background: #ffffff; border-color: #ff9a9e; box-shadow: 0 0 0 4px rgba(255, 154, 158, 0.15); }

/* Captcha Style */
.captcha-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}
.captcha-input {
  flex: 1;
}
.captcha-img-box {
  width: 150px;
  height: 50px;
  border-radius: 12px;
  overflow: hidden;
  background: #f0f0f0;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.captcha-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.send-code-btn {
  width: 120px;
  height: 56px;
  background: #fff0f5;
  color: #ff9a9e;
  font-size: 14px;
  font-weight: 600;
  border-radius: 16px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}
.send-code-btn:disabled {
  background: #f5f5f7;
  color: #bbb;
  cursor: not-allowed;
}

.login-btn { width: 100%; height: 56px; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #ffffff; font-size: 18px; font-weight: 600; border-radius: 16px; border: none; cursor: pointer; transition: all 0.3s ease; display: flex; justify-content: center; align-items: center; box-shadow: 0 10px 20px rgba(255, 154, 158, 0.3); }
.login-btn:hover { transform: translateY(-2px); box-shadow: 0 15px 25px rgba(255, 154, 158, 0.4); }
.login-btn:active { transform: scale(0.98); }
.login-btn:disabled { background: #d1d1d6; cursor: not-allowed; transform: none; }

.spinner { width: 24px; height: 24px; border: 3px solid rgba(255, 255, 255, 0.3); border-top-color: #ffffff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Toggle Mode Link */
.toggle-mode {
  text-align: center;
  margin-top: 24px;
  color: #888;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s;
}
.toggle-mode:hover { color: #ff9a9e; text-decoration: underline; }
</style>
