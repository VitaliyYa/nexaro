import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { supabase } from '@/lib/supabase';
import type { User, Session } from '@supabase/supabase-js';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const session = ref<Session | null>(null);
  const loading = ref(true);

  const isAuthenticated = computed(() => !!session.value);
  const isSuperAdmin = computed(() => {
    if (!user.value) return false;
    const appRole = user.value.app_metadata?.role;
    const userRole = user.value.user_metadata?.role;
    return appRole === 'superadmin' || userRole === 'superadmin';
  });

  async function initAuth() {
    loading.value = true;
    try {
      const { data } = await supabase.auth.getSession();
      session.value = data.session;
      user.value = data.session?.user || null;

      supabase.auth.onAuthStateChange((_event, currentSession) => {
        session.value = currentSession;
        user.value = currentSession?.user || null;
      });
    } finally {
      loading.value = false;
    }
  }

  async function signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
    session.value = data.session;
    user.value = data.user;
    return data;
  }

  async function signOut() {
    await supabase.auth.signOut();
    session.value = null;
    user.value = null;
  }

  return {
    user,
    session,
    loading,
    isAuthenticated,
    isSuperAdmin,
    initAuth,
    signIn,
    signOut,
  };
});
