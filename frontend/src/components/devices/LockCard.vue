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
  property_id?: string;
  device_id?: string;
  name?: string;
  pin_name?: string;
  valid_from: string;
  valid_to: string;
  is_active?: boolean;
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
const isPermanentPin = ref(false);
const newValidFrom = ref('');
const newValidTo = ref('');
const creatingPin = ref(false);

function initPinForm() {
  newPinName.value = '';
  newPinCode.value = '';
  isPermanentPin.value = false;

  const now = new Date();
  now.setMinutes(0, 0, 0);
  const fromIsoLocal = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);

  const checkout = new Date(now.getTime() + 3 * 24 * 3600 * 1000);
  checkout.setHours(12, 0, 0, 0);
  const toIsoLocal = new Date(checkout.getTime() - checkout.getTimezoneOffset() * 60000).toISOString().slice(0, 16);

  newValidFrom.value = fromIsoLocal;
  newValidTo.value = toIsoLocal;
}

function isPermanent(pin: PinItem): boolean {
  if (!pin.valid_to) return true;
  const yr = new Date(pin.valid_to).getFullYear();
  return yr >= 2099;
}

function isExpired(pin: PinItem): boolean {
  if (isPermanent(pin)) return false;
  return new Date(pin.valid_to).getTime() < Date.now();
}

function formatValidity(pin: PinItem): string {
  if (isPermanent(pin)) {
    return t('devices.permanentBadge');
  }
  const from = new Date(pin.valid_from).toLocaleString([], {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
  const to = new Date(pin.valid_to).toLocaleString([], {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
  return `${from} – ${to}`;
}

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
  if (!newPinName.value.trim() || !newPinCode.value.trim()) return;
  if (!isPermanentPin.value && (!newValidFrom.value || !newValidTo.value)) {
    showToast(t('common.error'), 'error');
    return;
  }
  creatingPin.value = true;
  try {
    const validFromIso = newValidFrom.value
      ? new Date(newValidFrom.value).toISOString()
      : new Date().toISOString();
    const validToIso = isPermanentPin.value
      ? '2099-12-31T23:59:59.000Z'
      : new Date(newValidTo.value).toISOString();

    await apiRequest(
      `/properties/${props.device.property_id}/locks/${props.device.id}/pins`,
      {
        method: 'POST',
        body: JSON.stringify({
          device_id: props.device.id,
          name: newPinName.value.trim(),
          pin: newPinCode.value.trim(),
          valid_from: validFromIso,
          valid_to: validToIso,
        }),
      }
    );
    showToast(t('common.success'), 'success');
    initPinForm();
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
  initPinForm();
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
            {{ isLocked ? t('devices.locked') : t('devices.unlocked') }}
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
          <div class="flex items-center justify-between">
            <h5 class="text-xs font-semibold uppercase tracking-wider text-slate-500">{{ t('devices.createPin') }}</h5>
            <label class="inline-flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                v-model="isPermanentPin"
                class="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900"
              />
              <span>{{ t('devices.permanentPin') }}</span>
            </label>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <Input v-model="newPinName" :placeholder="t('devices.pinName')" required />
            <Input v-model="newPinCode" type="text" inputmode="numeric" pattern="[0-9]*" :placeholder="t('devices.pinCode')" required />
          </div>

          <!-- Date & Time Range (hidden if permanent) -->
          <div v-if="!isPermanentPin" class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">{{ t('devices.validFrom') }}</label>
              <input
                v-model="newValidFrom"
                type="datetime-local"
                class="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                required
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">{{ t('devices.validTo') }}</label>
              <input
                v-model="newValidTo"
                type="datetime-local"
                class="w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                required
              />
            </div>
          </div>

          <Button size="sm" class="w-full mt-2" :loading="creatingPin" @click="createPin">
            {{ t('common.add') }}
          </Button>
        </div>

        <!-- PINs List -->
        <div class="space-y-2 max-h-60 overflow-y-auto">
          <div v-if="pinsLoading" class="text-center py-4 text-xs text-slate-400">
            {{ t('common.loading') }}
          </div>
          <div v-else-if="pins.length === 0" class="text-center py-4 text-xs text-slate-400">
            {{ t('devices.noPins') }}
          </div>
          <div
            v-for="pin in pins"
            :key="pin.id"
            class="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
          >
            <div class="space-y-1">
              <div class="flex items-center space-x-2">
                <span class="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {{ pin.name || pin.pin_name }}
                </span>
                <Badge :variant="isPermanent(pin) ? 'neutral' : (isExpired(pin) ? 'danger' : 'success')">
                  {{ isPermanent(pin) ? t('devices.permanentBadge') : (isExpired(pin) ? t('devices.expiredBadge') : t('devices.activeBadge')) }}
                </Badge>
              </div>
              <div class="text-xs text-slate-500 dark:text-slate-400 font-mono">
                {{ formatValidity(pin) }}
              </div>
            </div>
            <button
              @click="deletePin(pin.id)"
              class="p-1.5 text-slate-400 hover:text-rose-500 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
            >
              <Trash2 class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </Modal>
  </Card>
</template>
