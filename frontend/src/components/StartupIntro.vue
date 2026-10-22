<template>
  <Teleport to="body">
    <section
      ref="surface"
      class="startup-intro"
      :class="{ 'is-still': stillAt !== null }"
      :style="{ '--intro-frame': `${stillAt ?? 0}ms` }"
      role="dialog"
      aria-modal="true"
      aria-labelledby="startup-title"
      tabindex="-1"
      @keydown.esc.prevent="finish"
      @keydown.tab.prevent="skipButton?.focus()"
    >
      <div class="startup-topline">
        <svg class="startup-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
          <path d="M4 8V4h4m8 0h4v4M4 16v4h4m8 0h4v-4M8 8h8v8H8z" />
        </svg>
        <button ref="skipButton" class="startup-skip" type="button" @click="finish">
          跳过动画 <span aria-hidden="true">→</span>
        </button>
      </div>

      <div class="startup-composition">
        <svg class="startup-drawing" viewBox="0 0 640 440" fill="none" aria-hidden="true">
          <defs>
            <pattern id="intro-hatching" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
              <path d="M0 0V8" stroke="currentColor" stroke-opacity=".12" stroke-width="1" />
            </pattern>
            <clipPath id="intro-part-clip">
              <path d="M200 70H460V240H425V315H344L321 350H200Z" />
            </clipPath>
          </defs>

          <g class="startup-construction" stroke="currentColor" stroke-width="1">
            <path d="M158 70H505M158 350H505M200 28V393M460 28V393" stroke-dasharray="3 7" />
            <path d="M320 192V212M310 202H330" />
            <circle cx="320" cy="202" r="3" />
          </g>

          <g class="startup-material" clip-path="url(#intro-part-clip)">
            <path d="M200 70H460V240H425V315H344L321 350H200Z" fill="#e8dfce" />
            <path d="M200 70H460V240H425V315H344L321 350H200Z" fill="url(#intro-hatching)" />
          </g>

          <path class="startup-outline" d="M200 70H460V240H425V315H344L321 350H200Z" pathLength="1" stroke="currentColor" stroke-width="2" stroke-linejoin="round" />

          <g class="startup-holes" fill="var(--studio-bg, #f6f4ed)" stroke="currentColor" stroke-width="1.4">
            <rect x="214" y="88" width="7" height="20" rx="3.5" />
            <rect x="214" y="196" width="7" height="20" rx="3.5" />
            <rect x="441" y="212" width="7" height="20" rx="3.5" />
          </g>

          <g class="startup-dimensions" stroke="currentColor" stroke-width="1">
            <path d="M200 54V29M460 54V29M200 39H460M196 35L204 43M456 35L464 43" />
            <path d="M476 70H505M476 350H505M495 70V350M491 66L499 74M491 346L499 354" />
            <path d="M332 336L362 375H410" />
          </g>
          <g class="startup-dimension-text" fill="currentColor">
            <text x="330" y="26" text-anchor="middle">405 px</text>
            <text x="517" y="210" text-anchor="middle" transform="rotate(90 517 210)">434 px</text>
            <text x="371" y="398">轮廓与内孔</text>
          </g>

          <g class="startup-annotation" stroke="currentColor" stroke-width="2">
            <path d="M184 80V54H210M450 54H476V80M476 340V366H450M210 366H184V340" />
          </g>
          <g class="startup-scan" clip-path="url(#intro-part-clip)">
            <path d="M178 70H480" stroke="currentColor" stroke-width="2" />
          </g>
        </svg>

        <div class="startup-identity">
          <h1 id="startup-title">零件数据生成系统</h1>
          <p>从零件轮廓，到训练数据。</p>
        </div>
        <div class="startup-stages" aria-hidden="true">
          <span class="startup-stage startup-stage-contour"><i></i>轮廓</span>
          <span class="startup-stage-connector"></span>
          <span class="startup-stage startup-stage-material"><i></i>材质</span>
          <span class="startup-stage-connector"></span>
          <span class="startup-stage startup-stage-label"><i></i>标注</span>
        </div>
      </div>

      <span class="startup-caption" aria-hidden="true">制图工作台</span>
    </section>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({ stillAt: { type: Number, default: null } })
const emit = defineEmits(['finish'])
const surface = ref(null)
const skipButton = ref(null)
let timer
let finished = false
let previousOverflow = ''
let motionPreference

function finish() {
  if (finished) return
  finished = true
  clearTimeout(timer)
  emit('finish')
}

function handleMotionPreference(event) {
  if (event.matches) finish()
}

onMounted(() => {
  previousOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  surface.value?.focus({ preventScroll: true })
  motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)')
  motionPreference.addEventListener('change', handleMotionPreference)
  if (motionPreference.matches) {
    finish()
  } else if (props.stillAt === null) {
    // Independent of animation events and API requests, so the workspace always opens.
    timer = window.setTimeout(finish, 2200)
  }
})

onBeforeUnmount(() => {
  clearTimeout(timer)
  document.body.style.overflow = previousOverflow
  motionPreference?.removeEventListener('change', handleMotionPreference)
})
</script>

<style scoped>
.startup-intro {
  --intro-ink: var(--studio-primary, #a85b21);
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: grid;
  place-items: center;
  overflow: hidden;
  color: var(--intro-ink);
  background: var(--studio-bg, #f6f4ed);
  font-family: var(--studio-font, "Microsoft YaHei", sans-serif);
  animation: intro-depart 280ms cubic-bezier(.4, 0, 1, 1) calc(1920ms - var(--intro-frame)) both;
}
.startup-intro:focus { outline: none; }
.startup-intro::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: linear-gradient(#a89d8112 1px, transparent 1px), linear-gradient(90deg, #a89d8112 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(ellipse at 50% 42%, #000 5%, transparent 66%);
}
.startup-topline { position: absolute; top: 28px; right: 36px; left: 36px; display: flex; align-items: center; justify-content: space-between; }
.startup-mark { width: 28px; height: 28px; }
.startup-skip { display: inline-flex; align-items: center; gap: 12px; min-height: 44px; padding: 8px 12px; border: 1px solid transparent; border-radius: 3px; color: var(--studio-muted, #636c5f); background: transparent; font: inherit; font-size: 16px; cursor: pointer; transition: color 140ms ease, background-color 140ms ease; }
.startup-skip:hover { color: var(--intro-ink); background: #a85b210b; }
.startup-skip:active { transform: translateY(1px); }
.startup-skip:focus-visible { outline: 2px solid var(--intro-ink); outline-offset: 3px; }
.startup-skip span { font-size: 21px; }
.startup-composition { position: relative; width: min(640px, calc(100vw - 36px)); padding-bottom: 18px; text-align: center; }
.startup-drawing { display: block; width: min(100%, 580px); margin: 0 auto -8px; overflow: visible; }
.startup-construction { color: #b8b09c; animation: intro-appear 300ms ease calc(0ms - var(--intro-frame)) both; }
.startup-outline { stroke-dasharray: 1; stroke-dashoffset: 1; animation: intro-trace 720ms cubic-bezier(.45, 0, .2, 1) calc(80ms - var(--intro-frame)) both; }
.startup-holes { animation: intro-appear 240ms ease calc(470ms - var(--intro-frame)) both; }
.startup-material { transform-box: fill-box; transform-origin: top; animation: intro-material 650ms cubic-bezier(.22, 1, .36, 1) calc(780ms - var(--intro-frame)) both; }
.startup-dimensions { color: #af9778; animation: intro-appear 280ms ease calc(620ms - var(--intro-frame)) both; }
.startup-dimension-text { color: #87664b; font-size: 16px; animation: intro-appear 260ms ease calc(770ms - var(--intro-frame)) both; }
.startup-annotation { animation: intro-register 350ms cubic-bezier(.22, 1, .36, 1) calc(1160ms - var(--intro-frame)) both; transform-origin: center; }
.startup-scan path { animation: intro-scan 600ms cubic-bezier(.4, 0, .2, 1) calc(830ms - var(--intro-frame)) both; }
.startup-identity { animation: intro-identity 420ms cubic-bezier(.22, 1, .36, 1) calc(160ms - var(--intro-frame)) both; }
.startup-identity h1 { margin: 0; color: var(--studio-text, #252a30); font-size: clamp(27px, 3.3vw, 38px); font-weight: 600; line-height: 1.4; }
.startup-identity p { margin: 13px 0 0; color: var(--studio-muted, #636c5f); font-size: 17px; line-height: 1.7; }
.startup-stages { display: flex; align-items: center; justify-content: center; gap: 17px; margin-top: 34px; color: #745c43; font-size: 15px; line-height: 1.5; }
.startup-stage { display: inline-flex; align-items: center; gap: 8px; animation: intro-appear 240ms ease calc(420ms - var(--intro-frame)) both; }
.startup-stage i { width: 5px; height: 5px; background: currentColor; }
.startup-stage-material { animation-delay: calc(850ms - var(--intro-frame)); }
.startup-stage-label { animation-delay: calc(1280ms - var(--intro-frame)); }
.startup-stage-connector { width: 28px; height: 1px; background: #c9bcaa; animation: intro-appear 200ms ease calc(700ms - var(--intro-frame)) both; }
.startup-stage-connector:nth-of-type(4) { animation-delay: calc(1100ms - var(--intro-frame)); }
.startup-caption { position: absolute; bottom: 28px; color: #747668; font-size: 14px; }
.is-still, .is-still *, .is-still::before { animation-play-state: paused !important; }
@keyframes intro-trace { to { stroke-dashoffset: 0; } }
@keyframes intro-appear { from { opacity: 0; } to { opacity: 1; } }
@keyframes intro-material { from { opacity: 0; transform: scaleY(.02); } to { opacity: 1; transform: scaleY(1); } }
@keyframes intro-register { from { opacity: 0; transform: scale(1.035); } to { opacity: 1; transform: scale(1); } }
@keyframes intro-identity { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes intro-scan { 0% { opacity: 0; transform: translateY(0); } 12% { opacity: .65; } 85% { opacity: .65; } 100% { opacity: 0; transform: translateY(280px); } }
@keyframes intro-depart { to { opacity: 0; } }
@media (max-width: 600px) {
  .startup-topline { top: 16px; right: 16px; left: 20px; }
  .startup-composition { width: calc(100vw - 28px); }
  .startup-drawing { width: 100%; margin-bottom: 16px; }
  .startup-dimension-text { font-size: 23px; }
  .startup-identity h1 { font-size: clamp(24px, 6.4vw, 31px); }
  .startup-identity p { margin-top: 10px; font-size: 16px; }
  .startup-stages { gap: 12px; margin-top: 27px; }
  .startup-stage-connector { width: 22px; }
  .startup-caption { bottom: 22px; }
}
@media (max-height: 560px) and (min-width: 601px) {
  .startup-drawing { width: 340px; margin-bottom: 0; }
  .startup-identity h1 { font-size: 28px; }
  .startup-identity p { margin-top: 5px; }
  .startup-stages { margin-top: 15px; }
  .startup-dimension-text { font-size: 24px; }
  .startup-caption { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .startup-intro { display: none; }
  .startup-intro, .startup-intro * { animation: none; transition: none; }
}
</style>
