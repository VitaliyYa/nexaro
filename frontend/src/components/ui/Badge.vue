<script setup lang="ts">
import { computed } from 'vue';
import { cn } from '@/lib/utils';

interface Props {
  variant?: 'success' | 'warning' | 'danger' | 'neutral' | 'info';
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'neutral',
});

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20 dark:bg-emerald-950/50 dark:text-emerald-300';
    case 'warning':
      return 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20 dark:bg-amber-950/50 dark:text-amber-300';
    case 'danger':
      return 'bg-rose-50 text-rose-700 ring-1 ring-rose-600/20 dark:bg-rose-950/50 dark:text-rose-300';
    case 'info':
      return 'bg-sky-50 text-sky-700 ring-1 ring-sky-600/20 dark:bg-sky-950/50 dark:text-sky-300';
    case 'neutral':
    default:
      return 'bg-slate-100 text-slate-700 ring-1 ring-slate-600/10 dark:bg-slate-800 dark:text-slate-300';
  }
});
</script>

<template>
  <span
    :class="cn(
      'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-inset',
      variantClasses,
      props.class
    )"
  >
    <slot />
  </span>
</template>
