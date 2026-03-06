<template>
  <div class="space-y-6">
    <!-- Page header -->
    <section class="rounded-2xl bg-white border border-black/10 shadow-sm p-6">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 class="text-2xl font-semibold text-[#1C1C1C]">My Profile</h1>
          <p class="text-sm text-black/60">
            View and update your guide preferences.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span
            class="inline-flex items-center rounded-full bg-[#CAF0F8] px-3 py-1 text-xs font-semibold text-[#0077B6] ring-1 ring-[#00B4D8]/40"
          >
            Role: Guide
          </span>

          <span
            class="inline-flex items-center rounded-full bg-[#2A9D8F]/10 px-3 py-1 text-xs font-semibold text-[#2A9D8F]"
          >
            Status: Active
          </span>
        </div>
      </div>
    </section>

    <!-- Content grid -->
    <section class="grid gap-4 md:grid-cols-3">
      <!-- Left: identity card -->
      <div class="md:col-span-1 rounded-2xl bg-white border border-black/10 shadow-sm p-6">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-[#CAF0F8] ring-1 ring-[#00B4D8]/40 flex items-center justify-center">
            <span class="text-[#0077B6] font-bold">
              {{ initials }}
            </span>
          </div>
          <div class="leading-tight">
            <p class="text-sm text-black/60">Signed in as</p>
            <p class="text-base font-semibold text-[#1C1C1C]">
              {{ displayName }}
            </p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <div class="rounded-xl border border-black/10 p-4">
            <p class="text-xs text-black/60">Email</p>
            <p class="text-sm font-semibold text-[#1C1C1C] break-all">
              {{ displayEmail }}
            </p>
          </div>

          <div class="rounded-xl border border-black/10 p-4">
            <p class="text-xs text-black/60">Employee ID</p>
            <p class="text-sm font-semibold text-[#1C1C1C]">
              {{ employeeId }}
            </p>
          </div>
        </div>

        <div class="mt-5">
          <button
            type="button"
            class="w-full rounded-xl border border-[#0077B6] px-4 py-3 text-sm font-semibold text-[#0077B6] hover:bg-[#CAF0F8] transition"
            @click="resetToDefaults"
          >
            Reset to default
          </button>
        </div>
      </div>

      <!-- Right: editable form -->
      <div class="md:col-span-2 rounded-2xl bg-white border border-black/10 shadow-sm p-6">
        <h2 class="text-lg font-semibold text-[#1C1C1C]">Preferences</h2>
        <p class="text-sm text-black/60">These settings help admins schedule you better.</p>

        <form class="mt-5 space-y-5" @submit.prevent="saveProfile">
          <!-- Phone -->
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-[#1C1C1C]">Phone</label>
            <input
              v-model="form.phone"
              type="tel"
              class="w-full rounded-xl border border-black/10 px-4 py-3 text-sm outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6]"
              placeholder="e.g. (555) 123-4567"
            />
          </div>

          <!-- Languages -->
          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-2">
              <label class="block text-sm font-semibold text-[#1C1C1C]">Primary Language</label>
              <select
                v-model="form.primaryLanguage"
                class="w-full rounded-xl border border-black/10 px-4 py-3 text-sm outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6]"
              >
                <option>English</option>
                <option>French</option>
                <option>Spanish</option>
                <option>Portuguese</option>
                <option>Other</option>
              </select>
            </div>

            <div class="space-y-2">
              <label class="block text-sm font-semibold text-[#1C1C1C]">Secondary Language</label>
              <select
                v-model="form.secondaryLanguage"
                class="w-full rounded-xl border border-black/10 px-4 py-3 text-sm outline-none focus:border-[#0077B6] focus:ring-1 focus:ring-[#0077B6]"
              >
                <option value="">None</option>
                <option>English</option>
                <option>French</option>
                <option>Spanish</option>
                <option>Portuguese</option>
                <option>Other</option>
              </select>
            </div>
          </div>

          <!-- Preferred shifts -->
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-[#1C1C1C]">Preferred Shifts</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="shift in shifts"
                :key="shift"
                type="button"
                class="rounded-full px-4 py-2 text-sm font-semibold border transition"
                :class="chipClass(form.shifts, shift)"
                @click="toggleChip(form.shifts, shift)"
              >
                {{ shift }}
              </button>
            </div>
          </div>

          <!-- Available days -->
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-[#1C1C1C]">Available Days</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="day in days"
                :key="day"
                type="button"
                class="rounded-full px-4 py-2 text-sm font-semibold border transition"
                :class="chipClass(form.days, day)"
                @click="toggleChip(form.days, day)"
              >
                {{ day }}
              </button>
            </div>
          </div>

          <!-- Tour types -->
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-[#1C1C1C]">Preferred Tour Types</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="t in tourTypes"
                :key="t"
                type="button"
                class="rounded-full px-4 py-2 text-sm font-semibold border transition"
                :class="chipClass(form.tourTypes, t)"
                @click="toggleChip(form.tourTypes, t)"
              >
                {{ t }}
              </button>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 pt-2">
            <button
              type="submit"
              :disabled="saving"
              class="rounded-xl bg-[#0077B6] px-5 py-3 text-sm font-semibold text-white hover:bg-[#0097E7] disabled:opacity-60 disabled:cursor-not-allowed transition"
            >
              {{ saving ? "Saving..." : "Save Changes" }}
            </button>

            <button
              type="button"
              class="rounded-xl border border-black/10 px-5 py-3 text-sm font-semibold text-black/70 hover:bg-[#CAF0F8]/50 transition"
              @click="loadProfile"
            >
              Cancel
            </button>
          </div>

          <!-- Feedback -->
          <p
            v-if="toast"
            class="text-sm font-semibold"
            :class="toastType === 'success' ? 'text-[#2A9D8F]' : 'text-[#E63946]'"
          >
            {{ toast }}
          </p>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useAuth } from "@/contexts/authContext";
import { firebaseDisabled } from "@/utils/firebase";

const { user } = useAuth();

// Simple demo identity values
const displayEmail = computed(() => (firebaseDisabled ? "guest@local" : user?.value?.email || "unknown"));
const displayName = computed(() => {
  if (firebaseDisabled) return "Guest Guide";
  const email = user?.value?.email || "";
  return email ? email.split("@")[0] : "Guide";
});
const initials = computed(() => {
  const name = displayName.value || "G";
  const parts = name.replace(/[^a-zA-Z0-9 ]/g, " ").trim().split(/\s+/);
  const first = parts[0]?.[0] || "G";
  const second = parts[1]?.[0] || "";
  return (first + second).toUpperCase();
});
const employeeId = computed(() => "GD-" + (displayEmail.value || "000").slice(0, 3).toUpperCase());

// Options
const shifts = ["Morning", "Afternoon", "Evening"];
const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const tourTypes = ["Dolphins", "Reef", "Sharks", "Molluscs", "Deep Sea"];

// Storage key for demo persistence
const STORAGE_KEY = "guide_profile";

// Form state
const defaultProfile = () => ({
  phone: "",
  primaryLanguage: "English",
  secondaryLanguage: "",
  shifts: ["Morning"],
  days: ["Mon", "Tue", "Wed", "Thu", "Fri"],
  tourTypes: ["Dolphins", "Reef"],
});

const form = reactive(defaultProfile());
const saving = ref(false);
const toast = ref("");
const toastType = ref("success");

function chipClass(arr, value) {
  const active = arr.includes(value);
  return active
    ? "bg-[#CAF0F8] text-[#0077B6] border-[#00B4D8]/40"
    : "bg-white text-black/70 border-black/10 hover:bg-[#CAF0F8]/60";
}

function toggleChip(arr, value) {
  const idx = arr.indexOf(value);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(value);
}

function loadProfile() {
  toast.value = "";
  const raw = localStorage.getItem(STORAGE_KEY);
  const data = raw ? JSON.parse(raw) : null;
  const merged = data ? { ...defaultProfile(), ...data } : defaultProfile();

  Object.assign(form, merged);
}

function resetToDefaults() {
  localStorage.removeItem(STORAGE_KEY);
  Object.assign(form, defaultProfile());
  toastType.value = "success";
  toast.value = "Reset to default settings.";
  setTimeout(() => (toast.value = ""), 2000);
}

async function saveProfile() {
  toast.value = "";
  saving.value = true;

  try {
    // basic validation example
    if (form.phone && form.phone.length < 7) {
      toastType.value = "error";
      toast.value = "Phone number looks too short.";
      return;
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(form));
    toastType.value = "success";
    toast.value = "Profile saved successfully.";
    setTimeout(() => (toast.value = ""), 2000);
  } finally {
    saving.value = false;
  }
}

// Load profile when page opens
loadProfile();
</script>

