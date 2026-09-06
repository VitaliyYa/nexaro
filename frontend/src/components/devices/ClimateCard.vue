<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useDevicesStore } from '@/stores/devices';
import { useToast } from '@/composables/useToast';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Badge from '@/components/ui/Badge.vue';
import { Thermometer, Plus, Minus, Wind } from 'lucide-vue-next';
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
const currentTemp = computed(() => settings.value.current_temperature ?? 22.0);
const targetTemp = computed(() => settings.value.target_temperature ?? 22.0);
const mode = computed(() => settings.value.mode || 'cool');

async function adjustTemperature(delta: number) {
  const newTarget = Math.round((targetTemp.value + delta) * 10) / 10;
  try {
    await devicesStore.sendCommand(
      props.device.property_id,
      props.device.id,
      {
        command: 'SET_TEMPERATURE',
        target_temperature: newTarget,
        hvac_mode: mode.value,
        mode: mode.value,
      },
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
        <div class="p-2.5 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400">
          <Thermometer class="h-6 w-6" />
        </div>
        <div class="flex items-center space-x-2">
          <Badge variant="info">
            {{ mode.toUpperCase() }}
          </Badge>
        </div>
      </div>

      <div class="mt-4">
        <h4 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ device.name }}</h4>
        <p class="text-xs text-slate-500 flex items-center mt-1">
          <Wind class="h-3.5 w-3.5 mr-1" />
          {{ t('devices.climate') }}
        </p>
      </div>

      <div class="mt-4 flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
        <div>
          <span class="text-xs text-slate-500 block">{{ t('devices.current') }}</span>
          <span class="text-xl font-bold text-slate-800 dark:text-slate-100">{{ currentTemp }}°C</span>
        </div>
        <div class="text-right">
          <span class="text-xs text-slate-500 block">{{ t('devices.target') }}</span>
          <span class="text-xl font-bold text-indigo-600 dark:text-indigo-400">{{ targetTemp }}°C</span>
        </div>
      </div>
    </div>

    <div class="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between space-x-2">
      <Button
        size="sm"
        variant="outline"
        :loading="isPending"
        @click="adjustTemperature(-0.5)"
        class="w-full"
      >
        <Minus class="h-4 w-4 mr-1" /> -0.5°
      </Button>

      <Button
        size="sm"
        variant="outline"
        :loading="isPending"
        @click="adjustTemperature(0.5)"
        class="w-full"
      >
        <Plus class="h-4 w-4 mr-1" /> +0.5°
      </Button>
    </div>
  </Card>
</template>
