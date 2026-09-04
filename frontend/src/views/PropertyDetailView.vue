<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { usePropertiesStore } from '@/stores/properties';
import { useDevicesStore } from '@/stores/devices';
import { useToast } from '@/composables/useToast';
import { apiRequest } from '@/lib/api';
import LockCard from '@/components/devices/LockCard.vue';
import RelayCard from '@/components/devices/RelayCard.vue';
import ValveCard from '@/components/devices/ValveCard.vue';
import ClimateCard from '@/components/devices/ClimateCard.vue';
import Button from '@/components/ui/Button.vue';
import Modal from '@/components/ui/Modal.vue';
import Input from '@/components/ui/Input.vue';
import { Radio, RefreshCw, Plus, Clock, Cpu } from 'lucide-vue-next';

const route = useRoute();
const { t } = useI18n();
const propertyId = route.params.id as string;

const propertiesStore = usePropertiesStore();
const devicesStore = useDevicesStore();
const { showToast } = useToast();

const activeTab = ref<'devices' | 'timeline'>('devices');

// Add Device Modal State
const isAddDeviceOpen = ref(false);
const newDeviceId = ref('');
const newDeviceName = ref('');
const newDeviceType = ref<'lock' | 'relay' | 'valve' | 'climate'>('relay');
const addingDevice = ref(false);

onMounted(async () => {
  await propertiesStore.fetchProperty(propertyId);
  await devicesStore.initPropertyDevices(propertyId);
});

onUnmounted(() => {
  devicesStore.cleanup();
});

async function handleAddDevice() {
  if (!newDeviceId.value || !newDeviceName.value) return;
  addingDevice.value = true;
  try {
    await apiRequest(`/properties/${propertyId}/devices`, {
      method: 'POST',
      body: JSON.stringify({
        id: newDeviceId.value,
        name: newDeviceName.value,
        device_type: newDeviceType.value,
        is_active: true,
        settings: {},
      }),
    });
    showToast(t('common.success'), 'success');
    isAddDeviceOpen.value = false;
    newDeviceId.value = '';
    newDeviceName.value = '';
    await devicesStore.initPropertyDevices(propertyId);
  } catch (err: any) {
    showToast(err.message || t('common.error'), 'error');
  } finally {
    addingDevice.value = false;
  }
}

function loadTimeline() {
  devicesStore.fetchDeviceLogs(propertyId, 50);
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 dark:border-slate-800 gap-4">
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {{ propertiesStore.currentProperty?.name || t('properties.title') }}
          </h1>
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            <Radio class="h-3 w-3 mr-1 animate-pulse" />
            Live Realtime
          </span>
        </div>
        <p v-if="propertiesStore.currentProperty?.address" class="text-xs text-slate-500 mt-1">
          {{ propertiesStore.currentProperty.address }}
        </p>
      </div>

      <div class="flex items-center space-x-2">
        <Button variant="outline" size="sm" @click="isAddDeviceOpen = true">
          <Plus class="h-4 w-4 mr-1.5" />
          {{ t('common.add') }} Device
        </Button>
      </div>
    </div>

    <!-- Optimistic UI Notice -->
    <div class="p-3.5 rounded-lg bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900 text-xs text-indigo-700 dark:text-indigo-300 flex items-center">
      <Cpu class="h-4 w-4 mr-2 shrink-0" />
      <span>{{ t('devices.optimisticNote') }}</span>
    </div>

    <!-- Tabs: Devices / Timeline -->
    <div class="flex border-b border-slate-200 dark:border-slate-800 space-x-6">
      <button
        @click="activeTab = 'devices'"
        :class="[
          'pb-3 text-sm font-medium border-b-2 cursor-pointer transition-colors',
          activeTab === 'devices'
            ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
            : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300',
        ]"
      >
        {{ t('devices.title') }} ({{ devicesStore.devices.length }})
      </button>
      <button
        @click="() => { activeTab = 'timeline'; loadTimeline(); }"
        :class="[
          'pb-3 text-sm font-medium border-b-2 cursor-pointer transition-colors flex items-center',
          activeTab === 'timeline'
            ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
            : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300',
        ]"
      >
        <Clock class="h-4 w-4 mr-1.5" />
        {{ t('timeline.title') }}
      </button>
    </div>

    <!-- Tab 1: IoT Devices Grid -->
    <div v-if="activeTab === 'devices'">
      <div v-if="devicesStore.loading" class="text-center py-12 text-slate-400">
        {{ t('common.loading') }}
      </div>

      <div
        v-else-if="devicesStore.devices.length === 0"
        class="text-center py-16 px-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-800"
      >
        <Cpu class="mx-auto h-12 w-12 text-slate-400" />
        <h3 class="mt-4 text-base font-semibold text-slate-900 dark:text-slate-100">
          {{ t('devices.noDevices') }}
        </h3>
        <div class="mt-4">
          <Button size="sm" @click="isAddDeviceOpen = true">
            <Plus class="h-4 w-4 mr-1" />
            Add Device
          </Button>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <template v-for="dev in devicesStore.devices" :key="dev.id">
          <LockCard v-if="dev.device_type === 'lock'" :device="dev" />
          <RelayCard v-else-if="dev.device_type === 'relay'" :device="dev" />
          <ValveCard v-else-if="dev.device_type === 'valve'" :device="dev" />
          <ClimateCard v-else-if="dev.device_type === 'climate'" :device="dev" />
        </template>
      </div>
    </div>

    <!-- Tab 2: Activity Timeline (REST pagination) -->
    <div v-else-if="activeTab === 'timeline'" class="space-y-4">
      <div class="flex justify-end">
        <Button size="sm" variant="outline" :loading="devicesStore.logsLoading" @click="loadTimeline">
          <RefreshCw class="h-3.5 w-3.5 mr-1" />
          {{ t('common.refresh') }}
        </Button>
      </div>

      <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-sm">
          <thead class="bg-slate-50 dark:bg-slate-800/50 text-xs font-semibold text-slate-500 uppercase tracking-wider text-left">
            <tr>
              <th class="px-4 py-3">{{ t('timeline.timestamp') }}</th>
              <th class="px-4 py-3">Device ID</th>
              <th class="px-4 py-3">{{ t('timeline.event') }}</th>
              <th class="px-4 py-3">{{ t('timeline.payload') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr v-if="devicesStore.logs.length === 0">
              <td colspan="4" class="px-4 py-8 text-center text-slate-400">
                {{ t('timeline.noLogs') }}
              </td>
            </tr>
            <tr v-for="log in devicesStore.logs" :key="log.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
              <td class="px-4 py-3 text-xs text-slate-500 font-mono whitespace-nowrap">
                {{ new Date(log.created_at).toLocaleString() }}
              </td>
              <td class="px-4 py-3 font-mono text-xs font-medium text-slate-700 dark:text-slate-300">
                {{ log.device_id || 'node' }}
              </td>
              <td class="px-4 py-3">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-mono">
                  {{ log.event_type }}
                </span>
              </td>
              <td class="px-4 py-3 text-xs font-mono text-slate-600 dark:text-slate-400 max-w-md truncate">
                {{ JSON.stringify(log.payload) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Device Modal -->
    <Modal :open="isAddDeviceOpen" title="Register IoT Device" @close="isAddDeviceOpen = false">
      <form @submit.prevent="handleAddDevice" class="space-y-4">
        <Input
          id="devId"
          v-model="newDeviceId"
          label="Device Identifier (ID)"
          placeholder="e.g. main_entrance_lock"
          required
        />
        <Input
          id="devName"
          v-model="newDeviceName"
          label="Friendly Name"
          placeholder="e.g. Front Door Lock"
          required
        />
        <div class="space-y-1">
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">Device Type</label>
          <select
            v-model="newDeviceType"
            class="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
          >
            <option value="lock">Smart Lock (TTLock)</option>
            <option value="relay">Lighting / Relay</option>
            <option value="valve">Water Leak Valve</option>
            <option value="climate">Climate / AC</option>
          </select>
        </div>
        <div class="flex justify-end space-x-2 pt-2">
          <Button variant="secondary" type="button" @click="isAddDeviceOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button type="submit" :loading="addingDevice">
            {{ t('common.save') }}
          </Button>
        </div>
      </form>
    </Modal>
  </div>
</template>
