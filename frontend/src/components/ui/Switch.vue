<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next';
import { cn } from '@/lib/utils';

interface Props {
  checked: boolean;
  pending?: boolean;
  disabled?: boolean;
  label?: string;
  class?: string;
}

const props = withDefaults(defineProps<Props>(), {
  pending: false,
  disabled: false,
});

const emit = defineEmits<{
  (e: 'toggle'): void;
}>();

function handleClick() {
  if (props.disabled || props.pending) return;
  emit('toggle');
}
</script>

<template>
  <div class="flex items-center space-x-3" :class="props.class">
    <button
      type="button"
      role="switch"
      :aria-checked="checked"
      :disabled="disabled || pending"
      @click="handleClick"
      :class="cn(
        'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2',
        checked ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700',
        (disabled || pending) && 'cursor-not-allowed opacity-75'
      )"
    >
      <span class="sr-only">{{ label || 'Toggle switch' }}</span>
      <span
        :class="cn(
          'pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out flex items-center justify-center',
          checked ? 'translate-x-5' : 'translate-x-0'
        )"
      >
        <Loader2 v-if="pending" class="h-3 w-3 animate-spin text-indigo-600" />
      </span>
    </button>
    <span v-if="label" class="text-sm font-medium text-slate-900 dark:text-slate-100">
      {{ label }}
    </span>
  </div>
</template>
