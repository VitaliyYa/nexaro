import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useDevicesStore } from '@/stores/devices';

// Mock apiRequest
vi.mock('@/lib/api', () => ({
  apiRequest: vi.fn().mockImplementation((url: string) => {
    if (url.includes('/devices') && !url.includes('/command')) {
      return Promise.resolve([
        {
          id: 'dev-1',
          property_id: 'prop-123',
          device_type: 'relay',
          name: 'Test Relay',
          is_active: true,
          settings: { state: 'OFF' },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]);
    }
    if (url.includes('/command')) {
      return Promise.resolve({ status: 'dispatched' });
    }
    return Promise.resolve([]);
  }),
}));

// Mock supabase client
vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn().mockReturnValue({
      on: vi.fn().mockReturnThis(),
      subscribe: vi.fn().mockReturnThis(),
    }),
    removeChannel: vi.fn(),
  },
}));

describe('Devices Store - optimistic: false & Realtime lifecycle', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();
  });

  it('initializes devices via Fetch-then-Subscribe', async () => {
    const store = useDevicesStore();
    await store.initPropertyDevices('prop-123');

    expect(store.devices).toHaveLength(1);
    expect(store.devices[0].id).toBe('dev-1');
    expect(store.isPending('dev-1')).toBe(false);
  });

  it('marks device as pending when command is dispatched and reverts on timeout', async () => {
    const store = useDevicesStore();
    await store.initPropertyDevices('prop-123');

    const timeoutCallback = vi.fn();
    await store.sendCommand('prop-123', 'dev-1', 'ON', timeoutCallback);

    // Immediately pending
    expect(store.isPending('dev-1')).toBe(true);

    // Advance timer past 10s timeout
    vi.advanceTimersByTime(10500);

    expect(timeoutCallback).toHaveBeenCalled();
    expect(store.isPending('dev-1')).toBe(false);
  });
});
