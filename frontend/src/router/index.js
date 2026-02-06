// Import necessary modules
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../contexts/authContext'
import { firebaseDisabled } from '../utils/firebase'

//Import views
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import DashboardView from '../views/DashboardView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import AssetsView from '../views/AssetsView.vue'
import BookingsView from '../views/BookingsView.vue'
import CalendarView from '../views/CalendarView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/home', name: 'home', component: HomeView },
    { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
    { path: '/dashboard', name: 'dashboard', component: DashboardView },
    { path: '/notifications', name: 'notifications', component: NotificationsView },
    { path: '/assets', name: 'assets', component: AssetsView },
    { path: '/bookings', name: 'bookings', component: BookingsView },
    { path: '/calendar', name: 'calendar', component: CalendarView },
    { path: '/settings', name: 'settings', component: SettingsView },
    // Default route: when Firebase is disabled, go to /home; otherwise go to /login
    { path: '/', redirect: () => (firebaseDisabled ? '/home' : '/login') },
  ],
})

//Protect routes that require authentication
router.beforeEach((to, from, next) => {
  // If Firebase is not configured, skip auth checks so the app is usable in local/dev.
  if (firebaseDisabled) return next()

  const { user } = useAuth()

  // Public routes (no auth required)
  const publicRoutes = ['login', 'forgot-password']

  // If user is logged in and goes to login or forgot-password, send them to home
  if (publicRoutes.includes(to.name) && user.value) {
    return next('/home')
  }

  // If route is not public and user is not logged in, send them to login
  if (!publicRoutes.includes(to.name) && !user.value) {
    return next('/login')
  }

  // Otherwise, allow navigation
  return next()
})

export default router
