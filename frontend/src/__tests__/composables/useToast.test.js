import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useToast } from '../../composables/useToast'

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    const { toasts } = useToast()
    toasts.value = []
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('adds a toast to the reactive array', () => {
    const { addToast, toasts } = useToast()
    addToast('Hello world')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('Hello world')
    expect(toasts.value[0].type).toBe('info')
  })

  it('supports different toast types', () => {
    const { addToast, toasts } = useToast()
    addToast('Success!', { type: 'success' })
    addToast('Warning!', { type: 'warning' })
    addToast('Error!', { type: 'error' })

    expect(toasts.value[0].type).toBe('success')
    expect(toasts.value[1].type).toBe('warning')
    expect(toasts.value[2].type).toBe('error')
  })

  it('auto-removes toast after duration', () => {
    const { addToast, toasts } = useToast()
    addToast('Temporary', { duration: 3000 })
    expect(toasts.value).toHaveLength(1)

    vi.advanceTimersByTime(3000)
    expect(toasts.value).toHaveLength(0)
  })

  it('removes a specific toast via removeToast', () => {
    const { addToast, removeToast, toasts } = useToast()
    const id = addToast('Remove me', { duration: 0 })
    addToast('Keep me', { duration: 0 })
    expect(toasts.value).toHaveLength(2)

    removeToast(id)
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('Keep me')
  })

  it('caps at 5 toasts, removing the oldest', () => {
    const { addToast, toasts } = useToast()
    for (let i = 0; i < 6; i++) {
      addToast(`Toast ${i}`, { duration: 0 })
    }
    expect(toasts.value).toHaveLength(5)
    expect(toasts.value[0].message).toBe('Toast 1')
    expect(toasts.value[4].message).toBe('Toast 5')
  })
})
