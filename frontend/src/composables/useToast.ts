import { ref } from 'vue';

export interface Toast {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

const toasts = ref<Toast[]>([]);

export function useToast() {
  function showToast(message: string, type: Toast['type'] = 'info', durationMs = 4000) {
    const id = Math.random().toString(36).substring(2, 9);
    toasts.value.push({ id, type, message });

    setTimeout(() => {
      removeToast(id);
    }, durationMs);
  }

  function removeToast(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  return {
    toasts,
    showToast,
    removeToast,
  };
}
