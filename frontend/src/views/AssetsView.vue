<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import { getCustomers, getGuides } from '../services/api'

const tabs = [
  { key: 'customers', label: 'Customers' },
  { key: 'guides', label: 'Guides' },
]

const activeTab = ref('customers')
const searchQuery = ref('')
const isLoading = ref(false)
const apiError = ref('')

const customers = ref([])
const guides = ref([])
const currentPage = ref(1)
const pageSize = 15
const customerSort = ref('a-z')
const guideSort = ref('a-z')

const pageTitle = computed(() =>
  activeTab.value === 'guides' ? 'Guide Directory' : 'Customer Directory',
)

const listTitle = computed(() =>
  activeTab.value === 'guides' ? 'Registered guides' : 'Active customers',
)

const searchPlaceholder = computed(() =>
  activeTab.value === 'guides'
    ? 'Search by guide name, email, phone or status'
    : 'Search by customer name, email, id or phone',
)

const sortOptions = computed(() => {
  if (activeTab.value === 'guides') {
    return [
      { value: 'a-z', label: 'A to Z' },
      { value: 'z-a', label: 'Z to A' },
      { value: 'status', label: 'Status' },
    ]
  }

  return [
    { value: 'a-z', label: 'A to Z' },
    { value: 'z-a', label: 'Z to A' },
  ]
})

const currentSort = computed({
  get() {
    return activeTab.value === 'guides' ? guideSort.value : customerSort.value
  },
  set(value) {
    if (activeTab.value === 'guides') {
      guideSort.value = value
    } else {
      customerSort.value = value
    }
  },
})

const currentRows = computed(() => {
  const rows = activeTab.value === 'guides' ? [...guides.value] : [...customers.value]

  return rows.sort((left, right) => {
    if (activeTab.value === 'guides' && currentSort.value === 'status') {
      const statusComparison = String(left.status || '').localeCompare(String(right.status || ''), undefined, {
        sensitivity: 'base',
      })

      if (statusComparison !== 0) return statusComparison
    }

    const nameComparison = String(left.name || '').localeCompare(String(right.name || ''), undefined, {
      sensitivity: 'base',
    })

    if (currentSort.value === 'z-a') return nameComparison * -1
    return nameComparison
  })
})

const totalCount = computed(() => currentRows.value.length)

const summaryCards = computed(() => {
  if (activeTab.value === 'customers') {
    const returning = customers.value.filter((item) => Number(item.totalVisits) > 1).length
    return [
      { label: 'Total customers', value: customers.value.length },
      { label: 'Returning customers', value: returning },
      {
        label: 'New this year',
        value: customers.value.filter((item) =>
          item.firstTourDate?.startsWith(new Date().getFullYear().toString()),
        ).length,
      },
    ]
  }

  const active = guides.value.filter((item) => item.status === 'active').length
  return [
    { label: 'Total guides', value: guides.value.length },
    { label: 'Active guides', value: active },
    { label: 'Inactive guides', value: Math.max(0, guides.value.length - active) },
  ]
})

const filteredRows = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return currentRows.value.filter((row) => {
    const searchable = Object.values(row)
      .map((value) => String(value ?? ''))
      .join(' ')
      .toLowerCase()

    return searchable.includes(query)
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / pageSize)))

const paginatedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

const paginationRange = computed(() => {
  const pages = []
  const total = totalPages.value
  const page = currentPage.value

  if (total <= 7) {
    for (let index = 1; index <= total; index += 1) pages.push(index)
    return pages
  }

  pages.push(1)

  if (page > 3) pages.push('ellipsis-left')

  const start = Math.max(2, page - 1)
  const end = Math.min(total - 1, page + 1)

  for (let index = start; index <= end; index += 1) {
    pages.push(index)
  }

  if (page < total - 2) pages.push('ellipsis-right')

  pages.push(total)

  return pages
})

const paginationLabel = computed(() => {
  if (filteredRows.value.length === 0) return 'No records to display'

  const start = (currentPage.value - 1) * pageSize + 1
  const end = Math.min(currentPage.value * pageSize, filteredRows.value.length)
  return `Showing ${start}-${end} of ${filteredRows.value.length}`
})

const currentColumns = computed(() => {
  if (activeTab.value === 'customers') {
    return [
      { key: 'name', label: 'Customer' },
      { key: 'email', label: 'Email' },
      { key: 'customerId', label: 'Customer ID' },
      { key: 'totalVisits', label: 'Visits' },
      { key: 'firstTourDate', label: 'First Tour' },
      { key: 'phone', label: 'Phone' },
    ]
  }

  return [
    { key: 'id', label: 'Guide ID' },
    { key: 'name', label: 'Guide' },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: 'Phone' },
    { key: 'status', label: 'Status' },
    
  ]
})

function isCenteredColumn(columnKey) {
  return columnKey === 'totalVisits' || columnKey === 'id'
}

function normalizeCustomerRow(item, idx) {
  return {
    id: idx + 1,
    name: String(item?.full_name || item?.name || 'Unknown'),
    email: String(item?.email || 'Not provided'),
    customerId: String(item?.clorian_client_id || 'N/A'),
    totalVisits: Number(item?.total_visits) || 0,
    firstTourDate: item?.first_tour_date ? String(item.first_tour_date).slice(0, 10) : '-',
    phone: String(item?.phone || 'Not provided'),
  }
}

function normalizeGuideRow(item) {
  const firstName = String(item?.first_name || '').trim()
  const lastName = String(item?.last_name || '').trim()
  const fullName = `${firstName} ${lastName}`.trim()
  return {
    id: item?.id ?? 'N/A',
    name: fullName || String(item?.name || 'Unknown'),
    email: String(item?.email || 'Not provided'),
    phone: String(item?.phone || 'Not provided'),
    status: String(item?.active ? 'active' : item?.status || 'inactive').toLowerCase(),
  }
}

async function loadCustomers() {
  const data = await getCustomers()
  customers.value = Array.isArray(data)
    ? data.map((item, idx) => normalizeCustomerRow(item, idx))
    : []
}

async function loadGuides() {
  const data = await getGuides()
  guides.value = Array.isArray(data) ? data.map((item) => normalizeGuideRow(item)) : []
}

async function loadTabData(tab) {
  isLoading.value = true
  apiError.value = ''

  try {
    if (tab === 'customers') await loadCustomers()
    else if (tab === 'guides') await loadGuides()
  } catch (error) {
    apiError.value = String(error?.message || 'Failed to load data from API.')
  } finally {
    isLoading.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
  searchQuery.value = ''
  currentPage.value = 1
  apiError.value = ''
  loadTabData(tab)
}

function goToPage(page) {
  currentPage.value = Math.min(Math.max(1, page), totalPages.value)
}

// Debounce page reset so fast typing doesn't trigger excessive recomputation.
let searchDebounceTimer = null
watch(searchQuery, () => {
  clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    currentPage.value = 1
  }, 250)
})

watch(currentSort, () => {
  currentPage.value = 1
})

watch(filteredRows, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }
})

function statusClasses(status) {
  if (String(status).toLowerCase() === 'inactive') {
    return 'bg-rose-100 text-rose-800 border-rose-300'
  }
  return 'bg-emerald-100 text-emerald-800 border-emerald-300'
}

onMounted(() => {
  loadTabData(activeTab.value)
})
</script>

<template>
  <div class="flex min-h-screen bg-slate-100 overflow-x-hidden">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 xl:p-8">
      <section class="rounded-2xl border border-slate-200 bg-white shadow-sm p-4 md:p-6">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 class="text-2xl md:text-3xl font-semibold text-slate-900">{{ pageTitle }}</h1>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              type="button"
              class="px-4 py-2 rounded-xl text-sm font-medium border transition"
              :class="
                activeTab === tab.key
                  ? 'bg-[#0077B6] text-white border-[#0077B6]'
                  : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
              "
              @click="switchTab(tab.key)"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <div class="mt-5 grid grid-cols-1 md:grid-cols-3 gap-3">
          <article
            v-for="card in summaryCards"
            :key="card.label"
            class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
          >
            <p class="text-xs font-medium uppercase tracking-wide text-slate-500">{{ card.label }}</p>
            <p class="text-2xl font-semibold text-slate-900 mt-1">{{ card.value }}</p>
          </article>
        </div>

        <div class="mt-5 flex flex-col gap-3 lg:flex-row lg:items-end">
          <div class="relative flex-1">
            <input
              v-model="searchQuery"
              type="search"
              :placeholder="searchPlaceholder"
              class="w-full rounded-xl border border-slate-300 bg-white pl-10 pr-4 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200"
            />
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">⌕</span>
          </div>

          <label class="flex flex-col gap-1 text-sm text-slate-600 lg:w-52">
            <span class="font-medium text-slate-700">Sort by</span>
            <select
              v-model="currentSort"
              class="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-sky-200"
            >
              <option v-for="option in sortOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>

        <p
          v-if="apiError"
          class="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
        >
          {{ apiError }}
        </p>

      </section>

      <section class="mt-5 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <header class="px-4 md:px-5 py-4 border-b border-slate-200">
          <h2 class="text-xl font-semibold text-slate-900">{{ listTitle }}</h2>
          <p class="text-sm text-slate-500">
            Showing <span class="font-semibold text-slate-900">{{ paginatedRows.length }}</span> of
            <span class="font-semibold text-slate-900">{{ totalCount }}</span>
          </p>
        </header>

        <div v-if="isLoading" class="p-8 text-sm text-slate-500 text-center">Loading data...</div>

        <template v-else>
          <div class="hidden md:block overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead class="bg-slate-300 text-slate-700">
                <tr>
                  <th
                    v-for="column in currentColumns"
                    :key="column.key"
                    class="px-4 py-3 font-bold whitespace-nowrap"
                    :class="isCenteredColumn(column.key) ? 'text-center' : 'text-left'"
                  >
                    {{ column.label }}
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 text-slate-800">
                <tr v-if="paginatedRows.length === 0">
                  <td :colspan="currentColumns.length" class="px-4 py-10 text-center text-slate-500">
                    No records found for the current filters.
                  </td>
                </tr>

                <tr v-for="row in paginatedRows" :key="`${activeTab}-${row.id}`" class="hover:bg-slate-50">
                  <td
                    v-for="column in currentColumns"
                    :key="column.key"
                    class="px-4 py-3 align-top"
                    :class="isCenteredColumn(column.key) ? 'text-center' : 'text-left'"
                  >
                    <span
                      v-if="column.key === 'status'"
                      class="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium"
                      :class="statusClasses(row.status)"
                    >
                      {{ row.status }}
                    </span>
                    <span v-else>{{ row[column.key] }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="md:hidden space-y-3 p-3">
            <article
              v-for="row in paginatedRows"
              :key="`mobile-${activeTab}-${row.id}`"
              class="rounded-xl border border-slate-200 p-3 bg-slate-50"
            >
              <div class="flex items-start justify-between gap-3">
                <h3 class="font-semibold text-slate-900">{{ row.name }}</h3>
                <span
                  v-if="row.status"
                  class="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium"
                  :class="statusClasses(row.status)"
                >
                  {{ row.status }}
                </span>
              </div>

              <div class="mt-2 grid grid-cols-1 gap-1 text-sm text-slate-600">
                <p
                  v-for="column in currentColumns.filter((item) => item.key !== 'name' && item.key !== 'status')"
                  :key="column.key"
                >
                  <span class="font-medium text-slate-700">{{ column.label }}:</span>
                  {{ row[column.key] }}
                </p>
              </div>
            </article>

            <div
              v-if="paginatedRows.length === 0"
              class="rounded-xl border border-slate-200 p-5 text-center text-sm text-slate-500 bg-slate-50"
            >
              No records found for the current filters.
            </div>
          </div>

          <footer
            v-if="filteredRows.length > pageSize"
            class="border-t border-slate-200 px-4 py-4 md:px-5"
          >
            <div
              aria-label="Pagination"
              class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
              role="navigation"
            >
              <p class="text-sm text-slate-500">{{ paginationLabel }}</p>

              <div class="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium transition"
                  :class="
                    currentPage === 1
                      ? 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400'
                      : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                  "
                  :disabled="currentPage === 1"
                  @click="goToPage(currentPage - 1)"
                >
                  <span aria-hidden="true">‹</span>
                  Previous
                </button>

                <template v-for="item in paginationRange" :key="item">
                  <span
                    v-if="String(item).includes('ellipsis')"
                    class="inline-flex h-10 min-w-10 items-center justify-center rounded-xl border border-transparent px-2 text-sm text-slate-400"
                    aria-hidden="true"
                  >
                    ...
                  </span>

                  <button
                    v-else
                    type="button"
                    class="inline-flex h-10 min-w-10 items-center justify-center rounded-xl border px-3 text-sm font-medium transition"
                    :class="
                      currentPage === item
                        ? 'border-[#0077B6] bg-[#0077B6] text-white'
                        : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                    "
                    :aria-current="currentPage === item ? 'page' : undefined"
                    :aria-label="`Go to page ${item}`"
                    @click="goToPage(item)"
                  >
                    {{ item }}
                  </button>
                </template>

                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium transition"
                  :class="
                    currentPage === totalPages
                      ? 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400'
                      : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                  "
                  :disabled="currentPage === totalPages"
                  @click="goToPage(currentPage + 1)"
                >
                  Next
                  <span aria-hidden="true">›</span>
                </button>
              </div>
            </div>
          </footer>
        </template>
      </section>
    </main>
  </div>
</template>
