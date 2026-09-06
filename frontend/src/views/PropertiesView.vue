<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { usePropertiesStore } from '@/stores/properties';
import { useToast } from '@/composables/useToast';
import Card from '@/components/ui/Card.vue';
import Button from '@/components/ui/Button.vue';
import Modal from '@/components/ui/Modal.vue';
import Input from '@/components/ui/Input.vue';
import { Building2, Plus, MapPin, ArrowRight } from 'lucide-vue-next';

const { t } = useI18n();
const router = useRouter();
const propertiesStore = usePropertiesStore();
const { showToast } = useToast();

const isAddModalOpen = ref(false);
const newName = ref('');
const newAddress = ref('');
const creating = ref(false);

onMounted(() => {
  propertiesStore.fetchProperties();
});

async function handleCreateProperty() {
  if (!newName.value) return;
  creating.value = true;
  try {
    const prop = await propertiesStore.createProperty({
      name: newName.value,
      address: newAddress.value,
    });
    showToast(t('common.success'), 'success');
    isAddModalOpen.value = false;
    newName.value = '';
    newAddress.value = '';
    router.push(`/properties/${prop.id}`);
  } catch (err: any) {
    showToast(err.message || t('common.error'), 'error');
  } finally {
    creating.value = false;
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          {{ t('properties.title') }}
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          {{ t('properties.subtitle') }}
        </p>
      </div>

      <Button @click="isAddModalOpen = true" class="flex items-center">
        <Plus class="h-4 w-4 mr-2" />
        {{ t('properties.addProperty') }}
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="propertiesStore.loading" class="text-center py-12 text-slate-400">
      {{ t('common.loading') }}
    </div>

    <!-- Empty State -->
    <div
      v-else-if="propertiesStore.properties.length === 0"
      class="text-center py-16 px-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-800"
    >
      <Building2 class="mx-auto h-12 w-12 text-slate-400" />
      <h3 class="mt-4 text-base font-semibold text-slate-900 dark:text-slate-100">
        {{ t('properties.noProperties') }}
      </h3>
      <div class="mt-6">
        <Button @click="isAddModalOpen = true">
          <Plus class="h-4 w-4 mr-2" />
          {{ t('properties.addProperty') }}
        </Button>
      </div>
    </div>

    <!-- Properties Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card
        v-for="prop in propertiesStore.properties"
        :key="prop.id"
        class="flex flex-col justify-between hover:border-indigo-200 transition-colors"
      >
        <div>
          <div class="flex items-center justify-between">
            <div class="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
              <Building2 class="h-5 w-5" />
            </div>
            <span class="text-xs text-slate-400 font-mono">{{ prop.timezone }}</span>
          </div>

          <h3 class="mt-4 text-lg font-bold text-slate-900 dark:text-slate-100">{{ prop.name }}</h3>
          <p v-if="prop.address" class="text-xs text-slate-500 flex items-center mt-1">
            <MapPin class="h-3.5 w-3.5 mr-1 text-slate-400 shrink-0" />
            <span class="truncate">{{ prop.address }}</span>
          </p>
        </div>

        <div class="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <router-link
            :to="`/properties/${prop.id}`"
            class="inline-flex items-center text-sm font-semibold text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
          >
            <span>{{ t('properties.viewDashboard') }}</span>
            <ArrowRight class="h-4 w-4 ml-1" />
          </router-link>
        </div>
      </Card>
    </div>

    <!-- Add Property Modal -->
    <Modal :open="isAddModalOpen" :title="t('properties.addProperty')" @close="isAddModalOpen = false">
      <form @submit.prevent="handleCreateProperty" class="space-y-4">
        <Input
          id="propName"
          v-model="newName"
          :label="t('properties.title')"
          placeholder="e.g. Sunset Boulevard Apt 4B"
          required
        />
        <Input
          id="propAddress"
          v-model="newAddress"
          :label="t('properties.address')"
          placeholder="123 Palm Street, Miami, FL"
        />
        <div class="flex justify-end space-x-2 pt-2">
          <Button variant="secondary" type="button" @click="isAddModalOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button type="submit" :loading="creating">
            {{ t('common.save') }}
          </Button>
        </div>
      </form>
    </Modal>
  </div>
</template>
