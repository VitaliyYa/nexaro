<script setup lang="ts">
import { X } from 'lucide-vue-next';

interface Props {
  open: boolean;
  title: string;
}

defineProps<Props>();
const emit = defineEmits<{
  (e: 'close'): void;
}>();
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
    <div class="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900">
      <div class="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
        <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">{{ title }}</h3>
        <button
          @click="emit('close')"
          class="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-500 dark:hover:bg-slate-800"
        >
          <X class="h-5 w-5" />
        </button>
      </div>
      <div class="mt-4">
        <slot />
      </div>
    </div>
  </div>
</template>
