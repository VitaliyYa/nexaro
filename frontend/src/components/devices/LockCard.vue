<script setup lang="ts">
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useDevicesStore } from '@/stores/devices';
import { useToast } from '@/composables/useToast';
import { apiRequest } from '@/lib/api';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Badge from '@/components/ui/Badge.vue';
import Modal from '@/components/ui/Modal.vue';
import Input from '@/components/ui/Input.vue';
import { Lock, Unlock, KeyRound, Battery, Trash2 } from 'lucide-vue-next';
import type { DeviceSchema } from '@/types/generated';

interface Props {
  device: DeviceSchema;
}

interface PinItem {
  id: string;
  pin_name: string;
  created_at: string;
}

const props = defineProps<Props>();
const { t } = useI18n();
const devicesStore = useDevicesStore();
const { showToast } = useToast();

const isPending = computed(() => devicesStore.isPending(props.device.id));
const settings = computed(() => (props.device.settings as any) || {});
const lockState = computed(() => settings.value.lock_state || settings.value.state || 'locked');
const isLocked = computed(() => lockState.value === 'locked');
const battery = computed(() => settings.value.battery ?? 90);

// PIN Modal State
const isPinModalOpen = ref(false);
const pins = ref<PinItem[]>([]);
const pinsLoading = ref(false);
const newPinName = ref('');
const newPinCode = ref('');
const creatingPin = ref(false);

async function handleToggleLock() {
  const nextAction = isLocked.value ? 'UNLOCK' : 'LOCK';
  try {
    await devicesStore.sendCommand(
      props.device.property_id,
      props.device.id,
      nextAction,
      () => {
        showToast(t('devices.timeoutError'), 'error');
      }
    );
  } catch (err: any) {
    showToast(err.message || t('common.error'), 'error');
  }
}

async function loadPins() {
  pinsLoading.value = true;
  try {
    const data = await apiRequest<PinItem[]>(
      `/properties/${props.device.property_id}/locks/${props.device.id}/pins`
    );
    pins.value = data;
  } catch (err: any) {
    console.error('Failed to load pins:', err);
  } finally {
    pinsLoading.value = false;
  }
}

async function createPin() {
  if (!newPinName.value || !newPinCode.value) return;
  creatingPin.value = true;
  try {
    await apiRequest(
      `/properties/${props.device.property_id}/locks/${props.device.id}/pins`,
      {
        method: 'POST',
        body: JSON.stringify({
          pin_name: newPinName.value,
          pin_code: newPinCode.value,
        }),
      }
    );
    showToast(t('common.success'), 'success');
    newPinName.value = '';
    newPinCode.value = '';
    await loadPins();
  } catch (err: any) {
    showToast(err.message || t('common.error'), 'error');
  } finally {
    creatingPin.value = false;
  }
}

async function deletePin(pinId: string) {
  try {
    await apiRequest(
      `/properties/${props.device.property_id}/locks/${props.device.id}/pins/${pinId}`,
      { method: 'DELETE' }
    );
    pins.value = pins.value.filter((p) => p.id !== pinId);
    showToast(t('common.success'), 'success');
  } catch (err: any) {
    showToast(err.message || t('common.error'), 'error');
  }
}

function openPinManager() {
  isPinModalOpen.value = true;
  loadPins();
}
</script>

<template>
  <Card class="flex flex-col justify-between">
    <div>
      <div class="flex items-center justify-between">
        <div
          :class="[
            'p-2.5 rounded-lg',
            isLocked
              ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400'
              : 'bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-400',
          ]"
        >
          <Lock v-if="isLocked" class="h-6 w-6" />
          <Unlock v-else class="h-6 w-6" />
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-xs text-slate-500 flex items-center">
            <Battery class="h-3.5 w-3.5 mr-1 text-slate-400" />
            {{ battery }}%
          </span>
          <Badge :variant="isLocked ? 'success' : 'warning'">
            {{ isLocked ? t('devices.lock') : t('devices.unlock') }}
          </Badge>
        </div>
      </div>

      <div class="mt-4">
        <h4 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ device.name }}</h4>
        <p class="text-xs text-slate-500 flex items-center mt-1">
          {{ t('devices.smartLock') }} (TTLock)
        </p>
      </div>
    </div>

    <div class="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between space-x-2">
      <Button
        size="sm"
        variant="outline"
        @click="openPinManager"
        class="flex items-center"
      >
        <KeyRound class="h-4 w-4 mr-1.5" />
        {{ t('devices.pins') }}
      </Button>

      <Button
        size="sm"
        :variant="isLocked ? 'danger' : 'primary'"
        :loading="isPending"
        @click="handleToggleLock"
      >
        {{ isLocked ? t('devices.unlock') : t('devices.lock') }}
      </Button>
    </div>

    <!-- PIN Management Modal -->
    <Modal :open="isPinModalOpen" :title="`${t('devices.pins')} - ${device.name}`" @close="isPinModalOpen = false">
      <div class="space-y-4">
        <!-- Form to add new PIN -->
        <div class="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-3">
          <h5 class="text-xs font-semibold uppercase tracking-wider text-slate-500">{{ t('devices.createPin') }}</h5>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <Input v-model="newPinName" :placeholder="t('devices.pinName')" />
            <Input v-model="newPinCode" type="password" :placeholder="t('devices.pinCode')" />
          </div>
          <Button size="sm" class="w-full" :loading="creatingPin" @click="createPin">
            {{ t('common.add') }}
          </Button>
        </div>

        <!-- PINs List -->
        <div class="space-y-2 max-h-60 overflow-y-auto">
          <div v-if="pinsLoading" class="text-center py-4 text-xs text-slate-400">
            {{ t('common.loading') }}
          </div>
          <div v-else-if="pins.length === 0" class="text-center py-4 text-xs text-slate-400">
            {{ t('devices.noDevices') }}
          </div>
          <div
            v-for="pin in pins"
            :key="pin.id"
            class="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
          >
            <div>
              <div class="text-sm font-medium text-slate-900 dark:text-slate-100">{{ pin.pin_name }}</div>
              <div class="text-xs text-slate-400">
                {{ new Date(pin.created_at).toLocaleDateString() }}
              </div>
            </div>
            <button
              @click="deletePin(pin.id)"
              class="p-1.5 text-slate-400 hover:text-rose-500 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <Trash2 class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </Card>
</template>
