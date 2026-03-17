import { reactive, readonly } from 'vue';

const state = reactive({
  visible: false,
  title: '',
  message: '',
  type: 'info',
  duration: 3000,
  resolve: null
});

let toastInstance = null;

export function setToastInstance(instance) {
  toastInstance = instance;
}

export function useToast() {
  const showToast = (options) => {
    const {
      title = '',
      message = '',
      type = 'info',
      duration = 3000
    } = options;

    state.title = title;
    state.message = message;
    state.type = type;
    state.duration = duration;
    state.visible = true;

    return new Promise((resolve) => {
      state.resolve = resolve;
    });
  };

  const hideToast = () => {
    state.visible = false;
    if (state.resolve) {
      state.resolve();
      state.resolve = null;
    }
  };

  const success = (title, message = '') => showToast({ title, message, type: 'success' });
  const error = (title, message = '') => showToast({ title, message, type: 'error' });
  const warning = (title, message = '') => showToast({ title, message, type: 'warning' });
  const info = (title, message = '') => showToast({ title, message, type: 'info' });

  return {
    state: readonly(state),
    showToast,
    hideToast,
    success,
    error,
    warning,
    info
  };
}

export { state as toastState };

export function hideToast() {
  state.visible = false;
  if (state.resolve) {
    state.resolve();
    state.resolve = null;
  }
}