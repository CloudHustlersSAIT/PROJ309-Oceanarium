import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import AppToast from '../../components/AppToast.vue'
import { useToast } from '../../composables/useToast'

describe('AppToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    const { toasts } = useToast()
    toasts.value = []
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders toast messages', async () => {
    const { addToast } = useToast()
    addToast('Test message', { type: 'info', duration: 0 })

    const wrapper = mount(AppToast)
    expect(wrapper.text()).toContain('Test message')
  })

  it('removes toast when close button is clicked', async () => {
    const { addToast, toasts } = useToast()
    addToast('Close me', { type: 'success', duration: 0 })

    const wrapper = mount(AppToast)
    await wrapper.find('button[aria-label="Dismiss"]').trigger('click')

    expect(toasts.value).toHaveLength(0)
  })

  it('applies correct classes for info type', () => {
    const { addToast } = useToast()
    addToast('Info toast', { type: 'info', duration: 0 })

    const wrapper = mount(AppToast)
    const card = wrapper.find('[class*="border-blue"]')
    expect(card.exists()).toBe(true)
  })

  it('applies correct classes for success type', () => {
    const { addToast } = useToast()
    addToast('Success toast', { type: 'success', duration: 0 })

    const wrapper = mount(AppToast)
    const card = wrapper.find('[class*="border-emerald"]')
    expect(card.exists()).toBe(true)
  })

  it('applies correct classes for warning type', () => {
    const { addToast } = useToast()
    addToast('Warning toast', { type: 'warning', duration: 0 })

    const wrapper = mount(AppToast)
    const card = wrapper.find('[class*="border-amber"]')
    expect(card.exists()).toBe(true)
  })

  it('applies correct classes for error type', () => {
    const { addToast } = useToast()
    addToast('Error toast', { type: 'error', duration: 0 })

    const wrapper = mount(AppToast)
    const card = wrapper.find('[class*="border-red"]')
    expect(card.exists()).toBe(true)
  })
})
