<script setup lang="ts">
import { useToast } from '@/composables/useToast';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-vue-next';
import { cn } from '@/lib/utils';

const { toasts, removeToast } = useToast();
</script>

<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none">
    <div
      v-for="t in toasts"
      :key="t.id"
      :class="cn(
        'pointer-events-auto flex items-center justify-between p-4 rounded-lg shadow-lg text-sm border transition-all duration-200',
        t.type === 'error' && 'bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950 dark:border-rose-900 dark:text-rose-200',
        t.type === 'success' && 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950 dark:border-emerald-900 dark:text-emerald-200',
        t.type === 'warning' && 'bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950 dark:border-amber-900 dark:text-amber-200',
        t.type === 'info' && 'bg-sky-50 border-sky-200 text-sky-800 dark:bg-sky-950 dark:border-sky-900 dark:text-sky-200'
      )"
    >
      <div class="flex items-center space-x-3">
        <AlertCircle v-if="t.type === 'error' || t.type === 'warning'" class="h-5 w-5 shrink-0" />
        <CheckCircle2 v-else-if="t.type === 'success'" class="h-5 w-5 shrink-0" />
        <Info v-else class="h-5 w-5 shrink-0" />
        <span>{{ t.message }}</span>
      </div>
      <button @click="removeToast(t.id)" class="ml-3 p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/5">
        <X class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
