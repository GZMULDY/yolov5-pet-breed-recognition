<template>
  <div class="page-container aurora-bg">
    <div class="content-wrapper">
      <div class="header">
        <div v-if="currentLevel > 0" class="back-btn" @click="goBack">‹</div>
        <div class="title">
          <span class="emoji">{{ currentCategory?.icon || '📚' }}</span>
          <span class="text-gradient">{{ currentCategory?.name || '宠物百科' }}</span>
        </div>
        <p class="subtitle">{{ currentLevel === 0 ? '探索你喜爱的宠物世界 🐾' : '选择分类查看详情' }}</p>
      </div>

      <div class="category-grid">
        <div 
          v-for="item in currentItems" 
          :key="item.id" 
          class="category-card glass-effect"
          @click="handleItemClick(item)"
        >
          <div class="category-icon">{{ item.icon || '🐾' }}</div>
          <div class="category-name">{{ item.name }}</div>
          <div v-if="item.children && item.children.length > 0" class="category-arrow">›</div>
        </div>
      </div>

      <div v-if="currentItems.length === 0 && !loading" class="empty-state">
        <p>暂无内容</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { uni } from '@/utils/uni-adapter.js';

const categories = ref([]);
const currentLevel = ref(0);
const currentCategory = ref(null);
const currentItems = ref([]);
const loading = ref(false);
import { BASE_URL } from '@/utils/request.js';
const API_URL = BASE_URL;

onMounted(() => {
  const needRestore = sessionStorage.getItem('encyclopedia_need_restore');
  if (needRestore === 'true') {
    const savedState = sessionStorage.getItem('encyclopedia_state');
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        currentLevel.value = state.level || 0;
        currentCategory.value = state.category || null;
        currentItems.value = state.items || [];
      } catch (e) {
        console.error('Failed to restore encyclopedia state:', e);
        fetchCategories();
      }
    }
    sessionStorage.removeItem('encyclopedia_need_restore');
    sessionStorage.removeItem('encyclopedia_state');
  } else {
    fetchCategories();
  }
});

const fetchCategories = async () => {
  try {
    const token = uni.getStorageSync('token');
    const response = await uni.request({
      url: `${API_URL}/categories`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      }
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
      // 后端返回格式是 { code, message, data: [...], timestamp }
      // 需要取 res.data.data 获取实际的分类数据
      const categoriesData = res.data?.data || res.data;
      categories.value = categoriesData;
      currentItems.value = categoriesData;
    } else if (res.statusCode === 401) {
      uni.showToast({ title: '请先登录', icon: 'none' });
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/login/login' });
      }, 1500);
    } else {
      uni.showToast({ title: '加载失败: ' + res.statusCode, icon: 'none' });
    }
  } catch (e) {
    console.error('Failed to fetch categories:', e);
    uni.showToast({ title: '加载失败: ' + e.message, icon: 'none' });
  }
};

const handleItemClick = async (item) => {
  if (item.children && item.children.length > 0) {
    currentLevel.value++;
    currentCategory.value = item;
    currentItems.value = item.children;
  } else {
    sessionStorage.setItem('encyclopedia_state', JSON.stringify({
      level: currentLevel.value,
      category: currentCategory.value,
      items: currentItems.value
    }));
    sessionStorage.setItem('encyclopedia_need_restore', 'true');
    await fetchBreedAndNavigate(item);
  }
};

const fetchBreedAndNavigate = async (category) => {
  loading.value = true;
  try {
    const token = uni.getStorageSync('token');
    const response = await uni.request({
      url: `${API_URL}/breeds?category_id=${category.id}`,
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

    if (res.statusCode === 200 && res.data) {
      // 后端返回格式是 { code, message, data: [...], timestamp }
      const breedsData = res.data?.data || res.data;
      if (breedsData && breedsData.length > 0) {
        uni.navigateTo({
          url: `/pages/pets/detail?id=${breedsData[0].id}&name=${encodeURIComponent(breedsData[0].name)}`
        });
      } else {
        uni.showToast({ title: '暂无详情', icon: 'none' });
      }
    } else {
      uni.showToast({ title: '暂无详情', icon: 'none' });
    }
  } catch (e) {
    console.error('Failed to fetch breed:', e);
    uni.showToast({ title: '加载失败', icon: 'none' });
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  if (currentLevel.value > 0) {
    currentLevel.value--;
    if (currentLevel.value === 0) {
      currentCategory.value = null;
      currentItems.value = categories.value;
    } else {
      const findParent = (items, targetId) => {
        for (const item of items) {
          if (item.id === targetId) return items;
          if (item.children) {
            const found = findParent(item.children, targetId);
            if (found) return found;
          }
        }
        return null;
      };
      const parentItems = findParent(categories.value, currentCategory.value.id);
      if (parentItems) {
        currentItems.value = parentItems;
      }
      currentCategory.value = null;
      for (const cat of categories.value) {
        if (cat.children) {
          for (const child of cat.children) {
            if (child.id === currentItems.value[0]?.parent_id) {
              currentCategory.value = cat;
              break;
            }
          }
        }
      }
    }
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
  margin-bottom: 30px;
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

.emoji { font-size: 24px; }

.subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.category-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.category-card:active {
  transform: scale(0.98);
}

.category-icon {
  font-size: 36px;
  margin-right: 16px;
}

.category-name {
  flex: 1;
  font-size: 18px;
  font-weight: 700;
  color: #2d3436;
}

.category-arrow {
  font-size: 24px;
  color: #ccc;
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
</style>