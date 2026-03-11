<script setup>
import { computed, nextTick, ref } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import CancelButton from '../components/CancelButton.vue'

const activeTab = ref('customers')
const searchQuery = ref('')
const resourceTypeFilter = ref('all')
const feedbackMessage = ref('')

const customers = ref([
  {
    id: 1,
    name: 'Marie Schrader',
    email: 'Marie@DEA.com',
    phone: 'Not Provided',
    visits: 11,
    dateAdded: '12/22/2020',
  },
  {
    id: 2,
    name: 'Marla Singer',
    email: 'Marla@1strule.com',
    phone: '+1 (587) 822-9090',
    visits: 3,
    dateAdded: '08/18/2025',
  },
  {
    id: 3,
    name: 'Obi Wan Kenobi',
    email: 'BenKenobi@general.com',
    phone: 'Not Provided',
    visits: 5,
    dateAdded: '05/09/2023',
  },
  {
    id: 4,
    name: 'Mike Ehrmantraut',
    email: 'Mike@polloshermanos.com',
    phone: '+1 (598) 766-5544',
    visits: 12,
    dateAdded: '03/17/2021',
  },
  {
    id: 5,
    name: 'Vicenta Benito',
    email: 'Vicenta@show.com.es',
    phone: '+34 (91)123-4567',
    visits: 2,
    dateAdded: '07/30/2024',
  },
])

const guides = ref([
  {
    id: 101,
    name: 'Edward Elric',
    email: 'Edward@amestris.com',
    phone: 'Not Provided',
    startDate: '12/22/2020',
    endDate: 'Still Active',
  },
  {
    id: 102,
    name: 'Jonathan Wick',
    email: 'John@hightable.com',
    phone: '+1 (587) 822-9090',
    startDate: '12/01/2018',
    endDate: '08/18/2025',
  },
  {
    id: 103,
    name: 'Ignacio Varga',
    email: 'Nacho@salamanca.com',
    phone: '+1 (598) 766-5544',
    startDate: '07/30/2002',
    endDate: '03/17/2004',
  },
  {
    id: 104,
    name: 'Lucas Lucas',
    email: 'Lucas@oceanarium.com',
    phone: '+49 69 1234 5678',
    startDate: '10/20/2025',
    endDate: 'Still Active',
  },
  {
    id: 105,
    name: 'Lauren Ipsum',
    email: 'Lauren@oceanarium.com',
    phone: 'Not Provided',
    startDate: '06/09/2025',
    endDate: 'Still Active',
  },
])

const resources = ref([
  {
    id: 201,
    name: 'Room Anchovy',
    type: 'Room',
    availableQuantity: '-',
    totalQuantity: 1,
    status: 'Available',
    notes: 'Check AC unit',
  },
  {
    id: 202,
    name: 'Headphones',
    type: 'Audio Guides',
    availableQuantity: 30,
    totalQuantity: 50,
    status: 'Low Stock',
    notes: 'Order more',
  },
  {
    id: 203,
    name: 'Maps',
    type: 'Material',
    availableQuantity: 100,
    totalQuantity: 150,
    status: 'Available',
    notes: 'None',
  },
  {
    id: 204,
    name: 'Black Boards',
    type: 'Material',
    availableQuantity: 15,
    totalQuantity: 20,
    status: 'Available',
    notes: 'None',
  },
  {
    id: 205,
    name: 'Televisions',
    type: 'Digital Equipment',
    availableQuantity: 10,
    totalQuantity: 12,
    status: 'Available',
    notes: 'Fix unit #3',
  },
])

const editDialogOpen = ref(false)
const editingDraft = ref({})
const editDialogRef = ref(null)

const pageTitle = computed(() => {
  if (activeTab.value === 'guides') return 'Guides'
  if (activeTab.value === 'resources') return 'Resources'
  return 'Customers'
})

const listTitle = computed(() => {
  if (activeTab.value === 'guides') return 'Guides list'
  if (activeTab.value === 'resources') return 'Resources list'
  return 'Customer list'
})

const searchPlaceholder = computed(() => {
  if (activeTab.value === 'guides') return 'Search guides'
  if (activeTab.value === 'resources') return 'Search resources'
  return 'Search customers'
})

const resourceTypes = computed(() => {
  const typeMap = new Map()

  for (const item of resources.value) {
    if (!item.type) continue
    const value = item.type.toLowerCase()
    if (!typeMap.has(value)) {
      typeMap.set(value, item.type)
    }
  }

  return Array.from(typeMap.entries()).map(([value, label]) => ({ value, label }))
})

const filteredRows = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  if (activeTab.value === 'customers') {
    return customers.value.filter((item) => {
      const target = `${item.name} ${item.email} ${item.phone}`.toLowerCase()
      return target.includes(query)
    })
  }

  if (activeTab.value === 'guides') {
    return guides.value.filter((item) => {
      const target = `${item.name} ${item.email} ${item.phone}`.toLowerCase()
      return target.includes(query)
    })
  }

  return resources.value.filter((item) => {
    const target = `${item.name} ${item.type} ${item.notes} ${item.status}`.toLowerCase()
    const matchesSearch = target.includes(query)
    const matchesType =
      resourceTypeFilter.value === 'all' || item.type.toLowerCase() === resourceTypeFilter.value
    return matchesSearch && matchesType
  })
})

const totalCount = computed(() => {
  if (activeTab.value === 'guides') return guides.value.length
  if (activeTab.value === 'resources') return resources.value.length
  return customers.value.length
})

function switchTab(tab) {
  activeTab.value = tab
  searchQuery.value = ''
  resourceTypeFilter.value = 'all'
  feedbackMessage.value = ''
}

function openEdit(row) {
  editingDraft.value = { ...row }
  editDialogOpen.value = true
  nextTick(() => {
    editDialogRef.value?.focus()
  })
}

function closeEdit() {
  editDialogOpen.value = false
  editingDraft.value = {}
}

function saveEdit() {
  const targetList =
    activeTab.value === 'customers'
      ? customers.value
      : activeTab.value === 'guides'
        ? guides.value
        : resources.value

  const idx = targetList.findIndex((item) => item.id === editingDraft.value.id)
  if (idx !== -1) {
    targetList[idx] = { ...editingDraft.value }
    feedbackMessage.value = `${pageTitle.value.slice(0, -1)} record updated in prototype state.`
  }
  closeEdit()
}

function removeRow(id) {
  if (activeTab.value === 'customers') {
    customers.value = customers.value.filter((item) => item.id !== id)
    feedbackMessage.value = 'Customer removed in prototype state.'
  }

  if (activeTab.value === 'guides') {
    guides.value = guides.value.filter((item) => item.id !== id)
    feedbackMessage.value = 'Guide removed in prototype state.'
  }
}

function statusClasses(status) {
  if (status === 'Low Stock') return 'bg-amber-100 text-amber-800 border-amber-200'
  if (status === 'In Use') return 'bg-blue-100 text-blue-800 border-blue-200'
  return 'bg-emerald-100 text-emerald-800 border-emerald-200'
}
</script>

<template>
  <div class="flex min-h-screen bg-[#F4F7FA] overflow-x-hidden">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 lg:p-8">
      <section class="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 class="text-3xl font-semibold text-gray-900">{{ pageTitle }}</h1>
          <p class="text-sm text-gray-500">Frontend prototype only. No backend persistence.</p>
        </div>

        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="px-3 py-2 rounded-lg text-sm font-medium border transition"
            :class="
              activeTab === 'customers'
                ? 'bg-[#0EA5E9] text-white border-[#0EA5E9]'
                : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
            "
            @click="switchTab('customers')"
          >
            Customers
          </button>
          <button
            type="button"
            class="px-3 py-2 rounded-lg text-sm font-medium border transition"
            :class="
              activeTab === 'guides'
                ? 'bg-[#0EA5E9] text-white border-[#0EA5E9]'
                : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
            "
            @click="switchTab('guides')"
          >
            Guides
          </button>
          <button
            type="button"
            class="px-3 py-2 rounded-lg text-sm font-medium border transition"
            :class="
              activeTab === 'resources'
                ? 'bg-[#0EA5E9] text-white border-[#0EA5E9]'
                : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
            "
            @click="switchTab('resources')"
          >
            Resources
          </button>
        </div>
      </section>

      <section class="mb-4 flex flex-col md:flex-row gap-3 md:items-center">
        <div class="relative flex-1 max-w-xl">
          <input
            v-model="searchQuery"
            type="search"
            :placeholder="searchPlaceholder"
            class="w-full rounded-lg border border-gray-300 bg-white pl-10 pr-4 py-2.5 text-sm text-gray-800 outline-none focus:ring-2 focus:ring-sky-200"
          />
          <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">⌕</span>
        </div>

        <select
          v-if="activeTab === 'resources'"
          v-model="resourceTypeFilter"
          class="rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700"
        >
          <option value="all">All resources</option>
          <option v-for="rt in resourceTypes" :key="rt.value" :value="rt.value">
            {{ rt.label }}
          </option>
        </select>
      </section>

      <section class="rounded-xl border border-gray-200 bg-[#E9EEF2] shadow-sm overflow-hidden">
        <header class="px-4 md:px-5 py-4 border-b border-gray-300">
          <h2 class="text-3xl font-semibold text-gray-900 leading-tight">{{ listTitle }}</h2>
          <p class="text-sm text-gray-600">
            Total <span class="font-semibold text-gray-900">{{ totalCount }}</span>
          </p>
        </header>

        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead class="bg-[#DCE4EA] text-gray-700">
              <tr>
                <th class="px-4 py-3 text-left font-medium">Name</th>
                <th class="px-4 py-3 text-left font-medium">Email / Type</th>
                <th class="px-4 py-3 text-left font-medium">Phone / Available</th>
                <th class="px-4 py-3 text-left font-medium">Visits / Total</th>
                <th class="px-4 py-3 text-left font-medium">Date / Status</th>
                <th class="px-4 py-3 text-left font-medium">Notes</th>
                <th class="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-gray-300/70 text-gray-800">
              <tr v-if="filteredRows.length === 0">
                <td colspan="7" class="px-4 py-8 text-center text-gray-500">
                  No records found with the current filters.
                </td>
              </tr>

              <tr
                v-for="row in filteredRows"
                :key="row.id"
                class="hover:bg-[#DEE7EE] transition-colors"
              >
                <template v-if="activeTab === 'customers'">
                  <td class="px-4 py-3">{{ row.name }}</td>
                  <td class="px-4 py-3">{{ row.email }}</td>
                  <td class="px-4 py-3">{{ row.phone }}</td>
                  <td class="px-4 py-3">{{ row.visits }}</td>
                  <td class="px-4 py-3">{{ row.dateAdded }}</td>
                  <td class="px-4 py-3 text-gray-500">-</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        class="px-2.5 py-1.5 rounded border border-gray-300 text-xs"
                        @click="openEdit(row)"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        class="px-2.5 py-1.5 rounded border border-red-300 text-red-700 text-xs"
                        @click="removeRow(row.id)"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </template>

                <template v-else-if="activeTab === 'guides'">
                  <td class="px-4 py-3">{{ row.name }}</td>
                  <td class="px-4 py-3">{{ row.email }}</td>
                  <td class="px-4 py-3">{{ row.phone }}</td>
                  <td class="px-4 py-3">{{ row.startDate }}</td>
                  <td class="px-4 py-3">{{ row.endDate }}</td>
                  <td class="px-4 py-3 text-gray-500">-</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        class="px-2.5 py-1.5 rounded border border-gray-300 text-xs"
                        @click="openEdit(row)"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        class="px-2.5 py-1.5 rounded border border-red-300 text-red-700 text-xs"
                        @click="removeRow(row.id)"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </template>

                <template v-else>
                  <td class="px-4 py-3">{{ row.name }}</td>
                  <td class="px-4 py-3">{{ row.type }}</td>
                  <td class="px-4 py-3">{{ row.availableQuantity }}</td>
                  <td class="px-4 py-3">{{ row.totalQuantity }}</td>
                  <td class="px-4 py-3">
                    <span
                      class="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium"
                      :class="statusClasses(row.status)"
                    >
                      {{ row.status }}
                    </span>
                  </td>
                  <td class="px-4 py-3">{{ row.notes }}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        class="px-2.5 py-1.5 rounded border border-gray-300 text-xs"
                        @click="openEdit(row)"
                      >
                        Edit
                      </button>
                    </div>
                  </td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <p v-if="feedbackMessage" class="mt-3 text-sm text-emerald-700">
        {{ feedbackMessage }}
      </p>

      <div
        v-if="editDialogOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      >
        <div
          ref="editDialogRef"
          class="w-full max-w-lg rounded-xl border border-gray-200 bg-white p-5 shadow-xl"
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-dialog-title"
          tabindex="-1"
          @keydown.esc.prevent="closeEdit"
        >
          <h3 id="edit-dialog-title" class="text-lg font-semibold text-gray-900 mb-1">
            Edit Record
          </h3>
          <p class="text-sm text-gray-500 mb-4">
            Prototype dialog. Changes are local to this page state.
          </p>

          <div class="grid grid-cols-1 gap-3">
            <label class="text-sm text-gray-700">
              Name
              <input
                v-model="editingDraft.name"
                type="text"
                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
              />
            </label>

            <label v-if="activeTab !== 'resources'" class="text-sm text-gray-700">
              Email
              <input
                v-model="editingDraft.email"
                type="email"
                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
              />
            </label>

            <label v-if="activeTab !== 'resources'" class="text-sm text-gray-700">
              Phone
              <input
                v-model="editingDraft.phone"
                type="text"
                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
              />
            </label>

            <label v-if="activeTab === 'resources'" class="text-sm text-gray-700">
              Notes
              <input
                v-model="editingDraft.notes"
                type="text"
                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
              />
            </label>
          </div>

          <div class="mt-5 flex justify-end gap-2">
            <CancelButton class="px-3 py-2 text-sm" @cancel="closeEdit" />
            <button type="button" class="px-3 py-2 rounded-lg bg-[#0EA5E9] text-white text-sm" @click="saveEdit">Save</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
