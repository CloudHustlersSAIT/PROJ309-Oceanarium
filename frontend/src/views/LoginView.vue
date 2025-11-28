<script setup>
//Import necessary modules
import { ref } from "vue";
import { useAuth } from "../contexts/authContext";
import { useRouter } from "vue-router";

const { user, loading, error, loginWithEmail, signupWithEmail, logout } = useAuth(); //Get auth functions and state from auth context
const router = useRouter(); //Get router instance

const mode = ref("login"); // "login" or "signup"
const email = ref("");
const password = ref("");
const localError = ref(null);
const submitting = ref(false);

//Function to handle form submission for login/signup
async function handleSubmit() {
  localError.value = null;
  submitting.value = true;

  try {
    // Attempt to login or signup based on the current mode
    if (mode.value === "login") {
      await loginWithEmail(email.value, password.value);
    } else {
      await signupWithEmail(email.value, password.value);
    }

    //After successful login/signup, redirect to home page
    router.push("/home");

  } catch (err) {
    // Handle any errors that occur during login/signup
    localError.value = err.message || String(err);
  } finally {
    // Reset submitting state
    submitting.value = false;
  }
}

</script>

<!--Template for the login/signup page-->
<template>
  <main style="padding: 2rem; max-width: 400px;">
    <h1>{{ mode === "login" ? "Login" : "Sign Up" }}</h1>

    <p v-if="loading">Checking auth status...</p>

    <div v-else>
      <p v-if="user">Logged in as: <strong>{{ user.email }}</strong></p>

      <form @submit.prevent="handleSubmit" style="display: flex; flex-direction: column; gap: 0.5rem;">
        <input v-model="email" type="email" placeholder="Email" required />
        <input v-model="password" type="password" placeholder="Password" required />

        <button type="submit" :disabled="submitting">
          {{ submitting ? "Please wait..." : mode === "login" ? "Login" : "Create account" }}
        </button>
      </form>

      <p v-if="localError" style="color: red; margin-top: 0.5rem;">
        {{ localError }}
      </p>

      <p v-if="error && !localError" style="color: red; margin-top: 0.5rem;">
        {{ error.message || error }}
      </p>

      <div style="margin-top: 1rem;">
        <button type="button" @click="mode = 'login'">Switch to login</button>
        <button type="button" @click="mode = 'signup'">Switch to signup</button>
      </div>

      <div v-if="user" style="margin-top: 1rem;">
        <button type="button" @click="logout">Logout</button>
      </div>
    </div>
  </main>
</template>
