<script setup>
defineProps({
  title: { type: String, default: 'Lost at Sea!' },
  message: { type: String, default: 'We couldn\u2019t load the data. Please try again.' },
  details: { type: String, default: '' },
})

defineEmits(['retry'])
</script>

<template>
  <div class="ocean-error">
    <!-- Text content above the boat -->
    <div class="ocean-error__text">
      <h2 class="text-3xl font-bold text-[#0077B6]">{{ title }}</h2>
      <p class="text-gray-500 text-base mt-2">{{ message }}</p>
      <p v-if="details" class="text-gray-400 text-sm mt-3 font-mono break-all">{{ details }}</p>

      <button class="ocean-error__retry" @click="$emit('retry')">Try Again</button>
    </div>

    <!-- Boat + ocean section (full width) -->
    <div class="ocean-error__scene">
      <!-- Bobbing boat sitting on the water -->
      <div class="ocean-error__boat" aria-hidden="true">
        <svg
          viewBox="0 0 120 80"
          width="200"
          height="134"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <!-- Sail -->
          <polygon points="60,8 60,48 34,48" fill="#CAF0F8" stroke="#0077B6" stroke-width="2" />
          <polygon points="60,14 60,48 82,48" fill="#E0F7FF" stroke="#0077B6" stroke-width="2" />
          <!-- Mast -->
          <line
            x1="60"
            y1="8"
            x2="60"
            y2="58"
            stroke="#0077B6"
            stroke-width="2.5"
            stroke-linecap="round"
          />
          <!-- Hull -->
          <path
            d="M24 56 C24 56 30 72 60 72 C90 72 96 56 96 56 Z"
            fill="#0077B6"
            stroke="#005a8c"
            stroke-width="1.5"
          />
          <!-- Hull stripe -->
          <path
            d="M32 62 C32 62 40 70 60 70 C80 70 88 62 88 62"
            fill="none"
            stroke="#00B4D8"
            stroke-width="1.5"
          />
          <!-- Porthole -->
          <circle cx="52" cy="63" r="3" fill="#E0F7FF" stroke="#005a8c" stroke-width="1" />
          <circle cx="68" cy="63" r="3" fill="#E0F7FF" stroke="#005a8c" stroke-width="1" />
          <!-- Flag -->
          <rect
            x="58"
            y="6"
            width="12"
            height="8"
            rx="1"
            fill="#ff6b6b"
            stroke="#d63031"
            stroke-width="0.8"
          />
        </svg>
      </div>

      <!-- Waves (full width) -->
      <div class="ocean-error__waves" aria-hidden="true">
        <svg
          class="ocean-error__wave ocean-error__wave--1"
          viewBox="0 0 1440 120"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M0,40 C360,100 720,0 1080,60 C1260,90 1380,50 1440,40 L1440,120 L0,120 Z"
            fill="#CAF0F8"
          />
        </svg>
        <svg
          class="ocean-error__wave ocean-error__wave--2"
          viewBox="0 0 1440 120"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M0,60 C240,10 480,100 720,50 C960,0 1200,80 1440,40 L1440,120 L0,120 Z"
            fill="#90E0EF"
            opacity="0.7"
          />
        </svg>
        <svg
          class="ocean-error__wave ocean-error__wave--3"
          viewBox="0 0 1440 120"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M0,80 C180,30 360,90 540,50 C720,10 900,70 1080,40 C1260,10 1380,60 1440,50 L1440,120 L0,120 Z"
            fill="#00B4D8"
            opacity="0.5"
          />
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ocean-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: fadeSlideIn 0.6s ease-out both;
}

.ocean-error__text {
  text-align: center;
  padding: 2.5rem 2rem 1.5rem;
  max-width: 520px;
  width: 100%;
}

/* --- Scene: boat floating on waves --- */
.ocean-error__scene {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* --- Bobbing boat --- */
.ocean-error__boat {
  position: relative;
  z-index: 2;
  margin-bottom: -60px;
  animation: bob 3s ease-in-out infinite;
  display: inline-block;
}

/* --- Retry button --- */
.ocean-error__retry {
  margin-top: 1.75rem;
  padding: 0.75rem 2.5rem;
  border-radius: 9999px;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  background-color: #0077b6;
  cursor: pointer;
  border: none;
  transition:
    background-color 0.2s,
    transform 0.15s;
}
.ocean-error__retry:hover {
  background-color: #0097e7;
}
.ocean-error__retry:active {
  transform: scale(0.97);
}

/* --- Waves (full width) --- */
.ocean-error__waves {
  position: relative;
  width: 100%;
  height: 120px;
  overflow: hidden;
}

.ocean-error__wave {
  position: absolute;
  bottom: 0;
  width: 200%;
  height: 100%;
}

.ocean-error__wave--1 {
  animation: waveScroll 7s linear infinite;
}
.ocean-error__wave--2 {
  animation: waveScroll 5s linear infinite reverse;
}
.ocean-error__wave--3 {
  animation: waveScroll 9s linear infinite;
}

/* --- Keyframes --- */
@keyframes bob {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  25% {
    transform: translateY(-6px) rotate(-2deg);
  }
  50% {
    transform: translateY(2px) rotate(1deg);
  }
  75% {
    transform: translateY(-4px) rotate(-1deg);
  }
}

@keyframes waveScroll {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
