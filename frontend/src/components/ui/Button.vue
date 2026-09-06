<script setup lang="ts">
import { computed } from 'vue';
import { Loader2 } from 'lucide-vue-next';
import { cn } from '@/lib/utils';

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false,
  type: 'button',
});

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'secondary':
      return 'bg-slate-200 text-slate-800 hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700';
    case 'danger':
      return 'bg-rose-600 text-white hover:bg-rose-700 shadow-sm focus-visible:ring-rose-500';
    case 'outline':
      return 'border border-slate-300 bg-transparent hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200';
    case 'ghost':
      return 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300';
    case 'primary':
    default:
      return 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm focus-visible:ring-indigo-500';
  }
});

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-8 px-3 text-xs rounded-md';
    case 'lg':
      return 'h-12 px-6 text-base rounded-lg';
    case 'md':
    default:
      return 'h-10 px-4 text-sm rounded-md';
  }
});
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="cn(
      'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none cursor-pointer',
      variantClasses,
      sizeClasses,
      props.class
    )"
  >
    <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
    <slot />
  </button>
</template>
