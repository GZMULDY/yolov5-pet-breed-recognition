<template>
  <Teleport to="body">
    <Transition name="toast-fade">
      <div v-if="visible" class="custom-toast-overlay" @click="handleOverlayClick">
        <div class="custom-toast-box" :class="toastType" @click.stop>
          <div class="toast-icon">
            <span v-if="toastType === 'success'">✓</span>
            <span v-else-if="toastType === 'error'">✕</span>
            <span v-else-if="toastType === 'warning'">⚠</span>
            <span v-else-if="toastType === 'info'">ℹ</span>
          </div>
          <div class="toast-content">
            <div class="toast-title">{{ title }}</div>
            <div v-if="message" class="toast-message">{{ message }}</div>
          </div>
          <div class="toast-close" @click="close">✕</div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
  },
  duration: {
    type: Number,
    default: 3000
  },
  closeOnOverlay: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['close']);

const toastType = ref(props.type);

watch(() => props.type, (newType) => {
  toastType.value = newType;
});

watch(() => props.visible, (newVal) => {
  if (newVal && props.duration > 0) {
    setTimeout(() => {
      close();
    }, props.duration);
  }
});

const close = () => {
  emit('close');
};

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    close();
  }
};
</script>

<style scoped>
.custom-toast-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.custom-toast-box {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  min-width: 280px;
  max-width: 360px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.custom-toast-box.success {
  border-left: 4px solid #52c41a;
}

.custom-toast-box.error {
  border-left: 4px solid #ff4d4f;
}

.custom-toast-box.warning {
  border-left: 4px solid #faad14;
}

.custom-toast-box.info {
  border-left: 4px solid #1890ff;
}

.toast-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  flex-shrink: 0;
}

.success .toast-icon {
  background: #f6ffed;
  color: #52c41a;
}

.error .toast-icon {
  background: #fff2f0;
  color: #ff4d4f;
}

.warning .toast-icon {
  background: #fffbe6;
  color: #faad14;
}

.info .toast-icon {
  background: #e6f7ff;
  color: #1890ff;
}

.toast-content {
  flex: 1;
}

.toast-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.toast-message {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.toast-close {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  cursor: pointer;
  font-size: 14px;
  flex-shrink: 0;
}

.toast-close:hover {
  color: #666;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.3s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
}
</style>