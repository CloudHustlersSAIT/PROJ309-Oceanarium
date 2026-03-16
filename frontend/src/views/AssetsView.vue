<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import CancelButton from '../components/CancelButton.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import SaveButton from '../components/SaveButton.vue'
import {
  createGuide,
  getCustomers,
  getGuides,
  getLanguages,
  getTours,
  updateCustomer,
  updateGuide,
} from '../services/api'

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
const tourOptions = ref([])
const languageOptions = ref([])
const hasLoadedGuideEditorOptions = ref(false)
const isLoadingGuideEditorOptions = ref(false)
const currentPage = ref(1)
const pageSize = 15
const customerSort = ref('a-z')
const guideSort = ref('a-z')
const showEditPopup = ref(false)
const showConfirmSavePopup = ref(false)
const showGuideDetailsPopup = ref(false)
const isSavingEdit = ref(false)
const editError = ref('')
const selectedGuideDetails = ref(null)
const editForm = ref({
  mode: 'edit',
  tab: 'customers',
  rowId: '',
  recordKey: '',
  firstName: '',
  lastName: '',
  email: '',
  selectedLanguageCodes: [],
  selectedTourIds: [],
  guideTimezone: 'UTC',
  dailyAvailability: {},
})

const WEEK_DAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const pageTitle = computed(() =>
  activeTab.value === 'guides' ? 'Guide Directory' : 'Customer Directory',
)

const listTitle = computed(() =>
  activeTab.value === 'guides' ? 'Registered guides' : 'Active customers',
)

const searchPlaceholder = computed(() =>
  activeTab.value === 'guides'
    ? 'Search by guide name, email or language'
    : 'Search by customer name, email or id',
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
  if (!query) return currentRows.value

  return currentRows.value.filter((row) => {
    const searchable = activeTab.value === 'guides'
      ? `${row.id ?? ''} ${row.name ?? ''} ${row.email ?? ''} ${row.languageCodesDisplay ?? ''} ${row.availabilityDisplay ?? ''} ${row.status ?? ''}`
      : `${row.name ?? ''} ${row.email ?? ''} ${row.customerId ?? ''} ${row.totalVisits ?? ''} ${row.firstTourDate ?? ''}`

    const normalizedSearchable = searchable.toLowerCase()

    return normalizedSearchable.includes(query)
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

const editTargetLabel = computed(() =>
  editForm.value.mode === 'create'
    ? 'New Guide'
    : editForm.value.tab === 'guides'
      ? `Guide #${editForm.value.rowId}`
      : `Customer ${editForm.value.recordKey}`,
)

const canSaveEdit = computed(() => {
  const firstName = String(editForm.value.firstName || '').trim()
  const lastName = String(editForm.value.lastName || '').trim()
  const email = String(editForm.value.email || '').trim()
  return Boolean(firstName) && Boolean(lastName) && Boolean(email)
})

const confirmMessage = computed(() =>
  editForm.value.mode === 'create'
    ? 'This will create a new guide using the backend API. Do you want to proceed?'
    : 'This will save changes using the backend API. Do you want to proceed?',
)

const currentColumns = computed(() => {
  if (activeTab.value === 'customers') {
    return [
      { key: 'name', label: 'Customer' },
      { key: 'email', label: 'Email' },
      { key: 'customerId', label: 'Customer ID' },
      { key: 'totalVisits', label: 'Visits' },
      { key: 'firstTourDate', label: 'First Tour' },
    ]
  }

  return [
    { key: 'id', label: 'Guide ID' },
    { key: 'name', label: 'Guide' },
    { key: 'email', label: 'Email' },
    { key: 'languageCodesDisplay', label: 'Languages' },
    { key: 'availabilityDisplay', label: 'Availability' },
    { key: 'status', label: 'Status' },
  ]
})

const languageLabelByCode = computed(() =>
  Object.fromEntries(
    languageOptions.value.map((language) => [
      String(language.code || '').toLowerCase(),
      language.label,
    ]),
  ),
)

const tourLabelById = computed(() =>
  Object.fromEntries(
    tourOptions.value.map((tour) => [String(tour.id), tour.label]),
  ),
)

const selectedGuideLanguageLabels = computed(() => {
  const guide = selectedGuideDetails.value
  const codes = Array.isArray(guide?.languageCodes) ? guide.languageCodes : []
  const labelsFromCodes = codes.map(
    (code) => languageLabelByCode.value[String(code).toLowerCase()] || String(code),
  )
  if (labelsFromCodes.length > 0) return labelsFromCodes
  return Array.isArray(guide?.languageLabels) ? guide.languageLabels : []
})

const selectedGuideTourLabels = computed(() => {
  const guide = selectedGuideDetails.value
  const ids = Array.isArray(guide?.expertiseTourIds) ? guide.expertiseTourIds : []
  const labelsFromIds = ids.map((id) => tourLabelById.value[String(id)] || `Tour #${id}`)
  if (labelsFromIds.length > 0) return labelsFromIds
  return Array.isArray(guide?.expertiseLabels) ? guide.expertiseLabels : []
})

const selectedGuideWeeklySchedule = computed(() => {
  const guide = selectedGuideDetails.value
  const firstPattern = Array.isArray(guide?.availabilityPatterns) && guide.availabilityPatterns.length
    ? guide.availabilityPatterns[0]
    : null
  const slots = Array.isArray(firstPattern?.slots) ? firstPattern.slots : []

  const slotsByDay = Object.fromEntries(
    slots.map((slot) => [String(slot.day_of_week || '').trim(), slot]),
  )

  return WEEK_DAYS.map((day) => {
    const slot = slotsByDay[day]
    return {
      day,
      text: slot ? `${slot.start_time} - ${slot.end_time}` : 'Off',
    }
  })
})

function isCenteredColumn(columnKey) {
  return columnKey === 'totalVisits' || columnKey === 'id'
}

function normalizeCustomerRow(item, idx) {
  const recordKey = String(item?.clorian_client_id || '').trim()

  return {
    id: idx + 1,
    name: String(item?.full_name || item?.name || 'Unknown'),
    email: String(item?.email || 'Not provided'),
    customerId: recordKey || 'N/A',
    recordKey,
    totalVisits: Number(item?.total_visits) || 0,
    firstTourDate: item?.first_tour_date ? String(item.first_tour_date).slice(0, 10) : '-',
    phone: String(item?.phone || 'Not provided'),
  }
}

function normalizeGuideRow(item) {
  function normalizeCollection(value) {
    if (!Array.isArray(value)) return []

    return value
      .map((entry) => {
        if (entry == null) return null
        if (typeof entry === 'string') {
          const trimmed = entry.trim()
          return trimmed ? { id: trimmed, label: trimmed } : null
        }
        if (typeof entry === 'number') {
          return { id: entry, label: String(entry) }
        }
        if (typeof entry === 'object') {
          const id = entry.id ?? entry.code ?? entry.name ?? entry.title
          const label = entry.name || entry.title || entry.code || entry.id
          if (id == null && label == null) return null
          return { id, label: String(label || id).trim() }
        }
        return null
      })
      .filter(Boolean)
  }

  const firstName = String(item?.first_name || '').trim()
  const lastName = String(item?.last_name || '').trim()
  const fullName = `${firstName} ${lastName}`.trim()
  const hasIsActive = typeof item?.is_active === 'boolean'
  const hasActive = typeof item?.active === 'boolean'
  const normalizedStatus = hasIsActive
    ? (item.is_active ? 'active' : 'inactive')
    : hasActive
      ? (item.active ? 'active' : 'inactive')
      : String(item?.status || 'inactive').toLowerCase()

  const languageCollection = normalizeCollection(item?.language_codes)
  const fallbackLanguageCollection = normalizeCollection(
    item?.languages ?? item?.spoken_languages ?? item?.language,
  )
  const expertiseCollection = normalizeCollection(item?.expertise_tour_ids)
  const fallbackExpertiseCollection = normalizeCollection(
    item?.expertise_tours ?? item?.tour_types ?? item?.tours ?? item?.expertise,
  )
  const availabilityPatterns = Array.isArray(item?.availability_patterns)
    ? item.availability_patterns
    : []
  const availabilityLabel = availabilityPatterns.length > 0
    ? `${availabilityPatterns.length} pattern(s)`
    : typeof item?.availability === 'boolean'
      ? item.availability ? 'Available' : 'Unavailable'
      : String(item?.availability_status || item?.availability || 'Not mapped').trim() || 'Not mapped'

  return {
    id: item?.id ?? 'N/A',
    firstName,
    lastName,
    name: fullName || String(item?.name || 'Unknown'),
    email: String(item?.email || 'Not provided'),
    phone: String(item?.phone || 'Not provided'),
    languageCodes: languageCollection.map((entry) => String(entry.id).toLowerCase()),
    languageLabels: (languageCollection.length > 0 ? languageCollection : fallbackLanguageCollection)
      .map((entry) => String(entry.label)),
    expertiseTourIds: expertiseCollection
      .map((entry) => Number(entry.id))
      .filter((entry) => Number.isInteger(entry) && entry > 0),
    expertiseLabels: (expertiseCollection.length > 0 ? expertiseCollection : fallbackExpertiseCollection)
      .map((entry) => String(entry.label)),
    availabilityPatterns,
    languageCodesDisplay: (languageCollection.length > 0 ? languageCollection : fallbackLanguageCollection)
      .map((entry) => String(entry.label))
      .join(', ') || 'Not mapped',
    expertiseDisplay: (expertiseCollection.length > 0 ? expertiseCollection : fallbackExpertiseCollection)
      .map((entry) => String(entry.label))
      .join(', ') || 'Not mapped',
    availabilityDisplay: availabilityLabel,
    status: normalizedStatus,
  }
}

function splitName(fullName) {
  const normalized = String(fullName || '').trim()
  if (!normalized) return { firstName: '', lastName: '' }

  const parts = normalized.split(/\s+/)
  if (parts.length === 1) return { firstName: parts[0], lastName: '' }

  return {
    firstName: parts[0],
    lastName: parts.slice(1).join(' '),
  }
}

function createDefaultDailyAvailability() {
  return Object.fromEntries(
    WEEK_DAYS.map((day) => [
      day,
      {
        enabled: false,
        start: '09:00:00',
        end: '17:00:00',
      },
    ]),
  )
}

function dailyAvailabilityFromPatterns(patterns) {
  const daily = createDefaultDailyAvailability()
  const firstPattern = Array.isArray(patterns) && patterns.length ? patterns[0] : null
  const slots = Array.isArray(firstPattern?.slots) ? firstPattern.slots : []

  for (const slot of slots) {
    const day = String(slot?.day_of_week || '').trim()
    if (!WEEK_DAYS.includes(day)) continue

    daily[day] = {
      enabled: true,
      start: String(slot?.start_time || '09:00:00'),
      end: String(slot?.end_time || '17:00:00'),
    }
  }

  return daily
}

function availabilityPatternsFromDaily() {
  const slots = WEEK_DAYS
    .filter((day) => editForm.value.dailyAvailability?.[day]?.enabled)
    .map((day) => {
      const config = editForm.value.dailyAvailability[day]
      return {
        day_of_week: day,
        start_time: config.start,
        end_time: config.end,
      }
    })

  return [
    {
      timezone: String(editForm.value.guideTimezone || 'UTC').trim() || 'UTC',
      slots,
    },
  ]
}

async function loadGuideEditorOptions() {
  if (hasLoadedGuideEditorOptions.value) return
  if (isLoadingGuideEditorOptions.value) return

  isLoadingGuideEditorOptions.value = true

  try {
    const [tours, languages] = await Promise.all([getTours(), getLanguages()])

    tourOptions.value = Array.isArray(tours)
      ? tours.map((tour) => ({ id: tour.id, label: `${tour.id} - ${tour.name}` }))
      : []

    languageOptions.value = Array.isArray(languages)
      ? languages.map((language) => ({
        id: language.id,
        code: String(language.code || '').toLowerCase(),
        label: `${language.name} (${String(language.code || '').toLowerCase()})`,
      }))
      : []

    hasLoadedGuideEditorOptions.value = true
  } finally {
    isLoadingGuideEditorOptions.value = false
  }
}

async function ensureGuideEditorOptionsLoaded() {
  if (hasLoadedGuideEditorOptions.value || isLoadingGuideEditorOptions.value) return

  try {
    await loadGuideEditorOptions()
  } catch (error) {
    apiError.value = String(error?.message || 'Failed to load guide editor options.')
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

  if (tab === 'guides') {
    ensureGuideEditorOptionsLoaded()
  }

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

function openGuideDetails(row) {
  selectedGuideDetails.value = row
  showGuideDetailsPopup.value = true
}

function closeGuideDetails() {
  showGuideDetailsPopup.value = false
  selectedGuideDetails.value = null
}

async function openEditPopup(row) {
  const rowId = String(row?.id ?? '')
  const recordKey = activeTab.value === 'guides' ? rowId : String(row?.recordKey || '').trim()
  const split = splitName(row?.name)

  if (activeTab.value === 'customers' && !recordKey) {
    editError.value = 'This customer does not have a valid backend identifier and cannot be edited.'
    return
  }

  if (activeTab.value === 'guides') {
    await ensureGuideEditorOptionsLoaded()
  }

  editForm.value = {
    mode: 'edit',
    tab: activeTab.value,
    rowId,
    recordKey,
    firstName: String(row?.firstName || split.firstName || '').trim(),
    lastName: String(row?.lastName || split.lastName || '').trim(),
    email: String(row?.email || '').trim(),
    selectedLanguageCodes: Array.isArray(row?.languageCodes) ? [...row.languageCodes] : [],
    selectedTourIds: Array.isArray(row?.expertiseTourIds) ? [...row.expertiseTourIds] : [],
    guideTimezone: Array.isArray(row?.availabilityPatterns) && row.availabilityPatterns.length
      ? String(row.availabilityPatterns[0]?.timezone || 'UTC')
      : 'UTC',
    dailyAvailability: dailyAvailabilityFromPatterns(row?.availabilityPatterns),
  }
  editError.value = ''
  showConfirmSavePopup.value = false
  showEditPopup.value = true
}

async function openCreateGuidePopup() {
  await ensureGuideEditorOptionsLoaded()

  editForm.value = {
    mode: 'create',
    tab: 'guides',
    rowId: '',
    recordKey: '',
    firstName: '',
    lastName: '',
    email: '',
    selectedLanguageCodes: [],
    selectedTourIds: [],
    guideTimezone: 'UTC',
    dailyAvailability: createDefaultDailyAvailability(),
  }
  editError.value = ''
  showConfirmSavePopup.value = false
  showEditPopup.value = true
}

function closeEditPopup() {
  if (isSavingEdit.value) return

  showConfirmSavePopup.value = false
  showEditPopup.value = false
  editError.value = ''
}

function requestEditConfirmation() {
  if (!canSaveEdit.value) {
    editError.value = 'First name, last name and email are required.'
    return
  }

  showConfirmSavePopup.value = true
}

async function applyRowEdit() {
  const normalizedFirstName = String(editForm.value.firstName || '').trim()
  const normalizedLastName = String(editForm.value.lastName || '').trim()
  const normalizedEmail = String(editForm.value.email || '').trim()

  isSavingEdit.value = true
  editError.value = ''

  try {
    if (editForm.value.tab === 'customers') {
      if (!String(editForm.value.recordKey || '').trim()) {
        throw new Error('Customer backend identifier is missing. Unable to update this customer.')
      }

      await updateCustomer(editForm.value.recordKey, {
        first_name: normalizedFirstName,
        last_name: normalizedLastName,
        email: normalizedEmail,
      })
    } else {
      const slots = WEEK_DAYS
        .filter((day) => editForm.value.dailyAvailability?.[day]?.enabled)
        .map((day) => editForm.value.dailyAvailability[day])

      if (!slots.length) {
        throw new Error('Select at least one working day for guide availability.')
      }

      if (slots.some((slot) => !slot.start || !slot.end || slot.start >= slot.end)) {
        throw new Error('Each enabled day must have a valid start/end time.')
      }

      const guidePayload = {
        first_name: normalizedFirstName,
        last_name: normalizedLastName,
        email: normalizedEmail,
        language_codes: [...editForm.value.selectedLanguageCodes],
        expertise_tour_ids: [...editForm.value.selectedTourIds],
        availability_patterns: availabilityPatternsFromDaily(),
      }

      if (editForm.value.mode === 'create') {
        await createGuide(guidePayload)
      } else {
        await updateGuide(editForm.value.rowId, guidePayload)
      }
    }

    await loadTabData(editForm.value.tab)
    showConfirmSavePopup.value = false
    showEditPopup.value = false
    editError.value = ''
  } catch (error) {
    editError.value = String(error?.message || 'Failed to save changes.')
  } finally {
    isSavingEdit.value = false
  }
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
            <h1 class="typo-page-title">{{ pageTitle }}</h1>
          </div>

          <div class="flex flex-wrap gap-2 items-center">
            <button
              v-if="activeTab === 'guides'"
              type="button"
              class="px-3 py-1.5 rounded text-sm font-semibold border bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700"
              @click="openCreateGuidePopup"
            >
              + Add Guide
            </button>

            <button
              v-for="tab in tabs"
              :key="tab.key"
              type="button"
              class="px-3 py-1.5 rounded text-sm font-semibold border transition-colors"
              :class="
                activeTab === tab.key
                  ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700'
                  : 'bg-white text-gray-700 border-[#ACBAC4] hover:bg-gray-50'
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
            <p class="typo-card-label">{{ card.label }}</p>
            <p class="typo-card-value">{{ card.value }}</p>
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
          <h2 class="typo-section-title">{{ listTitle }}</h2>
          <p class="typo-muted">
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
                  <th class="px-4 py-3 text-right font-bold whitespace-nowrap">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 text-slate-800">
                <tr v-if="paginatedRows.length === 0">
                  <td :colspan="currentColumns.length + 1" class="px-4 py-10 text-center text-slate-500">
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
                    <button
                      v-else-if="column.key === 'name' && activeTab === 'guides'"
                      type="button"
                      class="text-blue-700 underline hover:text-blue-900"
                      @click="openGuideDetails(row)"
                    >
                      {{ row[column.key] }}
                    </button>
                    <span v-else>{{ row[column.key] }}</span>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <button
                      type="button"
                      class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 text-slate-600 transition hover:bg-slate-100"
                      :aria-label="`Edit ${activeTab === 'guides' ? 'guide' : 'customer'} ${row.name}`"
                      @click="openEditPopup(row)"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.8"
                        class="h-4 w-4"
                        aria-hidden="true"
                      >
                        <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L9 17l-4 1 1-4L16.5 3.5Z" />
                        <path d="M14.5 5.5l4 4" />
                      </svg>
                    </button>
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
                <button
                  v-if="activeTab === 'guides'"
                  type="button"
                  class="font-semibold text-slate-900 text-left underline"
                  @click="openGuideDetails(row)"
                >
                  {{ row.name }}
                </button>
                <h3 v-else class="font-semibold text-slate-900">{{ row.name }}</h3>
                <div class="flex items-center gap-2">
                  <span
                    v-if="row.status"
                    class="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium"
                    :class="statusClasses(row.status)"
                  >
                    {{ row.status }}
                  </span>
                  <button
                    type="button"
                    class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-300 text-slate-600 transition hover:bg-slate-100"
                    :aria-label="`Edit ${activeTab === 'guides' ? 'guide' : 'customer'} ${row.name}`"
                    @click="openEditPopup(row)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      class="h-4 w-4"
                      aria-hidden="true"
                    >
                      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L9 17l-4 1 1-4L16.5 3.5Z" />
                      <path d="M14.5 5.5l4 4" />
                    </svg>
                  </button>
                </div>
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
              <p class="typo-muted">{{ paginationLabel }}</p>

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

    <div v-if="showEditPopup" class="fixed inset-0 z-50 bg-black/40" @click.self="closeEditPopup">
      <div class="absolute right-0 top-0 h-full w-full max-w-105 bg-[#1f1f1f] text-white shadow-2xl p-5 overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="typo-modal-eyebrow">Edit</div>
            <h3 class="typo-modal-title-dark">{{ editTargetLabel }}</h3>
          </div>
          <button class="text-gray-300 hover:text-white text-xl leading-none" aria-label="Close edit popup" @click="closeEditPopup">×</button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="text-gray-300 block mb-1">First Name</label>
            <input
              v-model="editForm.firstName"
              type="text"
              class="w-full rounded border border-[#ACBAC4] bg-[#2d2d2d] px-3 py-2 text-sm placeholder:text-gray-400"
              placeholder="Enter first name"
            />
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Last Name</label>
            <input
              v-model="editForm.lastName"
              type="text"
              class="w-full rounded border border-[#ACBAC4] bg-[#2d2d2d] px-3 py-2 text-sm placeholder:text-gray-400"
              placeholder="Enter last name"
            />
          </div>

          <div>
            <label class="text-gray-300 block mb-1">Email</label>
            <input
              v-model="editForm.email"
              type="email"
              class="w-full rounded border border-[#ACBAC4] bg-[#2d2d2d] px-3 py-2 text-sm placeholder:text-gray-400"
              placeholder="Enter email"
            />
          </div>

          <template v-if="editForm.tab === 'guides'">
            <div>
              <label class="text-gray-300 block mb-1">Languages</label>
              <div class="max-h-28 overflow-y-auto rounded border border-[#ACBAC4] bg-[#2d2d2d] p-2 space-y-1">
                <label
                  v-for="language in languageOptions"
                  :key="`lang-${language.id}`"
                  class="flex items-center gap-2 text-xs text-gray-200"
                >
                  <input
                    v-model="editForm.selectedLanguageCodes"
                    type="checkbox"
                    :value="language.code"
                  />
                  <span>{{ language.label }}</span>
                </label>
                <p v-if="!languageOptions.length" class="text-xs text-gray-400">No language options available.</p>
              </div>
            </div>

            <div>
              <label class="text-gray-300 block mb-1">Tour Expertise</label>
              <div class="max-h-28 overflow-y-auto rounded border border-[#ACBAC4] bg-[#2d2d2d] p-2 space-y-1">
                <label
                  v-for="tour in tourOptions"
                  :key="`tour-${tour.id}`"
                  class="flex items-center gap-2 text-xs text-gray-200"
                >
                  <input
                    v-model="editForm.selectedTourIds"
                    type="checkbox"
                    :value="tour.id"
                  />
                  <span>{{ tour.label }}</span>
                </label>
                <p v-if="!tourOptions.length" class="text-xs text-gray-400">No tour options available.</p>
              </div>
            </div>

            <div>
              <label class="text-gray-300 block mb-1">Availability Timezone</label>
              <input
                v-model="editForm.guideTimezone"
                type="text"
                class="w-full rounded border border-[#ACBAC4] bg-[#2d2d2d] px-3 py-2 text-sm placeholder:text-gray-400"
                placeholder="UTC"
              />
            </div>

            <div>
              <label class="text-gray-300 block mb-1">Daily Availability</label>
              <div class="rounded border border-[#ACBAC4] bg-[#2d2d2d] p-2 space-y-2">
                <div
                  v-for="day in WEEK_DAYS"
                  :key="day"
                  class="grid grid-cols-[auto_1fr_1fr] items-center gap-2 text-xs text-gray-200"
                >
                  <label class="flex items-center gap-2">
                    <input v-model="editForm.dailyAvailability[day].enabled" type="checkbox" />
                    <span class="w-20">{{ day.slice(0, 3) }}</span>
                  </label>
                  <input
                    v-model="editForm.dailyAvailability[day].start"
                    type="time"
                    step="1"
                    :disabled="!editForm.dailyAvailability[day].enabled"
                    class="rounded border border-[#ACBAC4] bg-[#303030] px-2 py-1 disabled:opacity-50"
                  />
                  <input
                    v-model="editForm.dailyAvailability[day].end"
                    type="time"
                    step="1"
                    :disabled="!editForm.dailyAvailability[day].enabled"
                    class="rounded border border-[#ACBAC4] bg-[#303030] px-2 py-1 disabled:opacity-50"
                  />
                </div>
              </div>
            </div>
          </template>

          <p v-if="editError" class="text-xs text-red-300">{{ editError }}</p>
          <p class="text-xs text-gray-400">Changes are saved through backend API and then reloaded in this table.</p>

          <div class="pt-2 flex items-center justify-end gap-2">
            <CancelButton :disabled="isSavingEdit" @cancel="closeEditPopup" />
            <SaveButton :disabled="!canSaveEdit || isSavingEdit" :loading="isSavingEdit" @save="requestEditConfirmation" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="showGuideDetailsPopup" class="fixed inset-0 z-50 bg-black/40" @click.self="closeGuideDetails">
      <div class="absolute right-0 top-0 h-full w-full max-w-105 bg-[#1f1f1f] text-white shadow-2xl p-5 overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="typo-modal-eyebrow">Guide Details</div>
            <h3 class="typo-modal-title-dark">{{ selectedGuideDetails?.name }}</h3>
            <p class="text-sm text-gray-400">ID: {{ selectedGuideDetails?.id }}</p>
          </div>
          <button class="text-gray-300 hover:text-white text-xl leading-none" aria-label="Close guide details" @click="closeGuideDetails">×</button>
        </div>

        <div class="space-y-4 text-sm">
          <div class="rounded border border-[#ACBAC4] bg-[#2d2d2d] p-3">
            <p class="font-medium text-gray-300">Email</p>
            <p>{{ selectedGuideDetails?.email || '-' }}</p>
          </div>

          <div class="rounded border border-[#ACBAC4] bg-[#2d2d2d] p-3">
            <p class="font-medium text-gray-300">Languages</p>
            <ul class="list-disc pl-5">
              <li v-for="label in selectedGuideLanguageLabels" :key="label">{{ label }}</li>
              <li v-if="!selectedGuideLanguageLabels.length" class="list-none text-gray-400">No languages configured.</li>
            </ul>
          </div>

          <div class="rounded border border-[#ACBAC4] bg-[#2d2d2d] p-3">
            <p class="font-medium text-gray-300">Tour Expertise</p>
            <ul class="list-disc pl-5">
              <li v-for="label in selectedGuideTourLabels" :key="label">{{ label }}</li>
              <li v-if="!selectedGuideTourLabels.length" class="list-none text-gray-400">No expertise configured.</li>
            </ul>
          </div>

          <div class="rounded border border-[#ACBAC4] bg-[#2d2d2d] p-3">
            <p class="font-medium text-gray-300">Weekly Working Schedule</p>
            <p class="text-xs text-gray-400 mb-1">
              Timezone: {{ selectedGuideDetails?.availabilityPatterns?.[0]?.timezone || 'UTC' }}
            </p>
            <ul class="divide-y divide-[#ACBAC4] border border-[#ACBAC4] rounded">
              <li v-for="day in selectedGuideWeeklySchedule" :key="day.day" class="flex items-center justify-between px-3 py-2">
                <span class="font-medium">{{ day.day }}</span>
                <span>{{ day.text }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <ConfirmDialog
      :open="showConfirmSavePopup"
      title="Confirm save"
      :message="confirmMessage"
      confirm-label="Save"
      :loading="isSavingEdit"
      :disabled="isSavingEdit"
      @cancel="showConfirmSavePopup = false"
      @confirm="applyRowEdit"
    />
  </div>
</template>
