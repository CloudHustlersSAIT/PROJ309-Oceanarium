import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../contexts/authContext'
import { firebaseDisabled } from '../utils/firebase'

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
      redirect: () => (firebaseDisabled ? '/home' : '/login'),
    },

    // Catch-all route
    {
      path: '/:pathMatch(.*)*',
      redirect: () => (firebaseDisabled ? '/home' : '/login'),
    },
  ],
})

// -----------------------
// Global Route Guard
// -----------------------
router.beforeEach((to, from, next) => {
  // Allow everything in dev mode if Firebase disabled
  if (firebaseDisabled) return next()

  const { user } = useAuth()
  const publicRoutes = ['login', 'forgot-password']

  // If logged in user tries to access login/forgot-password
  if (to.name && publicRoutes.includes(to.name) && user.value) {
    const role = localStorage.getItem('role') || 'admin'
    return next(role === 'guide' ? '/guide/home' : '/home')
  }

  // If route requires authentication and user not logged in
  if (to.meta?.requiresAuth && !user.value) {
    return next('/login')
  }

  // Role-based access control
  const requiredRole = to.meta?.role
  if (requiredRole) {
    const role = localStorage.getItem('role') || 'admin'
    if (role !== requiredRole) {
      return next(role === 'guide' ? '/guide/home' : '/home')
    }
  }

  return next()
})

export default router
