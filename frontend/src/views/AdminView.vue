<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAdminStore } from '@/stores/admin';
import { useToast } from '@/composables/useToast';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Badge from '@/components/ui/Badge.vue';
import Input from '@/components/ui/Input.vue';
import { Shield, Server, Activity, UserPlus, CheckCircle2, RefreshCw, Lock, Zap, Droplet, Wind } from 'lucide-vue-next';

const { t } = useI18n();
const adminStore = useAdminStore();
const { showToast } = useToast();

const testEmail = ref(`landlord_${Math.floor(1000 + Math.random() * 9000)}@smartrent.io`);
const testPassword = ref('SecretPass123!');
const testName = ref('Alex Landlord');
const seedProperty = ref(true);

onMounted(() => {
  adminStore.fetchStatus();
});

async function handleCreateUser() {
  if (!testEmail.value || !testPassword.value) return;
  try {
    await adminStore.createTestUser({
      email: testEmail.value,
      password: testPassword.value,
      name: testName.value,
      seed_property: seedProperty.value,
    });
    showToast(t('admin.userCreated'), 'success');
    // Generate next email placeholder
    testEmail.value = `landlord_${Math.floor(1000 + Math.random() * 9000)}@smartrent.io`;
  } catch (err: any) {
    showToast(err.message || t('common.error'), 'error');
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
          <Shield class="h-6 w-6" />
        </div>
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {{ t('admin.title') }}
          </h1>
          <p class="text-xs text-slate-500 mt-0.5">
            SuperAdmin & Infrastructure Management
          </p>
        </div>
      </div>

      <Button variant="outline" size="sm" :loading="adminStore.loading" @click="adminStore.fetchStatus">
        <RefreshCw class="h-4 w-4 mr-1.5" />
        {{ t('common.refresh') }}
      </Button>
    </div>

    <!-- Health Metrics Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card>
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">{{ t('admin.backendStatus') }}</span>
          <Server class="h-5 w-5 text-slate-400" />
        </div>
        <div class="mt-4 flex items-center space-x-2">
          <Badge :variant="adminStore.status?.status === 'healthy' ? 'success' : 'danger'">
            {{ adminStore.status?.status?.toUpperCase() || 'OFFLINE' }}
          </Badge>
          <span class="text-xs text-slate-400 font-mono">FastAPI</span>
        </div>
      </Card>

      <Card>
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">{{ t('admin.mqttStatus') }}</span>
          <Activity class="h-5 w-5 text-slate-400" />
        </div>
        <div class="mt-4 flex items-center space-x-2">
          <Badge :variant="adminStore.status?.mqtt_connected ? 'success' : 'warning'">
            {{ adminStore.status?.mqtt_connected ? 'CONNECTED (QoS 1)' : 'RECONNECTING' }}
          </Badge>
          <span class="text-xs text-slate-400 font-mono">Mosquitto</span>
        </div>
      </Card>

      <Card>
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Environment</span>
          <Shield class="h-5 w-5 text-slate-400" />
        </div>
        <div class="mt-4 flex items-center space-x-2">
          <Badge variant="info">
            {{ (adminStore.status?.environment || 'dev').toUpperCase() }}
          </Badge>
          <span class="text-xs text-slate-400 font-mono">Supabase RLS Active</span>
        </div>
      </Card>
    </div>

    <!-- User Provisioning Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Form to Create User -->
      <Card class="space-y-6">
        <div>
          <div class="flex items-center space-x-2">
            <UserPlus class="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">
              {{ t('admin.createTestUser') }}
            </h2>
          </div>
          <p class="text-xs text-slate-500 mt-1">
            Instantly create a pre-verified test tenant account without email confirmation required.
          </p>
        </div>

        <form @submit.prevent="handleCreateUser" class="space-y-4">
          <Input
            id="testName"
            v-model="testName"
            label="Landlord Full Name"
            placeholder="e.g. Maria Gonzalez"
            required
          />

          <Input
            id="testEmail"
            v-model="testEmail"
            type="email"
            :label="t('admin.testUserEmail')"
            placeholder="maria@smartrent.io"
            required
          />

          <Input
            id="testPass"
            v-model="testPassword"
            type="text"
            :label="t('admin.testUserPass')"
            required
          />

          <div class="flex items-center space-x-2 pt-1">
            <input
              id="seedCheck"
              type="checkbox"
              v-model="seedProperty"
              class="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label for="seedCheck" class="text-xs text-slate-700 dark:text-slate-300 font-medium cursor-pointer">
              {{ t('admin.seedProperty') }}
            </label>
          </div>

          <Button
            type="submit"
            class="w-full"
            :loading="adminStore.creatingUser"
          >
            <UserPlus class="h-4 w-4 mr-2" />
            {{ t('admin.generate') }}
          </Button>
        </form>
      </Card>

      <!-- Last Created User Result / Quick Login Info -->
      <Card class="space-y-4 flex flex-col justify-between">
        <div>
          <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center">
            <CheckCircle2 class="h-5 w-5 text-emerald-500 mr-2" />
            Provisioning Output
          </h2>
          <p class="text-xs text-slate-500 mt-1">
            Details of the most recently created test account.
          </p>

          <div v-if="adminStore.lastCreatedUser" class="mt-4 space-y-3">
            <div class="p-3.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-xs space-y-1 font-mono">
              <div><strong class="text-slate-700 dark:text-slate-300">Email:</strong> {{ adminStore.lastCreatedUser.user.email }}</div>
              <div><strong class="text-slate-700 dark:text-slate-300">User ID:</strong> {{ adminStore.lastCreatedUser.user.id }}</div>
              <div v-if="adminStore.lastCreatedUser.seeded_property">
                <strong class="text-slate-700 dark:text-slate-300">Seeded Property:</strong> {{ adminStore.lastCreatedUser.seeded_property.property.name }}
              </div>
            </div>

            <div v-if="adminStore.lastCreatedUser.seeded_property" class="space-y-2">
              <h4 class="text-xs font-semibold uppercase text-slate-500">Seeded IoT Devices (4)</h4>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div class="p-2 rounded bg-slate-50 dark:bg-slate-800 flex items-center space-x-2">
                  <Lock class="h-3.5 w-3.5 text-indigo-500" />
                  <span>Smart Lock</span>
                </div>
                <div class="p-2 rounded bg-slate-50 dark:bg-slate-800 flex items-center space-x-2">
                  <Zap class="h-3.5 w-3.5 text-amber-500" />
                  <span>Relay Light</span>
                </div>
                <div class="p-2 rounded bg-slate-50 dark:bg-slate-800 flex items-center space-x-2">
                  <Droplet class="h-3.5 w-3.5 text-sky-500" />
                  <span>Water Valve</span>
                </div>
                <div class="p-2 rounded bg-slate-50 dark:bg-slate-800 flex items-center space-x-2">
                  <Wind class="h-3.5 w-3.5 text-teal-500" />
                  <span>Climate AC</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-12 text-slate-400 text-xs">
            No test users created in this session yet. Use the form to spin one up!
          </div>
        </div>

        <div class="pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500">
          💡 You can sign out and immediately log in with the generated email and password to test the tenant experience!
        </div>
      </Card>
    </div>
  </div>
</template>
