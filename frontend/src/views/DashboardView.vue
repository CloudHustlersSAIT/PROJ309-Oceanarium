<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import AppSidebar from '../components/AppSidebar.vue'
import {
  getBookings,
  getGuides,
  getSchedules,
  getStats,
  getTours,
} from '../services/api'

const rangeOptions = [
  { value: 'all-time', label: 'All Time' },
  { value: 'this-month', label: 'This Month' },
  { value: 'this-week', label: 'This Week' },
  { value: 'this-day', label: 'This Day' },
]

const selectedRange = ref('this-month')
const selectedDate = ref(new Date().toISOString().slice(0, 10))
const isLoading = ref(false)
const apiError = ref('')
const apiWarnings = ref([])
const showAlertCenter = ref(false)
const showAlertDetail = ref(false)
const selectedAlertDetail = ref(null)
const alertReadState = ref({})

const statsSnapshot = ref(null)
const reservations = ref([])
const schedules = ref([])
const guides = ref([])
const tours = ref([])

const DASHBOARD_ALERT_READ_STATE_KEY = 'dashboard-alert-read-state-v1'
const ALERT_THRESHOLDS = {
  criticalCancellationRate: 12,
  warningCancellationRate: 7,
  lowOccupancyRate: 55,
  guideCoverageTarget: 85,
}

const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const activeRangeLabel = computed(
  () => rangeOptions.find((option) => option.value === selectedRange.value)?.label || 'All Time',
)

const selectedDateObject = computed(() => {
  const parsed = parseDate(selectedDate.value)
  return parsed || new Date()
})

const rangeBoundary = computed(() => {
  const anchor = selectedDateObject.value
  const start = new Date(anchor)
  start.setHours(0, 0, 0, 0)
  const end = new Date(anchor)
  end.setHours(23, 59, 59, 999)

  if (selectedRange.value === 'this-day') {
    return { start, end }
  }

  if (selectedRange.value === 'this-week') {
    const mondayIndex = (start.getDay() + 6) % 7
    start.setDate(start.getDate() - mondayIndex)
    end.setTime(start.getTime())
    end.setDate(start.getDate() + 6)
    end.setHours(23, 59, 59, 999)
    return { start, end }
  }

  if (selectedRange.value === 'this-month') {
    start.setDate(1)
    end.setMonth(start.getMonth() + 1, 0)
    end.setHours(23, 59, 59, 999)
    return { start, end }
  }

  return { start: null, end: null }
})

const previousRangeBoundary = computed(() => {
  const { start, end } = rangeBoundary.value
  if (!start || !end) return { start: null, end: null }

  const windowMs = end.getTime() - start.getTime() + 1
  const prevEnd = new Date(start.getTime() - 1)
  const prevStart = new Date(prevEnd.getTime() - windowMs + 1)
  return { start: prevStart, end: prevEnd }
})

function parseDate(value) {
  if (!value) return null

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }

  const normalizedValue = String(value).trim()
  const dateOnlyMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(normalizedValue)
  if (dateOnlyMatch) {
    const year = Number(dateOnlyMatch[1])
    const monthIndex = Number(dateOnlyMatch[2]) - 1
    const day = Number(dateOnlyMatch[3])
    const parsedDateOnly = new Date(year, monthIndex, day)
    return Number.isNaN(parsedDateOnly.getTime()) ? null : parsedDateOnly
  }

  const parsed = new Date(normalizedValue)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function normalizeReservationStatus(status) {
  return String(status || '').trim().toUpperCase()
}

function isCancelledReservation(status) {
  return normalizeReservationStatus(status) === 'CANCELLED'
}

function isWithinRange(value, boundary) {
  const parsed = parseDate(value)
  if (!parsed) return false
  const { start, end } = boundary
  if (start && parsed < start) return false
  if (end && parsed > end) return false
  return true
}

function compareDelta(current, previous) {
  if (previous <= 0) {
    if (current <= 0) return 'No change from previous window'
    return 'New volume in selected window'
  }

  const delta = ((current - previous) / previous) * 100
  const direction = delta >= 0 ? '+' : ''
  return `${direction}${delta.toFixed(1)}% vs previous window`
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-US')
}

function formatPercentage(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function loadAlertReadState() {
  if (typeof window === 'undefined') return {}

  try {
    const raw = window.localStorage.getItem(DASHBOARD_ALERT_READ_STATE_KEY)
    const parsed = raw ? JSON.parse(raw) : {}
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function persistAlertReadState(state) {
  if (typeof window === 'undefined') return

  try {
    window.localStorage.setItem(DASHBOARD_ALERT_READ_STATE_KEY, JSON.stringify(state || {}))
  } catch {
    // Keep dashboard functional even if storage is unavailable.
  }
}

const filteredReservations = computed(() =>
  reservations.value.filter((item) => isWithinRange(item?.event_start_datetime, rangeBoundary.value)),
)

const filteredSchedules = computed(() =>
  schedules.value.filter((item) => isWithinRange(item?.event_start_datetime, rangeBoundary.value)),
)

const previousReservations = computed(() =>
  reservations.value.filter((item) => isWithinRange(item?.event_start_datetime, previousRangeBoundary.value)),
)

const previousSchedules = computed(() =>
  schedules.value.filter((item) => isWithinRange(item?.event_start_datetime, previousRangeBoundary.value)),
)

const guideRatings = computed(() => {
  const values = guides.value
    .map((guide) => Number(guide?.guide_rating))
    .filter((rating) => Number.isFinite(rating) && rating > 0)

  if (values.length === 0) {
    const fallback = Number(statsSnapshot.value?.avgRating)
    return Number.isFinite(fallback) ? fallback : 0
  }

  const total = values.reduce((acc, value) => acc + value, 0)
  return total / values.length
})

const occupancyRate = computed(() => {
  if (filteredSchedules.value.length === 0) return 0

  const schedulesWithDemand = filteredSchedules.value.filter(
    (item) => Number(item?.reservation_count || 0) > 0,
  ).length

  return (schedulesWithDemand / filteredSchedules.value.length) * 100
})

const visitorsServed = computed(() =>
  filteredReservations.value
    .filter((item) => !isCancelledReservation(item?.status))
    .reduce((acc, item) => acc + Number(item?.current_ticket_num || 0), 0),
)

const currentWindowBookings = computed(
  () =>
    filteredReservations.value.filter((item) => !isCancelledReservation(item?.status))
      .length,
)

const currentWindowCancellations = computed(
  () =>
    filteredReservations.value.filter((item) => isCancelledReservation(item?.status))
      .length,
)

const currentWindowCancellationRate = computed(() => {
  const total = currentWindowBookings.value + currentWindowCancellations.value
  if (total === 0) return 0
  return (currentWindowCancellations.value / total) * 100
})

const guideCoverageRate = computed(() => {
  if (filteredSchedules.value.length === 0) return 100

  const assigned = filteredSchedules.value.filter(
    (item) => String(item?.guide_name || '').trim().length > 0,
  ).length

  return (assigned / filteredSchedules.value.length) * 100
})

const lowDemandTours = computed(() => {
  const byTour = new Map()

  for (const schedule of filteredSchedules.value) {
    const tourName = String(schedule?.tour_name || `Tour #${schedule?.tour_id || 'N/A'}`)
    const reservationCount = Number(schedule?.reservation_count || 0)
    if (!byTour.has(tourName)) {
      byTour.set(tourName, { totalSchedules: 0, zeroDemandSchedules: 0 })
    }

    const current = byTour.get(tourName)
    current.totalSchedules += 1
    if (reservationCount === 0) current.zeroDemandSchedules += 1
  }

  return Array.from(byTour.entries())
    .filter(([, value]) => value.totalSchedules >= 2 && value.zeroDemandSchedules / value.totalSchedules >= 0.5)
    .map(([tourName]) => tourName)
})

const operationalAlerts = computed(() => {
  const alerts = []

  if (currentWindowCancellationRate.value >= ALERT_THRESHOLDS.criticalCancellationRate) {
    alerts.push({
      severity: 'critical',
      title: 'High cancellation pressure',
      detail: `${currentWindowCancellationRate.value.toFixed(1)}% cancellations in ${activeRangeLabel.value.toLowerCase()}.`,
    })
  }

  if (occupancyRate.value < ALERT_THRESHOLDS.lowOccupancyRate && filteredSchedules.value.length > 0) {
    alerts.push({
      severity: 'warning',
      title: 'Low occupancy detected',
      detail: `${occupancyRate.value.toFixed(1)}% of schedules have bookings in the selected window.`,
    })
  }

  if (guideCoverageRate.value < ALERT_THRESHOLDS.guideCoverageTarget && filteredSchedules.value.length > 0) {
    alerts.push({
      severity: 'warning',
      title: 'Guide coverage below target',
      detail: `${guideCoverageRate.value.toFixed(1)}% schedules have an assigned guide.`,
    })
  }

  if (lowDemandTours.value.length > 0) {
    alerts.push({
      severity: 'watch',
      title: 'Tours with repeated low demand',
      detail: lowDemandTours.value.slice(0, 2).join(', '),
    })
  }

  if (alerts.length === 0) {
    alerts.push({
      severity: 'healthy',
      title: 'Operational baseline is stable',
      detail: `No critical risk found for ${activeRangeLabel.value.toLowerCase()}.`,
    })
  }

  return alerts.slice(0, 3)
})

const visibleOperationalAlerts = computed(() =>
  operationalAlerts.value.filter((alert) => alert.severity === 'critical' || alert.severity === 'healthy'),
)

const alertCenterAlerts = computed(() =>
  operationalAlerts.value
    .filter((alert) => alert.severity === 'warning' || alert.severity === 'watch')
    .map((alert, index) => ({
      ...alert,
      id: `${alert.severity}-${index}-${alert.title}`,
      recommendation:
        alert.severity === 'warning'
          ? 'Review schedules and staffing distribution for the selected range.'
          : 'Review tour demand and update planning thresholds if needed.',
    })),
)

const unreadAlertCount = computed(
  () => alertCenterAlerts.value.filter((alert) => !alertReadState.value[alert.id]).length,
)

const previousVisitorsServed = computed(() =>
  previousReservations.value
    .filter((item) => !isCancelledReservation(item?.status))
    .reduce((acc, item) => acc + Number(item?.current_ticket_num || 0), 0),
)

const kpiCards = computed(() => [
  {
    label: 'Total Tours Conducted',
    value: formatNumber(filteredSchedules.value.length),
    trend: compareDelta(filteredSchedules.value.length, previousSchedules.value.length),
  },
  {
    label: 'Total Visitors Served',
    value: formatNumber(visitorsServed.value),
    trend: compareDelta(visitorsServed.value, previousVisitorsServed.value),
  },
  {
    label: 'Avg Occupancy Rate',
    value: formatPercentage(occupancyRate.value),
    trend: 'Share of schedules with at least one reservation',
  },
  {
    label: 'Avg Guide Rating',
    value: guideRatings.value > 0 ? guideRatings.value.toFixed(1) : 'N/A',
    trend: 'Based on available guide ratings',
  },
])

const toursPerYear = computed(() => {
  const counters = new Map()
  for (const schedule of schedules.value) {
    const parsed = parseDate(schedule?.event_start_datetime)
    if (!parsed) continue
    const year = String(parsed.getFullYear())
    counters.set(year, (counters.get(year) || 0) + 1)
  }

  return Array.from(counters.entries())
    .sort((left, right) => Number(left[0]) - Number(right[0]))
    .map(([label, value]) => ({ label, value }))
})

const visitorsPerTour = computed(() => {
  const tourLookup = new Map(
    tours.value.map((tour) => [String(tour?.id), String(tour?.name || `Tour #${tour?.id}`)]),
  )
  const counters = new Map()

  for (const reservation of filteredReservations.value) {
    if (isCancelledReservation(reservation?.status)) continue
    const key = String(reservation?.tour_id || '')
    if (!key) continue
    counters.set(key, (counters.get(key) || 0) + Number(reservation?.current_ticket_num || 0))
  }

  return Array.from(counters.entries())
    .map(([tourId, value]) => ({
      label: tourLookup.get(tourId) || `Tour #${tourId}`,
      value,
    }))
    .sort((left, right) => right.value - left.value)
    .slice(0, 6)
})

const bookingsVsCancellations = computed(() => {
  const year = selectedDateObject.value.getFullYear()
  const byMonth = Array.from({ length: 12 }, (_, monthIndex) => ({
    month: monthLabels[monthIndex],
    bookings: 0,
    cancellations: 0,
  }))

  for (const reservation of reservations.value) {
    const parsed = parseDate(reservation?.event_start_datetime)
    if (!parsed || parsed.getFullYear() !== year) continue

    const monthIndex = parsed.getMonth()
    if (isCancelledReservation(reservation?.status)) {
      byMonth[monthIndex].cancellations += 1
    } else {
      byMonth[monthIndex].bookings += 1
    }
  }

  return byMonth
})

const bookingsCancellationRows = computed(() =>
  bookingsVsCancellations.value.map((row) => {
    const total = Number(row.bookings || 0) + Number(row.cancellations || 0)
    const rate = total > 0 ? (Number(row.cancellations || 0) / total) * 100 : 0

    return {
      ...row,
      cancellationRate: rate,
    }
  }),
)

const highestCancellationMonth = computed(() => {
  if (bookingsCancellationRows.value.length === 0) return null

  return bookingsCancellationRows.value.reduce((highest, current) =>
    current.cancellationRate > highest.cancellationRate ? current : highest,
  )
})

const lineChartData = computed(() => {
  const rows = bookingsCancellationRows.value
  const viewW = 700
  const viewH = 220
  const padLeft = 44
  const padRight = 16
  const padTop = 16
  const padBottom = 32
  const chartW = viewW - padLeft - padRight
  const chartH = viewH - padTop - padBottom

  const maxVal = Math.max(
    1,
    ...rows.map((r) => Math.max(Number(r.bookings || 0), Number(r.cancellations || 0))),
  )

  const xOf = (i) => padLeft + (rows.length > 1 ? (i / (rows.length - 1)) * chartW : chartW / 2)
  const yOf = (v) => padTop + chartH - (Number(v || 0) / maxVal) * chartH

  const bookingsPoints = rows.map((r, i) => ({ x: xOf(i), y: yOf(r.bookings), v: r.bookings, month: r.month }))
  const cancellationsPoints = rows.map((r, i) => ({ x: xOf(i), y: yOf(r.cancellations), v: r.cancellations, month: r.month }))

  const toPath = (pts) =>
    pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')

  const ySteps = 4
  const gridLines = Array.from({ length: ySteps + 1 }, (_, i) => ({
    y: padTop + (i / ySteps) * chartH,
    label: Math.round((maxVal / ySteps) * (ySteps - i)),
  }))

  return {
    viewW,
    viewH,
    padLeft,
    padBottom,
    bookingsPoints,
    cancellationsPoints,
    bookingsPath: toPath(bookingsPoints),
    cancellationsPath: toPath(cancellationsPoints),
    gridLines,
    months: rows.map((r, i) => ({ label: r.month, x: xOf(i) })),
  }
})

const topGuides = computed(() => {
  const ratingLookup = new Map(
    guides.value.map((guide) => {
      const name = `${guide?.first_name || ''} ${guide?.last_name || ''}`.trim()
      return [name, Number(guide?.guide_rating)]
    }),
  )

  const counters = new Map()
  for (const schedule of filteredSchedules.value) {
    const guideName = String(schedule?.guide_name || '').trim()
    if (!guideName) continue
    counters.set(guideName, (counters.get(guideName) || 0) + 1)
  }

  return Array.from(counters.entries())
    .map(([name, toursCount]) => ({
      name,
      tours: toursCount,
      rating: Number.isFinite(ratingLookup.get(name)) ? ratingLookup.get(name).toFixed(1) : 'N/A',
    }))
    .sort((left, right) => right.tours - left.tours)
    .slice(0, 5)
})

const topRatedGuides = computed(() =>
  guides.value
    .map((guide) => ({
      name: `${guide?.first_name || ''} ${guide?.last_name || ''}`.trim() || 'Unknown',
      rating: Number(guide?.guide_rating),
      tours: guide?.tours_count ?? null,
    }))
    .filter((guide) => Number.isFinite(guide.rating) && guide.rating > 0)
    .sort((a, b) => b.rating - a.rating)
    .slice(0, 5),
)

const LANGUAGE_LABELS = {
  en: 'English',
  pt: 'Portuguese',
  es: 'Spanish',
  fr: 'French',
  zh: 'Chinese',
  de: 'German',
  it: 'Italian',
  ja: 'Japanese',
  ko: 'Korean',
  ar: 'Arabic',
  unknown: 'Unknown',
}

const LANGUAGE_GRADIENT_DARK = '#1e3a8a'
const LANGUAGE_GRADIENT_LIGHT = '#dbeafe'

function interpolateHexColor(fromHex, toHex, ratio) {
  const normalize = (hex) => String(hex || '').replace('#', '').trim()
  const from = normalize(fromHex)
  const to = normalize(toHex)
  if (!/^[0-9a-fA-F]{6}$/.test(from) || !/^[0-9a-fA-F]{6}$/.test(to)) {
    return LANGUAGE_GRADIENT_DARK
  }

  const t = Math.max(0, Math.min(1, Number(ratio || 0)))
  const channel = (hex, idx) => parseInt(hex.slice(idx, idx + 2), 16)
  const blend = (a, b) => Math.round(a + (b - a) * t)

  const r = blend(channel(from, 0), channel(to, 0))
  const g = blend(channel(from, 2), channel(to, 2))
  const b = blend(channel(from, 4), channel(to, 4))

  return `#${[r, g, b].map((value) => value.toString(16).padStart(2, '0')).join('')}`
}

const tourLanguageInfographic = computed(() => {
  const cx = 160
  const cy = 160
  const rOuter = 108
  const rInner = 64
  const innerPlaceholderRadius = 42
  const start = -Math.PI / 11

  const counters = new Map()
  for (const schedule of filteredSchedules.value) {
    const code = String(schedule?.language_code || '')
      .trim()
      .toLowerCase() || 'unknown'
    counters.set(code, (counters.get(code) || 0) + 1)
  }

  const sorted = Array.from(counters.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([code, count]) => ({
      code,
      label: LANGUAGE_LABELS[code] || code.toUpperCase(),
      count,
    }))

  const compact =
    sorted.length <= 5
      ? sorted
      : [
          ...sorted.slice(0, 4),
          {
            code: 'other',
            label: 'Other',
            count: sorted.slice(4).reduce((acc, item) => acc + item.count, 0),
          },
        ]

  const totalTours = compact.reduce((acc, item) => acc + item.count, 0)

  if (totalTours === 0) {
    return {
      viewBox: '0 0 320 320',
      cx,
      cy,
      innerPlaceholderRadius,
      totalTours: 0,
      segments: [],
    }
  }

  let cursor = start
  const segments = compact.map((item, index) => {
    const pct = (item.count / totalTours) * 100
    const sweep = (pct / 100) * Math.PI * 2
    const a0 = cursor
    const a1 = cursor + sweep
    cursor = a1
    const mid = a0 + sweep / 2

    const largeArcFlag = sweep > Math.PI ? 1 : 0

    const xo0 = cx + rOuter * Math.cos(a0)
    const yo0 = cy + rOuter * Math.sin(a0)
    const xo1 = cx + rOuter * Math.cos(a1)
    const yo1 = cy + rOuter * Math.sin(a1)

    const xi0 = cx + rInner * Math.cos(a0)
    const yi0 = cy + rInner * Math.sin(a0)
    const xi1 = cx + rInner * Math.cos(a1)
    const yi1 = cy + rInner * Math.sin(a1)

    const nodeX = cx + (rOuter + 4) * Math.cos(mid)
    const nodeY = cy + (rOuter + 4) * Math.sin(mid)

    const elbowX = cx + (rOuter + 24) * Math.cos(mid)
    const elbowY = cy + (rOuter + 24) * Math.sin(mid)

    const rightSide = Math.cos(mid) >= 0
    const lineEndX = elbowX + (rightSide ? 30 : -30)
    const lineEndY = elbowY

    const labelX = cx + 152 * Math.cos(mid)
    const labelY = cy + 152 * Math.sin(mid)

    const toneRatio = compact.length <= 1 ? 0 : index / (compact.length - 1)
    const fillColor = interpolateHexColor(LANGUAGE_GRADIENT_DARK, LANGUAGE_GRADIENT_LIGHT, toneRatio)

    return {
      id: `segment-${item.code}-${index + 1}`,
      color: fillColor,
      path: `M ${xo0.toFixed(2)} ${yo0.toFixed(2)} A ${rOuter} ${rOuter} 0 ${largeArcFlag} 1 ${xo1.toFixed(2)} ${yo1.toFixed(2)} L ${xi1.toFixed(2)} ${yi1.toFixed(2)} A ${rInner} ${rInner} 0 ${largeArcFlag} 0 ${xi0.toFixed(2)} ${yi0.toFixed(2)} Z`,
      nodeX,
      nodeY,
      elbowX,
      elbowY,
      lineEndX,
      lineEndY,
      rightSide,
      labelX,
      labelY,
      title: item.label,
      subtitle: `${pct.toFixed(1)}%`,
    }
  })

  return {
    viewBox: '0 0 320 320',
    cx,
    cy,
    innerPlaceholderRadius,
    totalTours,
    segments,
  }
})

const maxToursPerYear = computed(() =>
  Math.max(1, ...toursPerYear.value.map((item) => Number(item.value || 0))),
)
const maxVisitorsPerTour = computed(() =>
  Math.max(1, ...visitorsPerTour.value.map((item) => Number(item.value || 0))),
)
function percentage(value, max) {
  return `${Math.max(8, Math.round((Number(value || 0) / Math.max(1, max)) * 100))}%`
}

function alertClasses(severity) {
  if (severity === 'critical') return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-950/45 dark:text-rose-300'
  if (severity === 'warning') return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
  if (severity === 'watch') return 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-800 dark:bg-sky-950/45 dark:text-sky-300'
  return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/45 dark:text-emerald-300'
}

function toggleAlertCenter() {
  showAlertCenter.value = !showAlertCenter.value
}

function closeAlertCenter() {
  showAlertCenter.value = false
}

function markAllAlertsRead() {
  const next = { ...alertReadState.value }
  for (const alert of alertCenterAlerts.value) {
    next[alert.id] = true
  }
  alertReadState.value = next
}

function openAlertDetail(alert) {
  showAlertCenter.value = false
  selectedAlertDetail.value = alert
  showAlertDetail.value = true
  alertReadState.value = {
    ...alertReadState.value,
    [alert.id]: true,
  }
}

function closeAlertDetail() {
  showAlertDetail.value = false
  selectedAlertDetail.value = null
}

function handleGlobalKeydown(event) {
  if (event.key !== 'Escape') return

  if (showAlertDetail.value) {
    closeAlertDetail()
    return
  }

  if (showAlertCenter.value) {
    closeAlertCenter()
  }
}

async function loadDashboard() {
  isLoading.value = true
  apiError.value = ''
  apiWarnings.value = []

  const results = await Promise.allSettled([
    getStats(),
    getBookings(),
    getSchedules(),
    getGuides(),
    getTours(),
  ])

  const [statsResult, bookingsResult, schedulesResult, guidesResult, toursResult] = results

  if (statsResult.status === 'fulfilled') {
    statsSnapshot.value = statsResult.value
  } else {
    apiWarnings.value.push('Stats snapshot is currently unavailable.')
  }

  if (bookingsResult.status === 'fulfilled') {
    reservations.value = Array.isArray(bookingsResult.value) ? bookingsResult.value : []
  } else {
    apiWarnings.value.push('Reservations feed is unavailable.')
  }

  if (schedulesResult.status === 'fulfilled') {
    schedules.value = Array.isArray(schedulesResult.value) ? schedulesResult.value : []
  } else {
    apiWarnings.value.push('Schedules feed is unavailable.')
  }

  if (guidesResult.status === 'fulfilled') {
    guides.value = Array.isArray(guidesResult.value) ? guidesResult.value : []
  } else {
    apiWarnings.value.push('Guides feed is unavailable.')
  }

  if (toursResult.status === 'fulfilled') {
    tours.value = Array.isArray(toursResult.value) ? toursResult.value : []
  } else {
    apiWarnings.value.push('Tours feed is unavailable.')
  }

  if (results.every((result) => result.status === 'rejected')) {
    apiError.value = 'Unable to load dashboard data from API.'
  }

  isLoading.value = false
}

onMounted(() => {
  alertReadState.value = loadAlertReadState()
  window.addEventListener('keydown', handleGlobalKeydown)
  loadDashboard()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})

watch(alertReadState, (value) => {
  persistAlertReadState(value)
}, { deep: true })
</script>

<template>
  <div class="flex min-h-screen overflow-x-hidden bg-[#F8FAFC] dark:bg-[#0F1117]">
    <AppSidebar />

    <main class="flex-1 min-w-0 p-4 md:p-6 lg:p-8">
      <section class="app-page-wrap">
        <header class="app-surface-card app-section-padding relative">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 class="typo-page-title">Oceanarium Dashboard</h1>
              
            </div>

            <div class="flex items-end gap-3">
              <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <label class="flex flex-col gap-1">
                  <span class="typo-card-label">Date</span>
                  <input
                    v-model="selectedDate"
                    type="date"
                    class="typo-body rounded-xl border border-slate-300 bg-white px-3 py-2 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
                  />
                </label>

                <label class="flex flex-col gap-1">
                  <span class="typo-card-label">Range</span>
                  <select
                    v-model="selectedRange"
                    class="typo-body rounded-xl border border-slate-300 bg-white px-3 py-2 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-100"
                  >
                    <option v-for="option in rangeOptions" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </label>
              </div>

              <button
                type="button"
                class="relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-300 bg-white text-slate-700 transition hover:bg-slate-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300 dark:hover:bg-white/5"
                aria-label="Open alert center"
                aria-controls="dashboard-alert-center"
                :aria-expanded="showAlertCenter"
                @click="toggleAlertCenter"
              >
                <span aria-hidden="true">🔔</span>
                <span
                  v-if="unreadAlertCount > 0"
                  class="absolute -right-1 -top-1 inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-rose-600 px-1 text-[11px] font-semibold text-white"
                >
                  {{ unreadAlertCount }}
                </span>
              </button>
            </div>
          </div>

          <div v-if="showAlertCenter" class="fixed inset-0 z-10" @click="closeAlertCenter" />

          <div
            v-if="showAlertCenter"
            id="dashboard-alert-center"
            role="region"
            aria-label="Dashboard alert center"
            class="absolute right-6 top-22 z-20 w-full max-w-sm rounded-xl border border-slate-200 bg-white p-3 shadow-xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40"
          >
            <div class="flex items-center justify-between gap-3">
              <h3 class="typo-section-title text-base">Alert Center</h3>
              <button
                type="button"
                class="typo-caption text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                @click="closeAlertCenter"
              >
                Close
              </button>
            </div>

            <p class="mt-1 typo-caption">Warning and watch alerts are grouped here to reduce dashboard noise.</p>

            <div class="mt-3 space-y-2">
              <article
                v-for="alert in alertCenterAlerts"
                :key="alert.id"
                class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-[#1A2231]"
              >
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <p class="typo-card-label">{{ alert.severity }}</p>
                    <p class="typo-body font-semibold text-slate-800 dark:text-slate-100">{{ alert.title }}</p>
                    <p class="mt-1 typo-caption">{{ alert.detail }}</p>
                  </div>
                  <button
                    type="button"
                    class="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs font-medium text-slate-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300"
                    @click="openAlertDetail(alert)"
                  >
                    Details
                  </button>
                </div>
              </article>

              <p v-if="alertCenterAlerts.length === 0" class="typo-muted">No warning or watch alerts.</p>
            </div>

            <div class="mt-3 flex justify-end">
              <button
                type="button"
                class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300"
                @click="markAllAlertsRead"
              >
                Mark all as read
              </button>
            </div>
          </div>

          <p class="mt-3 typo-caption">
            Active filter: {{ activeRangeLabel }} · {{ selectedDate }}
          </p>
        </header>

        <p v-if="apiError" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 typo-body text-rose-700 dark:border-rose-800 dark:bg-rose-950/45 dark:text-rose-300">
          {{ apiError }}
        </p>

        <div v-if="apiWarnings.length > 0" class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-950/40">
          <p class="typo-card-label text-amber-700 dark:text-amber-300">Partial Data Notice</p>
          <ul class="mt-2 space-y-1">
            <li v-for="warning in apiWarnings" :key="warning" class="typo-body text-amber-700 dark:text-amber-300">
              {{ warning }}
            </li>
          </ul>
        </div>

        <section v-if="visibleOperationalAlerts.length > 0" class="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <article
            v-for="alert in visibleOperationalAlerts"
            :key="`${alert.severity}-${alert.title}`"
            class="rounded-xl border px-4 py-3"
            :class="alertClasses(alert.severity)"
          >
            <p class="typo-card-label">{{ alert.severity }}</p>
            <p class="mt-1 text-sm font-semibold">{{ alert.title }}</p>
            <p class="mt-1 typo-caption" :class="alert.severity === 'healthy' ? 'text-emerald-700' : ''">{{ alert.detail }}</p>
          </article>
        </section>

        <section class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <article
            v-for="card in kpiCards"
            :key="card.label"
            class="app-surface-card app-section-padding"
          >
            <p class="typo-card-label">{{ card.label }}</p>
            <p class="typo-card-value">{{ card.value }}</p>
            <p class="mt-1 typo-caption">{{ card.trend }}</p>
          </article>
        </section>

        <section class="grid grid-cols-1 gap-4 xl:grid-cols-[1.3fr_1fr]">
          <article class="app-surface-card app-section-padding">
            <h2 class="typo-section-title">Visitors Per Tour</h2>
            <p class="mt-1 typo-muted">Ticket volume by tour inside selected filter window.</p>

            <div class="mt-4 space-y-3">
              <div
                v-for="item in visitorsPerTour"
                :key="item.label"
                class="grid grid-cols-[minmax(0,170px)_1fr_70px] items-start gap-3"
              >
                <span class="typo-caption wrap-break-word leading-tight text-slate-700 dark:text-slate-300">{{ item.label }}</span>
                <div class="h-3 overflow-hidden rounded bg-slate-100 dark:bg-white/8">
                  <div class="h-full rounded bg-blue-600" :style="{ width: percentage(item.value, maxVisitorsPerTour) }" />
                </div>
                <span class="typo-caption text-right text-slate-700 dark:text-slate-300">{{ formatNumber(item.value) }}</span>
              </div>

              <p v-if="visitorsPerTour.length === 0" class="typo-muted">No reservation data available.</p>
            </div>
          </article>

          <article class="app-surface-card app-section-padding">
            <h2 class="typo-section-title">Total Tours Per Year</h2>
            <p class="mt-1 typo-muted">All schedules grouped by calendar year.</p>

            <div class="mt-4 space-y-3">
              <div
                v-for="item in toursPerYear"
                :key="item.label"
                class="grid grid-cols-[48px_1fr_70px] items-center gap-3"
              >
                <span class="typo-caption">{{ item.label }}</span>
                <div class="h-3 overflow-hidden rounded bg-slate-100 dark:bg-white/8">
                  <div class="h-full rounded bg-sky-500" :style="{ width: percentage(item.value, maxToursPerYear) }" />
                </div>
                <span class="typo-caption text-right text-slate-700 dark:text-slate-300">{{ formatNumber(item.value) }}</span>
              </div>

              <p v-if="toursPerYear.length === 0" class="typo-muted">No schedule data available.</p>
            </div>
          </article>
        </section>

        <article class="app-surface-card app-section-padding">
          <h2 class="typo-section-title">Bookings vs Cancellations</h2>
          <p class="mt-1 typo-muted">
            Annual view for {{ selectedDateObject.getFullYear() }}. Window summary uses
            {{ activeRangeLabel.toLowerCase() }}.
          </p>

          <div class="mt-3 grid grid-cols-3 gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-white/10 dark:bg-[#1A2231]">
            <p class="typo-caption">
              <span class="font-semibold text-slate-700 dark:text-slate-300">Bookings:</span>
              {{ currentWindowBookings }}
            </p>
            <p class="typo-caption">
              <span class="font-semibold text-slate-700 dark:text-slate-300">Cancellations:</span>
              {{ currentWindowCancellations }}
            </p>
            <p class="typo-caption">
              <span class="font-semibold text-slate-700 dark:text-slate-300">Cancellation Rate:</span>
              {{ currentWindowCancellationRate.toFixed(1) }}%
            </p>
          </div>

          <div class="mt-4 overflow-x-auto">
            <svg
              :viewBox="`0 0 ${lineChartData.viewW} ${lineChartData.viewH}`"
              class="w-full"
              :style="{ minWidth: '460px', height: '220px' }"
              overflow="visible"
              role="img"
              aria-label="Bookings vs Cancellations line chart"
            >
              <line
                v-for="grid in lineChartData.gridLines"
                :key="`grid-${grid.y}`"
                :x1="lineChartData.padLeft"
                :y1="grid.y"
                :x2="lineChartData.viewW - lineChartData.padRight"
                :y2="grid.y"
                stroke="#e2e8f0"
                stroke-width="1"
              />
              <text
                v-for="grid in lineChartData.gridLines"
                :key="`ylabel-${grid.y}`"
                :x="lineChartData.padLeft - 6"
                :y="grid.y + 4"
                text-anchor="end"
                fill="#94a3b8"
                style="font-size: 11px; font-family: inherit"
              >{{ grid.label }}</text>

              <text
                v-for="month in lineChartData.months"
                :key="`mlabel-${month.label}`"
                :x="month.x"
                :y="lineChartData.viewH - lineChartData.padBottom + 18"
                text-anchor="middle"
                fill="#94a3b8"
                style="font-size: 11px; font-family: inherit"
              >{{ month.label }}</text>

              <path
                :d="lineChartData.bookingsPath"
                fill="none"
                stroke="#0284c7"
                stroke-width="2.5"
                stroke-linejoin="round"
                stroke-linecap="round"
              />
              <path
                :d="lineChartData.cancellationsPath"
                fill="none"
                stroke="#f97316"
                stroke-width="2.5"
                stroke-linejoin="round"
                stroke-linecap="round"
              />

              <circle
                v-for="pt in lineChartData.bookingsPoints"
                :key="`bpt-${pt.x}`"
                :cx="pt.x"
                :cy="pt.y"
                r="4"
                fill="#0284c7"
                stroke="white"
                stroke-width="1.5"
              />
              <text
                v-for="pt in lineChartData.bookingsPoints"
                v-show="pt.v > 0"
                :key="`bval-${pt.x}`"
                :x="pt.x"
                :y="pt.y - 9"
                text-anchor="middle"
                fill="#0284c7"
                style="font-size: 10px; font-weight: 600; font-family: inherit"
              >{{ pt.v }}</text>

              <circle
                v-for="pt in lineChartData.cancellationsPoints"
                :key="`cpt-${pt.x}`"
                :cx="pt.x"
                :cy="pt.y"
                r="4"
                fill="#f97316"
                stroke="white"
                stroke-width="1.5"
              />
              <text
                v-for="pt in lineChartData.cancellationsPoints"
                v-show="pt.v > 0"
                :key="`cval-${pt.x}`"
                :x="pt.x"
                :y="pt.y - 9"
                text-anchor="middle"
                fill="#f97316"
                style="font-size: 10px; font-weight: 600; font-family: inherit"
              >{{ pt.v }}</text>
            </svg>
          </div>

          <div class="mt-3 flex flex-wrap items-center justify-between gap-3">
            <p class="typo-caption">
              Highest cancellation month:
              <span class="font-semibold text-slate-700 dark:text-slate-300">
                {{ highestCancellationMonth ? `${highestCancellationMonth.month} (${highestCancellationMonth.cancellationRate.toFixed(1)}%)` : 'N/A' }}
              </span>
            </p>
            <div class="flex flex-wrap gap-6 typo-caption">
              <div class="flex items-center gap-2">
                <span class="h-2.5 w-4 rounded bg-sky-600" /> Bookings
              </div>
              <div class="flex items-center gap-2">
                <span class="h-2.5 w-4 rounded bg-orange-500" /> Cancellations
              </div>
            </div>
          </div>
        </article>

        <section class="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <article class="app-surface-card p-4">
            <h2 class="typo-section-title">Top Guides by Tours</h2>
            <p class="mt-0.5 typo-muted">Assigned tours in selected window.</p>

            <ul class="mt-3 divide-y divide-slate-100 dark:divide-white/8">
              <li
                v-for="guide in topGuides"
                :key="guide.name"
                class="grid grid-cols-[1fr_auto_auto] items-center gap-2 py-1.5"
              >
                <span class="typo-body text-slate-700 truncate dark:text-slate-300">{{ guide.name }}</span>
                <span class="typo-caption text-slate-500">{{ guide.tours }}t</span>
                <span class="typo-caption font-medium text-amber-600">{{ guide.rating }} ★</span>
              </li>
            </ul>

            <p v-if="topGuides.length === 0" class="mt-3 typo-muted">No data available.</p>
          </article>

          <article class="app-surface-card p-4">
            <h2 class="typo-section-title">Top Rated Guides</h2>
            <p class="mt-0.5 typo-muted">Ranked by overall rating score.</p>

            <ul class="mt-3 divide-y divide-slate-100 dark:divide-white/8">
              <li
                v-for="(guide, index) in topRatedGuides"
                :key="guide.name"
                class="grid grid-cols-[20px_1fr_auto] items-center gap-2 py-1.5"
              >
                <span class="typo-caption font-semibold text-slate-400">#{{ index + 1 }}</span>
                <span class="typo-body text-slate-700 truncate dark:text-slate-300">{{ guide.name }}</span>
                <span class="typo-caption font-semibold text-amber-600">{{ guide.rating.toFixed(1) }} ★</span>
              </li>
            </ul>

            <p v-if="topRatedGuides.length === 0" class="mt-3 typo-muted">No data available.</p>
          </article>

          <article class="app-surface-card p-4">
            <h2 class="typo-section-title">Tour Volume by Language</h2>

            <div v-if="tourLanguageInfographic.segments.length > 0" class="relative mx-auto mt-6 w-full max-w-105">
              <svg
                :viewBox="tourLanguageInfographic.viewBox"
                class="h-auto w-full"
                role="img"
                aria-label="Tour volume by language infographic"
              >
                <defs>
                  <filter id="softDropShadow" x="-30%" y="-30%" width="160%" height="160%">
                    <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0f172a" flood-opacity="0.12" />
                  </filter>
                </defs>

                <path
                  v-for="segment in tourLanguageInfographic.segments"
                  :key="segment.id"
                  :d="segment.path"
                  :fill="segment.color"
                  stroke="#f8fafc"
                  stroke-width="1.5"
                  filter="url(#softDropShadow)"
                />

                <circle
                  :cx="tourLanguageInfographic.cx"
                  :cy="tourLanguageInfographic.cy"
                  :r="tourLanguageInfographic.innerPlaceholderRadius"
                  fill="#f8fafc"
                  stroke="#d7d7d2"
                  stroke-width="1.5"
                />
                <text
                  :x="tourLanguageInfographic.cx"
                  :y="tourLanguageInfographic.cy + 2"
                  text-anchor="middle"
                  fill="#475569"
                  style="font-size: 11px; font-weight: 700; font-family: inherit"
                >{{ tourLanguageInfographic.totalTours }} tours</text>

                <line
                  v-for="segment in tourLanguageInfographic.segments"
                  :key="`line-a-${segment.id}`"
                  :x1="segment.nodeX"
                  :y1="segment.nodeY"
                  :x2="segment.elbowX"
                  :y2="segment.elbowY"
                  stroke="#94a3b8"
                  stroke-width="1"
                />
                <line
                  v-for="segment in tourLanguageInfographic.segments"
                  :key="`line-b-${segment.id}`"
                  :x1="segment.elbowX"
                  :y1="segment.elbowY"
                  :x2="segment.lineEndX"
                  :y2="segment.lineEndY"
                  stroke="#94a3b8"
                  stroke-width="1"
                />
                <circle
                  v-for="segment in tourLanguageInfographic.segments"
                  :key="`node-${segment.id}`"
                  :cx="segment.nodeX"
                  :cy="segment.nodeY"
                  r="4"
                  fill="#f8fafc"
                  stroke="#94a3b8"
                  stroke-width="1"
                />
              </svg>

              <div
                v-for="segment in tourLanguageInfographic.segments"
                :key="`label-${segment.id}`"
                class="absolute w-22 rounded-lg border border-slate-200 bg-white/95 px-2 py-1.5 shadow-sm dark:border-white/10 dark:bg-[#161B27]/95"
                :style="{
                  left: `${(segment.labelX / 320) * 100}%`,
                  top: `${(segment.labelY / 320) * 100}%`,
                  transform: 'translate(-50%, -50%)',
                  textAlign: segment.rightSide ? 'left' : 'right',
                }"
              >
                <p class="typo-caption font-semibold leading-tight text-slate-700 dark:text-slate-200">{{ segment.title }}</p>
                <p class="typo-caption mt-0.5 leading-tight text-slate-400">{{ segment.subtitle }}</p>
              </div>
            </div>

            <p v-else class="mt-3 typo-muted">No language-coded schedule data for the selected window.</p>
          </article>

        </section>

        <p v-if="isLoading" class="typo-muted px-1">Loading dashboard data...</p>
      </section>
    </main>

    <div v-if="showAlertDetail && selectedAlertDetail" class="fixed inset-0 z-40 bg-black/40" @click.self="closeAlertDetail">
      <div class="absolute inset-x-0 top-20 mx-auto w-full max-w-lg rounded-xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/40">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="typo-card-label">{{ selectedAlertDetail.severity }}</p>
            <h3 class="typo-section-title text-lg">{{ selectedAlertDetail.title }}</h3>
          </div>
          <button
            type="button"
            class="rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm text-slate-600 dark:border-white/15 dark:bg-[#1C2333] dark:text-slate-300"
            aria-label="Close alert details"
            @click="closeAlertDetail"
          >
            Close
          </button>
        </div>

        <p class="mt-3 typo-body text-slate-700 dark:text-slate-300">{{ selectedAlertDetail.detail }}</p>

        <div class="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-white/10 dark:bg-[#1A2231]">
          <p class="typo-card-label">Recommended Action</p>
          <p class="mt-1 typo-body text-slate-700 dark:text-slate-300">{{ selectedAlertDetail.recommendation }}</p>
        </div>

        <p class="mt-4 typo-caption">Generated from current dashboard metrics and selected filter window.</p>
      </div>
    </div>
  </div>
</template>
