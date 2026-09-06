import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiRequest } from '@/lib/api';

export interface SystemStatus {
  status: string;
  environment: string;
  mqtt_connected: boolean;
  caller?: string;
}

export interface CreatedUserResult {
  message: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
  seeded_property?: any;
}

export const useAdminStore = defineStore('admin', () => {
  const status = ref<SystemStatus | null>(null);
  const loading = ref(false);
  const creatingUser = ref(false);
  const lastCreatedUser = ref<CreatedUserResult | null>(null);
  const error = ref<string | null>(null);

  async function fetchStatus() {
    loading.value = true;
    try {
      status.value = await apiRequest<SystemStatus>('/admin/status');
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch status';
    } finally {
      loading.value = false;
    }
  }

  async function createTestUser(payload: {
    email: string;
    password: string;
    name: string;
    seed_property: boolean;
  }) {
    creatingUser.value = true;
    error.value = null;
    try {
      const result = await apiRequest<CreatedUserResult>('/admin/users', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      lastCreatedUser.value = result;
      return result;
    } catch (err: any) {
      error.value = err.message || 'Failed to create test user';
      throw err;
    } finally {
      creatingUser.value = false;
    }
  }

  return {
    status,
    loading,
    creatingUser,
    lastCreatedUser,
    error,
    fetchStatus,
    createTestUser,
  };
});
