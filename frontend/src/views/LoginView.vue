<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { useToast } from '@/composables/useToast';
import Card from '@/components/ui/Card.vue';
import Input from '@/components/ui/Input.vue';
import Button from '@/components/ui/Button.vue';
import { Cpu } from 'lucide-vue-next';

const router = useRouter();
const { t } = useI18n();
const authStore = useAuthStore();
const { showToast } = useToast();

const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

async function handleLogin() {
  if (!email.value || !password.value) return;
  loading.value = true;
  error.value = '';

  try {
    await authStore.signIn(email.value, password.value);
    showToast(t('common.success'), 'success');
    router.push('/properties');
  } catch (err: any) {
    error.value = err.message || t('auth.invalidCredentials');
    showToast(error.value, 'error');
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-[85vh] flex items-center justify-center px-4 sm:px-6 lg:px-8">
    <div class="w-full max-w-md space-y-8">
      <div class="text-center">
        <div class="inline-flex p-3 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 mb-4">
          <Cpu class="h-10 w-10" />
        </div>
        <h2 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          {{ t('auth.signInTitle') }}
        </h2>
        <p class="mt-2 text-sm text-slate-500">
          {{ t('auth.signInSubtitle') }}
        </p>
      </div>

      <Card>
        <form @submit.prevent="handleLogin" class="space-y-4">
          <Input
            id="email"
            v-model="email"
            type="email"
            :label="t('auth.email')"
            placeholder="admin@smartrent.io"
            required
          />

          <Input
            id="password"
            v-model="password"
            type="password"
            :label="t('auth.password')"
            placeholder="••••••••"
            required
          />

          <p v-if="error" class="text-xs text-rose-500 font-medium">
            {{ error }}
          </p>

          <Button
            type="submit"
            class="w-full"
            :loading="loading"
          >
            {{ loading ? t('auth.signingIn') : t('auth.login') }}
          </Button>
        </form>
      </Card>
    </div>
  </div>
</template>
