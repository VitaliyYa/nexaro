import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiRequest } from '@/lib/api';
import type { PropertySchema } from '@/types/generated';

export const usePropertiesStore = defineStore('properties', () => {
  const properties = ref<PropertySchema[]>([]);
  const currentProperty = ref<PropertySchema | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchProperties() {
    loading.value = true;
    error.value = null;
    try {
      const data = await apiRequest<PropertySchema[]>('/properties');
      properties.value = data;
    } catch (err: any) {
      error.value = err.message || 'Failed to load properties';
    } finally {
      loading.value = false;
    }
  }

  async function fetchProperty(id: string) {
    loading.value = true;
    error.value = null;
    try {
      const data = await apiRequest<PropertySchema>(`/properties/${id}`);
      currentProperty.value = data;
      return data;
    } catch (err: any) {
      error.value = err.message || 'Failed to load property';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function createProperty(payload: { name: string; address?: string; timezone?: string }) {
    loading.value = true;
    error.value = null;
    try {
      const newProp = await apiRequest<PropertySchema>('/properties', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      properties.value.push(newProp);
      return newProp;
    } catch (err: any) {
      error.value = err.message || 'Failed to create property';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return {
    properties,
    currentProperty,
    loading,
    error,
    fetchProperties,
    fetchProperty,
    createProperty,
  };
});
