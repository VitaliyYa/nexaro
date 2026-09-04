<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import LanguageSwitcher from './LanguageSwitcher.vue';
import { Building2, Shield, LogOut, Cpu } from 'lucide-vue-next';

const authStore = useAuthStore();
const router = useRouter();
const { t } = useI18n();

async function handleLogout() {
  await authStore.signOut();
  router.push('/login');
}
</script>

<template>
  <header class="border-b border-slate-200 bg-white/80 backdrop-blur-md sticky top-0 z-40 dark:border-slate-800 dark:bg-slate-900/80">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-6">
        <router-link to="/" class="flex items-center space-x-2.5 font-bold text-indigo-600 dark:text-indigo-400">
          <div class="p-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/50">
            <Cpu class="h-6 w-6" />
          </div>
          <span class="text-lg tracking-tight">{{ t('common.appName') }}</span>
        </router-link>

        <nav v-if="authStore.isAuthenticated" class="hidden md:flex items-center space-x-1">
          <router-link
            to="/properties"
            active-class="bg-slate-100 text-indigo-600 dark:bg-slate-800 dark:text-indigo-400"
            class="flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800"
          >
            <Building2 class="h-4 w-4" />
            <span>{{ t('nav.properties') }}</span>
          </router-link>

          <router-link
            v-if="authStore.isSuperAdmin"
            to="/admin"
            active-class="bg-slate-100 text-indigo-600 dark:bg-slate-800 dark:text-indigo-400"
            class="flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800"
          >
            <Shield class="h-4 w-4" />
            <span>{{ t('nav.admin') }}</span>
          </router-link>
        </nav>
      </div>

      <div class="flex items-center space-x-4">
        <LanguageSwitcher />

        <div v-if="authStore.isAuthenticated" class="flex items-center space-x-3">
          <span class="text-xs text-slate-500 hidden sm:inline-block max-w-[150px] truncate">
            {{ authStore.user?.email }}
          </span>
          <button
            @click="handleLogout"
            class="p-2 rounded-md text-slate-500 hover:text-rose-600 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
            :title="t('common.logout')"
          >
            <LogOut class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
