<script setup>
//Import necessary modules
import { useRouter } from "vue-router";
import { useAuth } from "../contexts/authContext";

const router = useRouter(); //Get router instance
const { user, logout } = useAuth(); //Get user and logout function from auth context

//Function to handle user logout
async function handleLogout() {
  try {
    await logout();
    //After logging out, send the user to the login page
    router.push("/login");
  } catch (err) {
    //Log any errors that occur during logout
    console.error("Error logging out:", err);
  }
}
</script>

<!--Template for the home page-->
<template>
  <main style="padding: 2rem;">
    <h1>Home</h1>

    <p v-if="user">
      Welcome, <strong>{{ user.email }}</strong>
    </p>
    <p v-else>
      Welcome, guest
    </p>

    <button @click="handleLogout">Logout</button>
  </main>
</template>
