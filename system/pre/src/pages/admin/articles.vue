<template>
  <div class="page-container aurora-bg">
    <div class="content-wrapper">
      <div class="header">
        <div class="title">
          <span class="emoji">📰</span>
          <span class="text-gradient">百科管理</span>
        </div>
        <button class="action-btn" @click="openAddModal">
          <span class="btn-icon">✏️</span> 发布文章
        </button>
      </div>

      <div class="article-list">
        <div 
          v-for="(article, index) in articles" 
          :key="article.id" 
          class="article-card glass-effect"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="article-cover" v-if="article.cover_image">
            <img :src="article.cover_image" class="cover-img" alt="封面图" />
          </div>
          <div class="article-content">
            <div class="article-title">{{ article.title }}</div>
            <div class="article-meta">
              <span class="date">📅 {{ formatDate(article.created_at) }}</span>
            </div>
            <div class="article-excerpt">{{ article.content.substring(0, 50) }}...</div>
          </div>
          <div class="actions">
            <button class="icon-btn edit" @click="editArticle(article)" title="编辑">
              ✏️
            </button>
            <button class="icon-btn delete" @click="deleteArticle(article.id)" title="删除">
              🗑️
            </button>
          </div>
        </div>
        
        <div v-if="articles.length === 0" class="empty-state">
          <span class="empty-emoji">📭</span>
          <p>还没有发布任何百科哦~</p>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal glass-effect bounce-in">
        <div class="modal-header">
          {{ isEditing ? '📝 编辑百科' : '✨ 发布新百科' }}
        </div>
        <div class="form">
          <div class="input-group">
            <span class="input-icon">📌</span>
            <input v-model="formData.title" placeholder="请输入标题" class="cute-input" />
          </div>
          <div class="input-group">
            <span class="input-icon">🖼️</span>
            <input v-model="formData.cover_image" placeholder="封面图片链接 (可选)" class="cute-input" />
          </div>
          <div class="input-group textarea-group">
            <textarea v-model="formData.content" placeholder="请输入正文内容..." class="cute-textarea"></textarea>
          </div>
        </div>
        <div class="modal-actions">
          <button class="modal-btn cancel" @click="closeModal">👋 取消</button>
          <button class="modal-btn confirm" @click="submitForm">💖 发布</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { uni } from '@/utils/uni-adapter.js';

const articles = ref([]);
const showModal = ref(false);
const isEditing = ref(false);
const editingId = ref(null);

const formData = reactive({
  title: '',
  content: '',
  cover_image: ''
});

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

const openAddModal = () => {
  isEditing.value = false;
  formData.title = '';
  formData.content = '';
  formData.cover_image = '';
  showModal.value = true;
};

const editArticle = (article) => {
  isEditing.value = true;
  editingId.value = article.id;
  formData.title = article.title;
  formData.content = article.content;
  formData.cover_image = article.cover_image || '';
  showModal.value = true;
};

const deleteArticle = async (id) => {
  const token = uni.getStorageSync('token');
  uni.showModal({
    title: '💔 确认删除',
    content: '这篇文章将被永久移除哦？',
    confirmColor: '#FF9A9E',
    success: async (res) => {
      if (res.confirm) {
        try {
          await uni.request({
            url: `${API_URL}/articles/${id}`,
            method: 'DELETE',
            header: { 'Authorization': `Bearer ${token}` }
          });
          uni.showToast({ title: '已删除 ✨' });
          fetchArticles();
        } catch (e) {
          uni.showToast({ title: '删除失败 😭', icon: 'none' });
        }
      }
    }
  });
};

const submitForm = async () => {
  if (!formData.title || !formData.content) {
    uni.showToast({ title: '标题和内容不能为空哦 🥺', icon: 'none' });
    return;
  }

  const token = uni.getStorageSync('token');
  const url = isEditing.value ? `${API_URL}/articles/${editingId.value}` : `${API_URL}/articles`;
  const method = isEditing.value ? 'PUT' : 'POST';

  try {
    const res = await uni.request({
      url,
      method,
      data: formData,
      header: { 'Authorization': `Bearer ${token}` }
    });

    if (res.statusCode === 200 || res.statusCode === 201) {
      uni.showToast({ title: isEditing.value ? '修改成功 💖' : '发布成功 🎉' });
      closeModal();
      fetchArticles();
    } else {
      uni.showToast({ title: '操作失败 🥺', icon: 'none' });
    }
  } catch (e) {
    // 错误已在 request.js 中统一处理
  }
};

const closeModal = () => {
  showModal.value = false;
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
/* Inherit Aurora Background & Common Styles from Admin Users Page */
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

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
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

.action-btn {
  background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 50px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(102, 166, 255, 0.4);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 12px 25px rgba(102, 166, 255, 0.5);
}

/* Article List */
.article-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

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
  position: relative;
  overflow: hidden;
}

.article-card:hover {
  transform: translateY(-3px);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 15px 35px rgba(102, 166, 255, 0.15);
}

.article-cover {
  width: 80px;
  height: 80px;
  border-radius: 16px;
  overflow: hidden;
  margin-right: 16px;
  flex-shrink: 0;
  background-color: #f0f0f5;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.article-content {
  flex: 1;
  min-width: 0; /* Fix flex text overflow */
}

.article-title {
  font-size: 18px;
  font-weight: 700;
  color: #2d3436;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-left: 12px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.5);
}

.icon-btn:hover { transform: scale(1.1); background: white; }

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #888;
}

.empty-emoji {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(230, 240, 255, 0.4);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  width: 90%;
  max-width: 500px;
  border-radius: 32px;
  padding: 30px;
  border: 2px solid rgba(255, 255, 255, 0.8);
}

.bounce-in {
  animation: bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.modal-header {
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 25px;
  text-align: center;
  background: linear-gradient(45deg, #89f7fe, #66a6ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-group {
  position: relative;
  display: flex;
  align-items: center;
}

.textarea-group {
  align-items: flex-start;
}

.input-icon {
  position: absolute;
  left: 14px;
  z-index: 1;
  font-size: 16px;
  top: 14px;
}

.cute-input, .cute-textarea {
  width: 100%;
  padding: 14px 14px 14px 44px;
  background: rgba(255, 255, 255, 0.6);
  border: 2px solid transparent;
  border-radius: 20px;
  font-size: 15px;
  color: #555;
  transition: all 0.3s;
  box-sizing: border-box;
  font-family: inherit;
}

.cute-textarea {
  min-height: 120px;
  resize: none;
}

.cute-input:focus, .cute-textarea:focus {
  outline: none;
  background: white;
  border-color: #89f7fe;
  box-shadow: 0 0 0 4px rgba(137, 247, 254, 0.2);
}

.modal-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
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

.modal-btn.cancel { background: #f0f0f5; color: #888; }
.modal-btn.confirm {
  background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);
  color: white;
  box-shadow: 0 8px 20px rgba(102, 166, 255, 0.3);
}

.modal-btn.confirm:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 25px rgba(102, 166, 255, 0.4);
}

/* Animations */
@keyframes slideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes bounceIn {
  0% { transform: scale(0.3); opacity: 0; }
  50% { transform: scale(1.05); opacity: 1; }
  70% { transform: scale(0.9); }
  100% { transform: scale(1); }
}
</style>
