import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../contexts/authContext'
import { firebaseDisabled } from '../utils/firebase'
import { getDefaultRouteForRole } from '../services/authService'

// Admin views
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import DashboardView from '../views/DashboardView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import AssetsView from '../views/AssetsView.vue'
import BookingsView from '../views/BookingsView.vue'
import CalendarView from '../views/CalendarView.vue'
import SettingsView from '../views/SettingsView.vue'

// Guide layout + views
import GuideLayout from '../layouts/GuideLayout.vue'
import GuideHomeView from '../views/guide/GuideHomeView.vue'
import GuideScheduleView from '../views/guide/GuideScheduleView.vue'
import GuideRequestsView from '../views/guide/GuideRequestsView.vue'
import GuideNotificationsView from '../views/guide/GuideNotificationsView.vue'
import GuideProfileView from '../views/guide/GuideProfileView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Public routes
    { path: '/login', name: 'login', component: LoginView },
    { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },

    // -----------------------
    // Admin routes
    // -----------------------
    {
      path: '/home',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: NotificationsView,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/assets',
      name: 'assets',
      component: AssetsView,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/bookings',
      name: 'bookings',
      component: BookingsView,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/calendar',
      name: 'calendar',
      component: CalendarView,
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true, role: 'admin' },
    },

    // -----------------------
    // Guide Portal (Nested)
    // -----------------------
    {
      path: '/guide',
      component: GuideLayout,
      meta: { requiresAuth: true, role: 'guide' },
      children: [
        { path: '', redirect: { name: 'guide-home' } },
        { path: 'home', name: 'guide-home', component: GuideHomeView },
        { path: 'schedule', name: 'guide-schedule', component: GuideScheduleView },
        { path: 'requests', name: 'guide-requests', component: GuideRequestsView },
        { path: 'notifications', name: 'guide-notifications', component: GuideNotificationsView },
        { path: 'profile', name: 'guide-profile', component: GuideProfileView },
      ],
    },

    // Default route
    {
      path: '/',
      redirect: '/login',
    },

    // Catch-all route
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

// -----------------------
// Global Route Guard
// -----------------------
router.beforeEach(async (to, from, next) => {
  // Allow everything in dev mode if Firebase disabled
  if (firebaseDisabled) return next()

  const { user, role, ensureAuthReady } = useAuth()
  try {
    await ensureAuthReady()
  } catch {
    // Let the checks below handle redirects for invalid sessions.
  }
  const publicRoutes = ['login', 'forgot-password']

  // If logged in user tries to access login/forgot-password
  if (to.name && publicRoutes.includes(to.name) && user.value && role.value) {
    return next(getDefaultRouteForRole(role.value))
  }

  // If route requires authentication and user not logged in
  if (to.meta?.requiresAuth && !user.value) {
    return next('/login')
  }

  if (to.meta?.requiresAuth && user.value && !role.value) {
    return next('/login')
  }

  // Role-based access control
  const requiredRole = to.meta?.role
  if (requiredRole) {
    if (role.value !== requiredRole) {
      return next(getDefaultRouteForRole(role.value))
    }
  }

  return next()
})

export default router
