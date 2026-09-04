<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useDevicesStore } from '@/stores/devices';
import { useToast } from '@/composables/useToast';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Badge from '@/components/ui/Badge.vue';
import { Droplet, AlertTriangle, ShieldCheck } from 'lucide-vue-next';
import type { DeviceSchema } from '@/types/generated';

interface Props {
  device: DeviceSchema;
}

const props = defineProps<Props>();
const { t } = useI18n();
const devicesStore = useDevicesStore();
const { showToast } = useToast();

const isPending = computed(() => devicesStore.isPending(props.device.id));
const settings = computed(() => (props.device.settings as any) || {});
const isOpen = computed(() => settings.value.state !== 'closed');
const isLeakDetected = computed(() => !!settings.value.leak_detected);

async function handleToggleValve() {
  const nextAction = isOpen.value ? 'CLOSE' : 'OPEN';
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
</script>

<template>
  <Card class="flex flex-col justify-between" :class="isLeakDetected ? 'ring-2 ring-rose-500 bg-rose-50/20' : undefined">
    <div>
      <div class="flex items-center justify-between">
        <div
          :class="[
            'p-2.5 rounded-lg',
            isLeakDetected
              ? 'bg-rose-100 text-rose-700 animate-pulse dark:bg-rose-950/70 dark:text-rose-300'
              : 'bg-sky-50 text-sky-600 dark:bg-sky-950/50 dark:text-sky-400',
          ]"
        >
          <AlertTriangle v-if="isLeakDetected" class="h-6 w-6" />
          <Droplet v-else class="h-6 w-6" />
        </div>
        <div class="flex items-center space-x-2">
          <Badge v-if="isLeakDetected" variant="danger">
            {{ t('devices.leakDetected') }}
          </Badge>
          <Badge v-else variant="success">
            {{ t('devices.normal') }}
          </Badge>
        </div>
      </div>

      <div class="mt-4">
        <h4 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ device.name }}</h4>
        <p class="text-xs text-slate-500 flex items-center mt-1">
          <ShieldCheck class="h-3.5 w-3.5 mr-1 text-emerald-500" />
          {{ t('devices.waterValve') }}
        </p>
      </div>
    </div>

    <div class="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
      <span class="text-sm font-medium text-slate-700 dark:text-slate-300">
        {{ isOpen ? t('common.active') : t('common.inactive') }}
      </span>
      <Button
        size="sm"
        :variant="isOpen ? 'danger' : 'primary'"
        :loading="isPending"
        @click="handleToggleValve"
      >
        {{ isOpen ? t('devices.closeValve') : t('devices.openValve') }}
      </Button>
    </div>
  </Card>
</template>
