---
name: vue3-iot-ui
description: >-
  Frontend UI/UX architecture and Pinia state management patterns for Vue 3 SPA in SmartRent,
  implementing optimistic: false and real-time IoT state synchronization.
---

# Vue 3 IoT Frontend & State Management Guide

This skill governs the Vue 3 SPA architecture, Pinia state stores, and UI interaction models for **SmartRent**.

---

## 1. The `optimistic: false` Pattern for IoT Controls

For physical IoT devices (relays, smart locks, water valves, climate):
- **Never** optimistically switch the toggle/state in the UI immediately upon user click.
- Instead, put the target component/switch into a `loading = true` state.
- Dispatch the API/MQTT command to the backend.
- The UI toggle updates its visual state and resets `loading = false` **only** when the actual confirmation package arrives via the `state` stream (SSE or WSS).
- If no confirmation arrives within a timeout (e.g. 5-10 seconds), reset loading and display a toast notification ("Device did not respond").

### Example Component Pattern
```vue
<script setup lang="ts">
import { ref } from 'vue';
import { useDeviceStore } from '@/stores/devices';

const props = defineProps<{
  deviceId: string;
  currentState: 'ON' | 'OFF';
}>();

const deviceStore = useDeviceStore();
const isPending = ref(false);

async function handleToggle() {
  isPending.value = true;
  try {
    const nextState = props.currentState === 'ON' ? 'OFF' : 'ON';
    await deviceStore.sendCommand(props.deviceId, nextState);
    // Note: isPending will be cleared by the store once the state update is received from telemetry stream
  } catch (error) {
    isPending.value = false;
  }
}
</script>

<template>
  <button 
    :disabled="isPending"
    :class="{ 'loading-spinner': isPending, 'active': currentState === 'ON' }"
    @click="handleToggle"
  >
    <span v-if="isPending">Updating...</span>
    <span v-else>{{ currentState }}</span>
  </button>
</template>
```

---

## 2. Pinia Store Design for Real-time Devices

- Keep a normalized map of devices keyed by `deviceId`.
- Maintain connection health state (`online` / `offline`) per Edge node.
- Subscribe to real-time events upon entering the property dashboard, and unsubscribe on route leave to avoid memory leaks.
