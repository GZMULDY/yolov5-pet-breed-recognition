<template>
  <div class="page-container aurora-bg">
    <div class="content-wrapper">
      <div class="header">
        <div class="title">
          <span class="emoji">📖</span>
          <span class="text-gradient">宠物百科</span>
        </div>
      </div>

      <div class="article-list">
        <div 
          v-for="(article, index) in articles" 
          :key="article.id" 
          class="article-card glass-effect"
          :style="{ animationDelay: `${index * 0.1}s` }"
          @click="viewArticle(article)"
        >
          <div class="article-cover" v-if="article.cover_image">
            <img :src="article.cover_image" class="cover-img" alt="封面图" />
          </div>
          <div class="article-content">
            <div class="article-title">{{ article.title }}</div>
            <div class="article-meta">
              <span class="date">📅 {{ formatDate(article.created_at) }}</span>
            </div>
            <div class="article-excerpt">{{ article.content.substring(0, 60) }}...</div>
          </div>
        </div>
        
        <div v-if="articles.length === 0" class="empty-state">
          <span class="empty-emoji">📭</span>
          <p>暂时没有文章哦~</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { uni } from '@/utils/uni-adapter.js';

const articles = ref([]);
import { BASE_URL } from '@/utils/request.js';
const API_URL = BASE_URL;

const fetchArticles = async () => {
  const token = uni.getStorageSync('token');
  try {
    const res = await uni.request({
      url: `${API_URL}/articles`,
      header: { 'Authorization': `Bearer ${token}` }
    });
    if (res.statusCode === 200) {
      // 后端返回格式是 { code, message, data: [...], timestamp }
      const articlesData = res.data?.data || res.data;
      articles.value = articlesData;
    }
  } catch (e) {
    uni.showToast({ title: '加载失败 😭', icon: 'none' });
  }
};

const viewArticle = (article) => {
  uni.navigateTo({
    url: `/pages/articles/detail?id=${article.id}`
  });
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

onMounted(() => {
  fetchArticles();
});
</script>

<style scoped>
/* Inherit Styles */
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

.content-wrapper { max-width: 800px; margin: 0 auto; }

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
  background: linear-gradient(45deg, #f6d365, #fda085);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.emoji { font-size: 28px; }

/* Article List */
.article-list { display: flex; flex-direction: column; gap: 20px; }

.glass-effect {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05);
}

.article-card {
  padding: 20px;
  border-radius: 24px;
  display: flex;
  align-items: flex-start;
  transition: all 0.3s ease;
  animation: slideIn 0.5s ease-out backwards;
  cursor: pointer;
}

.article-card:hover {
  transform: translateY(-3px);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 15px 35px rgba(253, 160, 133, 0.2);
}

.article-cover {
  width: 90px;
  height: 90px;
  border-radius: 16px;
  overflow: hidden;
  margin-right: 16px;
  flex-shrink: 0;
  background-color: #f0f0f5;
}

.cover-img { width: 100%; height: 100%; object-fit: cover; }

.article-content { flex: 1; }

.article-title {
  font-size: 18px;
  font-weight: 700;
  color: #2d3436;
  margin-bottom: 6px;
}

.article-meta {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
}

.article-excerpt {
  font-size: 14px;
  color: #636e72;
  line-height: 1.4;
}

.empty-state { text-align: center; padding: 60px 0; color: #888; }
.empty-emoji { font-size: 48px; display: block; margin-bottom: 16px; }

@keyframes slideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
