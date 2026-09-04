<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { switchLanguage, type SupportedLocale } from '@/i18n';
import { Globe } from 'lucide-vue-next';

const { locale } = useI18n();

const languages: { code: SupportedLocale; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'ru', label: 'Русский' },
  { code: 'ka', label: 'ქართული' },
  { code: 'he', label: 'עברית' },
];

function handleChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  switchLanguage(target.value as SupportedLocale);
}
</script>

<template>
  <div class="flex items-center space-x-1.5 text-sm">
    <Globe class="h-4 w-4 text-slate-500" />
    <select
      :value="locale"
      @change="handleChange"
      class="bg-transparent text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none cursor-pointer rounded py-1 px-1.5 border border-slate-200 dark:border-slate-800"
    >
      <option v-for="lang in languages" :key="lang.code" :value="lang.code" class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200">
        {{ lang.label }}
      </option>
    </select>
  </div>
</template>
