<script setup>
//Import necessary modules
import { useRouter } from 'vue-router'
import { useAuth } from '../contexts/authContext'

import Sidebar from '../components/Sidebar.vue'

const router = useRouter() //Get router instance
const { user, logout } = useAuth() //Get user and logout function from auth context

//Function to handle user logout
async function handleLogout() {
  try {
    await logout()
    //After logging out, send the user to the login page
    router.push('/login')
  } catch (err) {
    //Log any errors that occur during logout
    console.error('Error logging out:', err)
  }
}
</script>

<!--Template for the home page-->
<template>
  <div class="flex min-h-screen">
    <Sidebar/>
  </div>
</template>
