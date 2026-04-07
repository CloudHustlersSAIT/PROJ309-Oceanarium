<script setup>
import { computed, onUnmounted, ref } from 'vue'

import { postInsightQuery } from '../services/api'

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const voiceState = ref('idle') // 'idle' | 'listening' | 'processing' | 'result'
const question = ref('')
const result = ref(null)
const apiError = ref('')
const showContentSafetyModal = ref(false)
const showSql = ref(false)

const speechSupported =
  typeof window !== 'undefined' &&
  ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)

// ---------------------------------------------------------------------------
// Web Speech API
// ---------------------------------------------------------------------------
let recognition = null

if (speechSupported) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.continuous = true
  recognition.interimResults = true
  recognition.lang = 'en-US'

  recognition.onresult = (event) => {
    let transcript = ''
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript
    }
    question.value = transcript
  }

  recognition.onend = () => {
    if (voiceState.value === 'listening') {
      submitQuestion()
    }
  }

  recognition.onerror = (event) => {
    if (event.error !== 'no-speech') {
      voiceState.value = 'idle'
    }
  }
}

onUnmounted(() => {
  recognition?.stop()
})

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------
function toggleMic() {
  if (voiceState.value === 'idle' || voiceState.value === 'result') {
    question.value = ''
    result.value = null
    apiError.value = ''
    showSql.value = false
    voiceState.value = 'listening'
    recognition?.start()
  } else if (voiceState.value === 'listening') {
    recognition?.stop()
    submitQuestion()
  }
}

async function submitQuestion() {
  const q = question.value.trim()
  if (!q) {
    voiceState.value = 'idle'
    return
  }

  voiceState.value = 'processing'
  result.value = null
  apiError.value = ''
  showSql.value = false

  try {
    const data = await postInsightQuery(q)
    result.value = data
    voiceState.value = 'result'
  } catch (err) {
    const code = err?.response?.data?.detail?.code ?? err?.detail?.code
    if (
      code === 'CONTENT_SAFETY_BLOCKED' ||
      (err?.status === 400 && JSON.stringify(err).includes('CONTENT_SAFETY_BLOCKED'))
    ) {
      showContentSafetyModal.value = true
    } else {
      apiError.value =
        err?.response?.data?.detail?.message ??
        err?.message ??
        'Something went wrong. Please try again.'
    }
    voiceState.value = 'idle'
  }
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey && voiceState.value === 'idle') {
    event.preventDefault()
    submitQuestion()
  }
}

function dismissContentSafetyModal() {
  showContentSafetyModal.value = false
  question.value = ''
  voiceState.value = 'idle'
}

// ---------------------------------------------------------------------------
// Chart computations
// ---------------------------------------------------------------------------
const barChartData = computed(() => {
  const chart = result.value?.chart
  if (!chart || chart.type !== 'bar' || !chart.data?.length) return null

  const maxValue = Math.max(...chart.data.map((d) => d.value), 1)
  return {
    items: chart.data.map((d) => ({
      ...d,
      pct: `${Math.round((d.value / maxValue) * 100)}%`,
    })),
    maxValue,
  }
})

const lineChartData = computed(() => {
  const chart = result.value?.chart
  if (!chart || chart.type !== 'line' || !chart.data?.length) return null

  const W = 560
  const H = 160
  const padL = 40
  const padR = 16
  const padT = 12
  const padB = 28
  const chartW = W - padL - padR
  const chartH = H - padT - padB
  const maxVal = Math.max(...chart.data.map((d) => d.value), 1)
  const xOf = (i) => padL + (i / (chart.data.length - 1 || 1)) * chartW
  const yOf = (v) => padT + chartH - (v / maxVal) * chartH

  const points = chart.data.map((d, i) => ({
    x: xOf(i),
    y: yOf(d.value),
    v: d.value,
    label: d.label,
  }))
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

  const gridSteps = 4
  const gridLines = Array.from({ length: gridSteps + 1 }, (_, i) => ({
    y: padT + (i / gridSteps) * chartH,
    label: Math.round(maxVal - (i / gridSteps) * maxVal),
  }))

  return { W, H, padL, padB, points, pathD, gridLines }
})

const donutData = computed(() => {
  const chart = result.value?.chart
  if (!chart || chart.type !== 'donut' || !chart.data?.length) return null

  const total = chart.data.reduce((s, d) => s + d.value, 0) || 1
  const cx = 80
  const cy = 80
  const r = 60
  const innerR = 36
  const colors = ['#0284c7', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2']

  let cumAngle = -Math.PI / 2
  const segments = chart.data.map((d, i) => {
    const angle = (d.value / total) * 2 * Math.PI
    const startAngle = cumAngle
    const endAngle = cumAngle + angle
    cumAngle = endAngle

    const x1 = cx + r * Math.cos(startAngle)
    const y1 = cy + r * Math.sin(startAngle)
    const x2 = cx + r * Math.cos(endAngle)
    const y2 = cy + r * Math.sin(endAngle)
    const ix1 = cx + innerR * Math.cos(endAngle)
    const iy1 = cy + innerR * Math.sin(endAngle)
    const ix2 = cx + innerR * Math.cos(startAngle)
    const iy2 = cy + innerR * Math.sin(startAngle)
    const largeArc = angle > Math.PI ? 1 : 0

    const midAngle = startAngle + angle / 2
    const labelR = r + 18
    const labelX = cx + labelR * Math.cos(midAngle)
    const labelY = cy + labelR * Math.sin(midAngle)

    return {
      d: `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} L ${ix1} ${iy1} A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix2} ${iy2} Z`,
      color: colors[i % colors.length],
      label: d.label,
      value: d.value,
      pct: Math.round((d.value / total) * 100),
      labelX,
      labelY,
    }
  })

  return { segments, cx, cy, total }
})

// ---------------------------------------------------------------------------
// Badge + color helpers
// ---------------------------------------------------------------------------
const ACTION_BADGE = {
  train: {
    bg: 'bg-blue-100 dark:bg-blue-900/40',
    text: 'text-blue-700 dark:text-blue-300',
    label: 'Train',
  },
  hire: {
    bg: 'bg-violet-100 dark:bg-violet-900/40',
    text: 'text-violet-700 dark:text-violet-300',
    label: 'Hire',
  },
  assign: {
    bg: 'bg-emerald-100 dark:bg-emerald-900/40',
    text: 'text-emerald-700 dark:text-emerald-300',
    label: 'Assign',
  },
  review: {
    bg: 'bg-amber-100 dark:bg-amber-900/40',
    text: 'text-amber-700 dark:text-amber-300',
    label: 'Review',
  },
}

function badgeClasses(actionType) {
  const b = ACTION_BADGE[actionType] ?? ACTION_BADGE.review
  return `${b.bg} ${b.text}`
}

function badgeLabel(actionType) {
  return (ACTION_BADGE[actionType] ?? ACTION_BADGE.review).label
}

const micAriaLabel = computed(() => {
  if (voiceState.value === 'idle') return 'Start voice recording'
  if (voiceState.value === 'listening') return 'Stop voice recording'
  return 'Processing'
})
</script>

<template>
  <article class="app-surface-card app-section-padding">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="typo-section-title">Ask Your Data</h2>
        <p class="mt-1 typo-muted">
          Ask a natural-language question about schedules, guides, bookings, and more.
        </p>
      </div>
      <span
        class="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
      >
        AI
      </span>
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Input row                                                           -->
    <!-- ------------------------------------------------------------------ -->
    <div class="mt-5 flex items-center gap-3">
      <!-- Mic button -->
      <div v-if="speechSupported" class="relative flex-shrink-0">
        <!-- Pulsing ring (listening state) -->
        <span
          v-if="voiceState === 'listening'"
          class="absolute inset-0 rounded-full bg-red-400 opacity-40"
          style="animation: ping 1s cubic-bezier(0, 0, 0.2, 1) infinite"
          aria-hidden="true"
        />
        <button
          type="button"
          :aria-label="micAriaLabel"
          :disabled="voiceState === 'processing'"
          class="relative z-10 flex h-11 w-11 items-center justify-center rounded-full border transition focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
          :class="{
            'border-slate-300 bg-white text-blue-600 hover:bg-blue-50 dark:border-white/15 dark:bg-[#1C2333] dark:text-blue-400 dark:hover:bg-blue-900/20':
              voiceState === 'idle' || voiceState === 'result',
            'border-red-400 bg-red-50 text-red-600 dark:border-red-600/60 dark:bg-red-950/40 dark:text-red-400':
              voiceState === 'listening',
            'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400 dark:border-white/10 dark:bg-white/5':
              voiceState === 'processing',
          }"
          @click="toggleMic"
        >
          <!-- Spinner (processing) -->
          <svg
            v-if="voiceState === 'processing'"
            class="h-5 w-5 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>

          <!-- Mic icon (idle / result) -->
          <svg
            v-else-if="voiceState === 'idle' || voiceState === 'result'"
            class="h-5 w-5"
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              d="M12 1a4 4 0 014 4v6a4 4 0 01-8 0V5a4 4 0 014-4zm0 2a2 2 0 00-2 2v6a2 2 0 004 0V5a2 2 0 00-2-2z"
            />
            <path d="M19 11a1 1 0 012 0 9 9 0 01-18 0 1 1 0 012 0 7 7 0 0014 0z" />
            <path d="M11 20h2v3h-2z" />
          </svg>

          <!-- Mic-stop icon (listening) -->
          <svg v-else class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        </button>
      </div>

      <!-- Text input -->
      <div class="relative flex-1">
        <input
          v-model="question"
          type="text"
          maxlength="500"
          :disabled="voiceState === 'processing' || voiceState === 'listening'"
          :placeholder="
            voiceState === 'listening'
              ? 'Listening...'
              : 'e.g. How many upcoming schedules have no guide?'
          "
          class="w-full rounded-xl border px-4 py-2.5 pr-12 typo-body transition focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
          :class="{
            'border-red-400 bg-red-50/50 dark:border-red-600/60 dark:bg-red-950/20':
              voiceState === 'listening',
            'border-slate-300 bg-white dark:border-white/15 dark:bg-[#1C2333]':
              voiceState !== 'listening',
            'cursor-not-allowed opacity-60': voiceState === 'processing',
          }"
          @keydown="handleKeydown"
        />
        <!-- Character count -->
        <span
          v-if="question.length > 400"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-xs"
          :class="question.length >= 500 ? 'text-red-500' : 'text-slate-400'"
        >
          {{ question.length }}/500
        </span>
      </div>

      <!-- Send button -->
      <button
        type="button"
        :disabled="!question.trim() || voiceState === 'processing' || voiceState === 'listening'"
        class="flex h-11 items-center gap-1.5 rounded-xl px-4 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
        :class="
          voiceState === 'processing'
            ? 'bg-slate-100 text-slate-400 dark:bg-white/5'
            : 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500'
        "
        @click="submitQuestion"
      >
        <svg
          class="h-4 w-4"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 12h15" />
        </svg>
        Ask
      </button>
    </div>

    <!-- Hint text below input -->
    <p v-if="voiceState === 'listening'" class="mt-2 typo-caption text-red-500 dark:text-red-400">
      Recording — tap the mic button or the stop icon to stop
    </p>
    <p v-else-if="voiceState === 'processing'" class="mt-2 typo-caption">Analyzing your data…</p>
    <p v-else class="mt-2 typo-caption">
      <span v-if="speechSupported">Tap the mic to speak, or type and press Enter.</span>
      <span v-else>Type your question and press Enter or click Ask.</span>
    </p>

    <!-- API error -->
    <p
      v-if="apiError"
      class="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2.5 typo-body text-rose-700 dark:border-rose-800 dark:bg-rose-950/45 dark:text-rose-300"
    >
      {{ apiError }}
    </p>

    <!-- ------------------------------------------------------------------ -->
    <!-- Result area                                                         -->
    <!-- ------------------------------------------------------------------ -->
    <template v-if="result && voiceState === 'result'">
      <div class="mt-6 space-y-5 border-t border-slate-200 pt-6 dark:border-white/10">
        <!-- Chart FIRST (more visual) -->
        <div
          v-if="result.chart"
          class="animate-slideUp rounded-xl border border-slate-200 bg-gradient-to-br from-blue-50 to-slate-50 p-6 shadow-sm dark:border-white/10 dark:from-blue-950/20 dark:to-[#1A2231]"
        >
          <div class="flex items-center gap-2">
            <svg
              class="h-5 w-5 text-blue-600 dark:text-blue-400"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <p class="typo-section-title text-base">{{ result.chart.title }}</p>
          </div>

          <!-- number -->
          <div
            v-if="result.chart.type === 'number' && result.chart.data?.length"
            class="mt-6 flex flex-col items-center justify-center gap-2 py-8"
          >
            <span class="text-7xl font-bold text-blue-600 dark:text-blue-400">
              {{ result.chart.data[0].value.toLocaleString() }}
            </span>
            <span class="typo-muted text-lg font-medium">{{ result.chart.data[0].label }}</span>
          </div>

          <!-- bar -->
          <div v-else-if="result.chart.type === 'bar' && barChartData" class="mt-6 space-y-4">
            <div
              v-for="item in barChartData.items"
              :key="item.label"
              class="grid grid-cols-[minmax(0,200px)_1fr_80px] items-center gap-4"
            >
              <span class="typo-body truncate font-medium text-slate-700 dark:text-slate-300">{{
                item.label
              }}</span>
              <div class="h-4 overflow-hidden rounded-full bg-slate-200 dark:bg-white/10">
                <div
                  class="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-700"
                  :style="{ width: item.pct }"
                />
              </div>
              <span class="typo-body text-right font-bold text-slate-800 dark:text-slate-100">{{
                item.value.toLocaleString()
              }}</span>
            </div>
          </div>

          <!-- line -->
          <div
            v-else-if="result.chart.type === 'line' && lineChartData"
            class="mt-4 overflow-x-auto"
          >
            <svg
              :viewBox="`0 0 ${lineChartData.W} ${lineChartData.H}`"
              class="w-full"
              :style="{ minWidth: '320px', height: '160px' }"
              overflow="visible"
              role="img"
              :aria-label="result.chart.title"
            >
              <line
                v-for="g in lineChartData.gridLines"
                :key="g.y"
                :x1="lineChartData.padL"
                :y1="g.y"
                :x2="lineChartData.W - 16"
                :y2="g.y"
                stroke="#e2e8f0"
                stroke-width="1"
              />
              <text
                v-for="g in lineChartData.gridLines"
                :key="`lbl-${g.y}`"
                :x="lineChartData.padL - 6"
                :y="g.y + 4"
                text-anchor="end"
                fill="#94a3b8"
                style="font-size: 10px; font-family: inherit"
              >
                {{ g.label }}
              </text>
              <path
                :d="lineChartData.pathD"
                fill="none"
                stroke="#0284c7"
                stroke-width="2.5"
                stroke-linejoin="round"
                stroke-linecap="round"
              />
              <circle
                v-for="pt in lineChartData.points"
                :key="`pt-${pt.x}`"
                :cx="pt.x"
                :cy="pt.y"
                r="4"
                fill="#0284c7"
                stroke="white"
                stroke-width="1.5"
              />
              <text
                v-for="pt in lineChartData.points"
                :key="`xl-${pt.x}`"
                :x="pt.x"
                :y="lineChartData.H - lineChartData.padB + 14"
                text-anchor="middle"
                fill="#94a3b8"
                style="font-size: 10px; font-family: inherit"
              >
                {{ pt.label }}
              </text>
            </svg>
          </div>

          <!-- donut -->
          <div
            v-else-if="result.chart.type === 'donut' && donutData"
            class="mt-4 flex flex-col items-center gap-4 sm:flex-row sm:items-start"
          >
            <svg
              viewBox="0 0 160 160"
              class="h-40 w-40 flex-shrink-0"
              role="img"
              :aria-label="result.chart.title"
            >
              <path
                v-for="seg in donutData.segments"
                :key="seg.label"
                :d="seg.d"
                :fill="seg.color"
                stroke="white"
                stroke-width="1.5"
              />
              <text
                :x="donutData.cx"
                :y="donutData.cy + 5"
                text-anchor="middle"
                fill="#64748b"
                style="font-size: 12px; font-family: inherit"
              >
                Total
              </text>
              <text
                :x="donutData.cx"
                :y="donutData.cy + 20"
                text-anchor="middle"
                fill="#1e293b"
                style="font-size: 16px; font-weight: 600; font-family: inherit"
              >
                {{ donutData.total.toLocaleString() }}
              </text>
            </svg>
            <div class="space-y-2">
              <div
                v-for="seg in donutData.segments"
                :key="seg.label"
                class="flex items-center gap-2"
              >
                <span
                  class="h-3 w-3 flex-shrink-0 rounded-full"
                  :style="{ backgroundColor: seg.color }"
                />
                <span class="typo-caption text-slate-700 dark:text-slate-300">{{ seg.label }}</span>
                <span class="typo-caption font-semibold text-slate-700 dark:text-slate-200">{{
                  seg.value.toLocaleString()
                }}</span>
                <span class="typo-caption text-slate-400">({{ seg.pct }}%)</span>
              </div>
            </div>
          </div>

          <!-- list -->
          <ol
            v-else-if="result.chart.type === 'list' && result.chart.data?.length"
            class="mt-4 space-y-2"
          >
            <li
              v-for="(item, idx) in result.chart.data"
              :key="item.label"
              class="flex items-center gap-3"
            >
              <span
                class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 dark:bg-blue-900/50 dark:text-blue-300"
              >
                {{ idx + 1 }}
              </span>
              <span class="flex-1 typo-body text-slate-700 dark:text-slate-300">{{
                item.label
              }}</span>
              <span class="typo-body font-semibold text-slate-800 dark:text-slate-100">{{
                item.value.toLocaleString()
              }}</span>
            </li>
          </ol>

          <!-- comparison -->
          <div
            v-else-if="result.chart.type === 'comparison' && result.chart.data?.length >= 2"
            class="mt-4 grid grid-cols-2 gap-4"
          >
            <div
              v-for="item in result.chart.data.slice(0, 2)"
              :key="item.label"
              class="flex flex-col items-center justify-center gap-1 rounded-xl border border-slate-200 py-5 dark:border-white/10"
            >
              <span class="text-4xl font-bold text-slate-800 dark:text-slate-100">{{
                item.value.toLocaleString()
              }}</span>
              <span class="typo-caption">{{ item.label }}</span>
            </div>
            <!-- Delta -->
            <div
              v-if="result.chart.data.length >= 2"
              class="col-span-2 flex items-center justify-center gap-1.5"
            >
              <template v-if="result.chart.data[1].value !== 0">
                <svg
                  class="h-4 w-4"
                  :class="
                    result.chart.data[0].value >= result.chart.data[1].value
                      ? 'text-emerald-500'
                      : 'text-rose-500'
                  "
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    v-if="result.chart.data[0].value >= result.chart.data[1].value"
                    fill-rule="evenodd"
                    d="M10 17a1 1 0 01-1-1V6.414L5.707 9.707a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0l5 5a1 1 0 01-1.414 1.414L11 6.414V16a1 1 0 01-1 1z"
                  />
                  <path
                    v-else
                    fill-rule="evenodd"
                    d="M10 3a1 1 0 011 1v9.586l3.293-3.293a1 1 0 011.414 1.414l-5 5a1 1 0 01-1.414 0l-5-5a1 1 0 011.414-1.414L9 13.586V4a1 1 0 011-1z"
                  />
                </svg>
                <span
                  class="typo-caption font-semibold"
                  :class="
                    result.chart.data[0].value >= result.chart.data[1].value
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-rose-600 dark:text-rose-400'
                  "
                >
                  {{
                    Math.abs(
                      Math.round(
                        ((result.chart.data[0].value - result.chart.data[1].value) /
                          result.chart.data[1].value) *
                          100,
                      ),
                    )
                  }}%
                  {{
                    result.chart.data[0].value >= result.chart.data[1].value
                      ? 'increase'
                      : 'decrease'
                  }}
                </span>
              </template>
            </div>
          </div>
        </div>

        <!-- Answer text SECOND (supporting detail) -->
        <div
          class="animate-fadeIn rounded-xl border border-blue-200 bg-blue-50 px-5 py-4 dark:border-blue-800/50 dark:bg-blue-950/30"
        >
          <div class="flex items-center gap-2">
            <svg
              class="h-5 w-5 text-blue-600 dark:text-blue-400"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p class="typo-card-label text-blue-600 dark:text-blue-400">Answer</p>
          </div>
          <p class="mt-2 text-base font-medium leading-relaxed text-slate-800 dark:text-slate-100">
            {{ result.answer }}
          </p>
        </div>

        <!-- Recommendations -->
        <div v-if="result.recommendations?.length" class="mt-5">
          <p class="typo-card-label">Recommended Actions</p>
          <div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <article
              v-for="rec in result.recommendations"
              :key="rec.title"
              class="rounded-xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#1C2333]"
            >
              <div class="flex items-start justify-between gap-2">
                <p class="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  {{ rec.title }}
                </p>
                <span
                  class="flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold"
                  :class="badgeClasses(rec.action_type)"
                >
                  {{ badgeLabel(rec.action_type) }}
                </span>
              </div>
              <p class="mt-2 typo-caption leading-relaxed">{{ rec.description }}</p>
            </article>
          </div>
        </div>

        <!-- SQL used (collapsible) -->
        <div v-if="result.sql_used" class="mt-4">
          <button
            type="button"
            class="flex items-center gap-1 typo-caption hover:text-slate-700 dark:hover:text-slate-300"
            @click="showSql = !showSql"
          >
            <svg
              class="h-3 w-3 transition-transform"
              :class="showSql ? 'rotate-90' : ''"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fill-rule="evenodd"
                d="M7.293 4.293a1 1 0 011.414 0L14 9.586l-5.293 5.293a1 1 0 01-1.414-1.414L11.586 9 6.293 3.707a1 1 0 010-1.414z"
              />
            </svg>
            {{ showSql ? 'Hide SQL' : 'View SQL used' }}
          </button>
          <pre
            v-if="showSql"
            class="mt-2 overflow-x-auto rounded-lg border border-slate-200 bg-slate-900 p-3 text-xs text-green-400 dark:border-white/10"
            >{{ result.sql_used }}</pre
          >
        </div>
      </div>
    </template>
  </article>

  <!-- -------------------------------------------------------------------- -->
  <!-- Content Safety Blocked Modal                                          -->
  <!-- -------------------------------------------------------------------- -->
  <div
    v-if="showContentSafetyModal"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    role="dialog"
    aria-modal="true"
    aria-labelledby="cs-modal-title"
    @click.self="dismissContentSafetyModal"
  >
    <div
      class="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-white/10 dark:bg-[#161B27] dark:shadow-black/60"
    >
      <!-- Icon -->
      <div
        class="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-950/60"
      >
        <svg
          class="h-6 w-6 text-red-600 dark:text-red-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
          />
        </svg>
      </div>

      <h3 id="cs-modal-title" class="mt-4 typo-modal-title">Content Flagged</h3>
      <p class="mt-2 typo-body">
        Your question was flagged by our content safety system. Please rephrase your question and
        try again.
      </p>

      <button
        type="button"
        class="mt-5 w-full rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-red-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
        @click="dismissContentSafetyModal"
      >
        Got it
      </button>
    </div>
  </div>
</template>

<style scoped>
@keyframes ping {
  75%,
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.animate-slideUp {
  animation: slideUp 0.4s ease-out;
}

.animate-fadeIn {
  animation: fadeIn 0.5s ease-out 0.2s both;
}
</style>
