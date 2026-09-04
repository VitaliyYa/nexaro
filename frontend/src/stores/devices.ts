import { defineStore } from 'pinia';
import { ref } from 'vue';
import { supabase } from '@/lib/supabase';
import { apiRequest } from '@/lib/api';
import type { DeviceSchema } from '@/types/generated';
import type { RealtimeChannel } from '@supabase/supabase-js';

export interface DeviceLog {
  id: number;
  property_id: string;
  device_id: string | null;
  topic: string;
  event_type: string;
  payload: any;
  created_at: string;
}

export const useDevicesStore = defineStore('devices', () => {
  const devices = ref<DeviceSchema[]>([]);
  const pendingDeviceIds = ref<Set<string>>(new Set());
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Append-only history logs (fetched on-demand)
  const logs = ref<DeviceLog[]>([]);
  const logsLoading = ref(false);

  let activeChannel: RealtimeChannel | null = null;
  const timeoutTimers = new Map<string, ReturnType<typeof setTimeout>>();

  function isPending(deviceId: string): boolean {
    return pendingDeviceIds.value.has(deviceId);
  }

  function setPending(deviceId: string, pending: boolean) {
    const next = new Set(pendingDeviceIds.value);
    if (pending) {
      next.add(deviceId);
    } else {
      next.delete(deviceId);
    }
    pendingDeviceIds.value = next;
  }

  /**
   * "Fetch-then-Subscribe" pattern for a property's devices.
   */
  async function initPropertyDevices(propertyId: string) {
    cleanup(); // Unsubscribe previous channel if any
    loading.value = true;
    error.value = null;

    try {
      // 1. Fetch initial device states via REST API
      const initialDevices = await apiRequest<DeviceSchema[]>(`/properties/${propertyId}/devices`);
      devices.value = initialDevices;

      // 2. Subscribe to Supabase Realtime changes for this property's devices
      activeChannel = supabase
        .channel(`property-devices-${propertyId}`)
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'devices',
            filter: `property_id=eq.${propertyId}`,
          },
          (payload) => {
            handleRealtimeEvent(payload);
          }
        )
        .subscribe();
    } catch (err: any) {
      error.value = err.message || 'Failed to initialize devices';
    } finally {
      loading.value = false;
    }
  }

  function handleRealtimeEvent(payload: any) {
    const { eventType, new: newRecord, old: oldRecord } = payload;

    if (eventType === 'INSERT') {
      const exists = devices.value.some((d) => d.id === newRecord.id);
      if (!exists) {
        devices.value.push(newRecord as DeviceSchema);
      }
    } else if (eventType === 'UPDATE') {
      const idx = devices.value.findIndex((d) => d.id === newRecord.id);
      if (idx !== -1) {
        devices.value[idx] = newRecord as DeviceSchema;
      }
      // Clear pending state and timer on physical confirmation from Realtime
      if (timeoutTimers.has(newRecord.id)) {
        clearTimeout(timeoutTimers.get(newRecord.id));
        timeoutTimers.delete(newRecord.id);
      }
      setPending(newRecord.id, false);
    } else if (eventType === 'DELETE') {
      devices.value = devices.value.filter((d) => d.id !== oldRecord.id);
      setPending(oldRecord.id, false);
    }
  }

  /**
   * Dispatches a command to the device following the `optimistic: false` pattern.
   * UI toggle switches into pending state immediately, and only updates
   * upon arrival of the Supabase Realtime confirmation event.
   */
  async function sendCommand(
    propertyId: string,
    deviceId: string,
    commandPayload: any,
    onTimeout?: () => void
  ) {
    // 1. Enter pending state
    setPending(deviceId, true);

    // 2. Clear any existing timer for this device
    if (timeoutTimers.has(deviceId)) {
      clearTimeout(timeoutTimers.get(deviceId));
    }

    // 3. Set 10-second safety timeout
    const timer = setTimeout(() => {
      if (isPending(deviceId)) {
        setPending(deviceId, false);
        timeoutTimers.delete(deviceId);
        if (onTimeout) {
          onTimeout();
        }
      }
    }, 10000);
    timeoutTimers.set(deviceId, timer);

    // 4. Send command via FastAPI Backend REST API
    try {
      await apiRequest(`/properties/${propertyId}/devices/${deviceId}/command`, {
        method: 'POST',
        body: JSON.stringify({
          command: commandPayload,
        }),
      });
    } catch (err: any) {
      // Revert pending state immediately if HTTP command dispatch failed
      clearTimeout(timer);
      timeoutTimers.delete(deviceId);
      setPending(deviceId, false);
      throw err;
    }
  }

  /**
   * Fetch append-only device history logs on demand with pagination.
   */
  async function fetchDeviceLogs(propertyId: string, limit = 50) {
    logsLoading.value = true;
    try {
      const data = await apiRequest<DeviceLog[]>(`/properties/${propertyId}/logs?limit=${limit}`);
      logs.value = data;
    } catch (err: any) {
      console.error('Failed to load device logs:', err);
    } finally {
      logsLoading.value = false;
    }
  }

  function cleanup() {
    if (activeChannel) {
      supabase.removeChannel(activeChannel);
      activeChannel = null;
    }
    for (const timer of timeoutTimers.values()) {
      clearTimeout(timer);
    }
    timeoutTimers.clear();
    pendingDeviceIds.value.clear();
  }

  return {
    devices,
    loading,
    error,
    logs,
    logsLoading,
    isPending,
    initPropertyDevices,
    sendCommand,
    fetchDeviceLogs,
    cleanup,
  };
});
