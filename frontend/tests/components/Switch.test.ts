import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import Switch from '@/components/ui/Switch.vue';

describe('Switch UI Component (optimistic: false)', () => {
  it('renders correctly with checked=false', () => {
    const wrapper = mount(Switch, {
      props: {
        checked: false,
        pending: false,
      },
    });

    expect(wrapper.find('button').attributes('aria-checked')).toBe('false');
    expect(wrapper.find('button').classes()).toContain('bg-slate-300');
  });

  it('renders correctly with checked=true', () => {
    const wrapper = mount(Switch, {
      props: {
        checked: true,
        pending: false,
      },
    });

    expect(wrapper.find('button').attributes('aria-checked')).toBe('true');
    expect(wrapper.find('button').classes()).toContain('bg-indigo-600');
  });

  it('emits toggle event when clicked', async () => {
    const wrapper = mount(Switch, {
      props: {
        checked: false,
        pending: false,
      },
    });

    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('toggle')).toBeTruthy();
  });

  it('does NOT emit toggle when pending is true', async () => {
    const wrapper = mount(Switch, {
      props: {
        checked: false,
        pending: true,
      },
    });

    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('toggle')).toBeFalsy();
    expect(wrapper.find('button').attributes('disabled')).toBeDefined();
  });
});
