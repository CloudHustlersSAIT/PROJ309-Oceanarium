<template>
  <div class="app-page-wrap">
    <section class="app-surface-card app-section-padding">
      <div class="flex flex-wrap items-start justify-between gap-3 sm:items-center">
        <div>
          <h1 class="app-title">Notifications</h1>
          <p class="app-subtitle">Recent updates</p>
        </div>

        <div class="flex w-full flex-wrap items-center gap-2 sm:w-auto sm:gap-3">
          <button
            @click="archiveAllNotifications"
            class="app-action-btn border border-black/15 text-[#1C1C1C] hover:bg-black/5 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="activeNotifications.length === 0"
          >
            Archive all
          </button>
          <button
            @click="markAllRead"
            class="app-action-btn border border-[#0077B6]/35 bg-[#EAF6FD] text-[#005A8A] hover:bg-[#D8EEFB]"
          >
            Mark all as read
          </button>
        </div>
      </div>

      <div class="mt-4 overflow-x-auto pb-1">
        <div class="inline-flex rounded-xl border border-black/10 bg-white p-1">
        <button
          type="button"
          class="app-action-btn whitespace-nowrap"
          :class="viewMode === 'active' ? 'bg-[#CAF0F8] text-[#1C1C1C] ring-1 ring-[#00B4D8]/35' : 'text-black/75 hover:bg-black/5'"
          @click="viewMode = 'active'"
        >
          Active Notifications
        </button>
        <button
          type="button"
          class="app-action-btn whitespace-nowrap"
          :class="viewMode === 'archived' ? 'bg-[#CAF0F8] text-[#1C1C1C] ring-1 ring-[#00B4D8]/35' : 'text-black/75 hover:bg-black/5'"
          @click="viewMode = 'archived'"
        >
          Archived Notifications
        </button>
        </div>
      </div>

      <div class="mt-5 space-y-3">
        <div
          v-for="notification in visibleNotifications"
          :key="notification.id"
          class="p-3.5 sm:p-4"
          :class="notificationCardClass(notification)"
        >
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="app-body-title leading-snug">
                {{ notification.message }}
              </p>
              <p class="mt-1 text-sm font-medium text-black/70">
                {{ notification.time }}
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
              <button
                v-if="!notification.archived"
                type="button"
                class="app-action-btn border border-[#0077B6]/35 bg-[#EAF6FD] text-[#005A8A] hover:bg-[#D8EEFB]"
                @click="archiveNotification(notification.id)"
              >
                Archive
              </button>
              <button
                v-else
                type="button"
                class="app-action-btn border border-[#0077B6]/35 bg-[#EAF6FD] text-[#005A8A] hover:bg-[#D8EEFB]"
                @click="restoreNotification(notification.id)"
              >
                Restore
              </button>
              <button
                type="button"
                class="app-action-btn border border-[#E63946]/45 bg-[#FFF1F2] text-[#B91C1C] hover:bg-[#FFE4E6]"
                @click="deleteNotification(notification.id)"
              >
                Delete
              </button>
            </div>
          </div>
        </div>

        <div v-if="visibleNotifications.length === 0" class="text-sm text-black/60">
          {{ viewMode === "active" ? "You're all caught up!" : "No archived notifications yet." }}
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const notifications = ref([
  {
    id: 1,
    message: "You have a new swap request.",
    time: "5 minutes ago",
    read: false,
    archived: false,
  },
  {
    id: 2,
    message: "Your schedule was updated.",
    time: "2 hours ago",
    read: false,
    archived: false,
  },
]);
const viewMode = ref("active");

const activeNotifications = computed(() =>
  notifications.value.filter((n) => !n.archived)
);
const archivedNotifications = computed(() =>
  notifications.value.filter((n) => n.archived)
);
const visibleNotifications = computed(() =>
  viewMode.value === "active" ? activeNotifications.value : archivedNotifications.value
);
const unreadCount = computed(
  () => activeNotifications.value.filter((n) => !n.read).length
);

watch(
  unreadCount,
  (count) => {
    localStorage.setItem("guideUnreadNotifications", String(count));
    window.dispatchEvent(
      new CustomEvent("guide-unread-updated", { detail: count })
    );
  },
  { immediate: true }
);

function markAllRead() {
  notifications.value = notifications.value.map((n) => ({
    ...n,
    read: true,
  }));
}

function archiveNotification(id) {
  notifications.value = notifications.value.map((n) =>
    n.id === id ? { ...n, archived: true } : n
  );
}

function deleteNotification(id) {
  notifications.value = notifications.value.filter((n) => n.id !== id);
}

function restoreNotification(id) {
  notifications.value = notifications.value.map((n) =>
    n.id === id ? { ...n, archived: false } : n
  );
}

function archiveAllNotifications() {
  notifications.value = notifications.value.map((n) =>
    n.archived ? n : { ...n, archived: true }
  );
}

function notificationCardClass(notification) {
  if (!notification.read) {
    return "notification-card-unread";
  }

  return "notification-card";
}
</script>

