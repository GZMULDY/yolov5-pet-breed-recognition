<template>
  <div class="page-container aurora-bg">
    <div class="content-wrapper">
      <div v-if="article" class="article-detail">
        <div class="header">
          <h1 class="title">{{ article.title }}</h1>
          <div class="meta">
            <span class="date">📅 {{ formatDate(article.created_at) }}</span>
            <span class="author">👤 {{ article.author_id }}</span>
          </div>
        </div>

        <div v-if="article.cover_image" class="cover-image-box">
          <img :src="article.cover_image" class="cover-image" alt="封面图" />
        </div>

        <div class="content glass-effect">
          <p class="content-text">{{ article.content }}</p>
        </div>
      </div>
      <div v-else class="loading-state">
        <div class="spinner"></div>
        <p>正在加载精彩内容...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { uni } from '@/utils/uni-adapter.js';

const article = ref(null);
import { BASE_URL } from '@/utils/request.js';
const API_URL = BASE_URL;

// 从 URL 参数获取文章 ID
const urlParams = new URLSearchParams(window.location.search);
const articleId = urlParams.get('id');

onMounted(() => {
  if (articleId) {
    fetchArticleDetail(articleId);
  }
});

const fetchArticleDetail = async (id) => {
  const token = uni.getStorageSync('token');
  try {
    const res = await uni.request({
      url: `${API_URL}/articles/${id}`,
      header: { 'Authorization': `Bearer ${token}` }
    });
    if (res.statusCode === 200) {
      article.value = res.data?.data || res.data;
    } else {
      uni.showToast({ title: '文章不存在', icon: 'none' });
    }
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' });
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};
</script>

<style scoped>
/* Inherit Aurora Background */
.aurora-bg {
  background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #ffd1ff, #a18cd1);
  background-size: 400% 400%;
  animation: aurora 15s ease infinite;
  min-height: 100vh;
}

@keyframes aurora {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.page-container {
  padding: 20px;
  font-family: 'Nunito', 'Rounded Mplus 1c', 'PingFang SC', sans-serif;
}

.content-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.header {
  margin-bottom: 24px;
  text-align: center;
}

.title {
  font-size: 24px;
  font-weight: 800;
  color: #2d3436;
  margin-bottom: 12px;
  line-height: 1.4;
}

.meta {
  font-size: 13px;
  color: #888;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.cover-image-box {
  margin-bottom: 24px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.cover-image {
  width: 100%;
  display: block;
}

.glass-effect {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05);
}

.content-text {
  font-size: 16px;
  color: #4a4a4a;
  line-height: 1.8;
  white-space: pre-wrap;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  color: #888;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ff9a9e;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
