import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SidebarButton from '../../components/SidebarButton.vue'

const mockPush = vi.fn()
const mockHasRoute = vi.fn(() => false)

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
    hasRoute: mockHasRoute,
  }),
  useRoute: () => ({
    name: 'home',
    path: '/home',
  }),
}))

describe('SidebarButton', () => {
  const defaultProps = {
    label: 'Dashboard',
    to: '/dashboard',
    icon: '/icons/dashboards.svg',
  }

  it('renders the label text', () => {
    const wrapper = mount(SidebarButton, { props: defaultProps })
    expect(wrapper.text()).toContain('Dashboard')
  })

  it('renders the icon image', () => {
    const wrapper = mount(SidebarButton, { props: defaultProps })
    const img = wrapper.find('img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('/icons/dashboards.svg')
  })

  it('applies inactive class when route does not match', () => {
    const wrapper = mount(SidebarButton, { props: defaultProps })
    expect(wrapper.find('button').classes()).toContain('bg-white/5')
  })

  it('applies active class when path matches current route', () => {
    const wrapper = mount(SidebarButton, {
      props: { ...defaultProps, to: '/home' },
    })
    expect(wrapper.find('button').classes()).toContain('bg-white/25')
  })

  it('navigates on click using path when not a named route', async () => {
    mockHasRoute.mockReturnValue(false)
    const wrapper = mount(SidebarButton, { props: defaultProps })
    await wrapper.find('button').trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('navigates using route name when it is a named route', async () => {
    mockHasRoute.mockReturnValue(true)
    const wrapper = mount(SidebarButton, {
      props: { ...defaultProps, to: 'dashboard' },
    })
    await wrapper.find('button').trigger('click')
    expect(mockPush).toHaveBeenCalledWith({ name: 'dashboard' })
  })
})
