<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useDevicesStore } from '@/stores/devices';
import { useToast } from '@/composables/useToast';
import Card from '@/components/ui/Card.vue';
import Switch from '@/components/ui/Switch.vue';
import Badge from '@/components/ui/Badge.vue';
import { Lightbulb, Zap } from 'lucide-vue-next';
import type { DeviceSchema } from '@/types/generated';

interface Props {
  device: DeviceSchema;
}

const props = defineProps<Props>();
const { t } = useI18n();
const devicesStore = useDevicesStore();
const { showToast } = useToast();

const isPending = computed(() => devicesStore.isPending(props.device.id));
const currentState = computed(() => {
  const settings = props.device.settings as any;
  const state = settings?.state || 'OFF';
  return String(state).toUpperCase();
});
const isOn = computed(() => currentState.value === 'ON');

async function handleToggle() {
  const nextState = isOn.value ? 'OFF' : 'ON';
  try {
    await devicesStore.sendCommand(
      props.device.property_id,
      props.device.id,
      nextState,
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
  <Card class="flex flex-col justify-between">
    <div>
      <div class="flex items-center justify-between">
        <div class="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
          <Lightbulb class="h-6 w-6" />
        </div>
        <Badge :variant="isOn ? 'success' : 'neutral'">
          {{ isOn ? t('common.active') : t('common.inactive') }}
        </Badge>
      </div>

      <div class="mt-4">
        <h4 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ device.name }}</h4>
        <p class="text-xs text-slate-500 flex items-center mt-1">
          <Zap class="h-3 w-3 mr-1" />
          {{ t('devices.relay') }}
        </p>
      </div>
    </div>

    <div class="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
      <span class="text-sm font-medium text-slate-700 dark:text-slate-300">
        {{ isOn ? t('devices.turnOn') : t('devices.turnOff') }}
      </span>
      <Switch
        :checked="isOn"
        :pending="isPending"
        @toggle="handleToggle"
      />
    </div>
  </Card>
</template>
