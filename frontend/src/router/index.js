// Import necessary modules
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../contexts/authContext'

//Import views
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {path: "/login", name: "login", component: LoginView},
    {path: "/home", name: "home", component: HomeView}, 
    //Default route to login page
    {path: "/", redirect: "/login"},
  ],
})

//Protect routes that require authentication
router.beforeEach((to, from, next) => {
  const { user, loading } = useAuth();

  // Wait for Firebase to load auth state
  if (loading.value) {
    return next();
  }

  // If user is authenticated and tries to access login → redirect to home
  if (to.name === "login" && user.value) {
    return next("/home");
  }

  // If route requires auth (anything not login) and user isn't logged in → redirect to login
  if (to.name !== "login" && !user.value) {
    return next("/login");
  }

  return next();
});

export default router
