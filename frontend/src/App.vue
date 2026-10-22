<template>
  <div class="drafting-shell" :inert="introActive || undefined" :aria-hidden="introActive ? 'true' : undefined">
    <header class="drafting-header">
      <router-link to="/" class="drafting-brand" aria-label="零件数据，项目总览">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 8V4h4m8 0h4v4M4 16v4h4m8 0h4v-4M8 8h8v8H8z" /></svg>
        <span>零件数据</span>
      </router-link>
      <nav class="drafting-navigation" aria-label="主导航">
        <router-link to="/" :class="{ 'section-active': isProjectSection }">项目总览</router-link>
        <router-link to="/tasks">任务中心</router-link>
        <router-link to="/guide">使用指引</router-link>
      </nav>
      <span class="drafting-workspace-label">制图工作台</span>
    </header>
    <ProjectNavigation v-if="projectRoot" :root="projectRoot" />
    <main class="route-workspace"><router-view /></main>
  </div>
  <StartupIntro v-if="introActive" :still-at="introStillAt" @finish="finishIntro" />
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRoute } from 'vue-router'
import ProjectNavigation from './components/ProjectNavigation.vue'
import StartupIntro from './components/StartupIntro.vue'

const introSessionKey = 'parts-data:startup:v1'
const introQuery = new URLSearchParams(window.location.search)
const introPreview = introQuery.get('intro') === 'preview'
const requestedFrame = Number(introQuery.get('introFrame'))
const introStillAt = introPreview && introQuery.has('introFrame') && Number.isFinite(requestedFrame)
  ? Math.min(1800, Math.max(0, requestedFrame)) : null

function shouldShowIntro() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false
  if (introPreview) return true
  try { return window.sessionStorage.getItem(introSessionKey) !== 'seen' }
  catch { return true }
}

const introActive = ref(shouldShowIntro())

async function finishIntro() {
  const restoreFocus = document.activeElement?.closest('.startup-intro')
  introActive.value = false
  try { window.sessionStorage.setItem(introSessionKey, 'seen') } catch { /* Storage can be disabled. */ }
  await nextTick()
  if (restoreFocus) document.querySelector('.drafting-brand')?.focus({ preventScroll: true })
}

const route = useRoute()
const projectRoot = computed(() => route.params.id ? `/projects/${encodeURIComponent(String(route.params.id))}` : '')
const isProjectSection = computed(() => route.path === '/' || route.path.startsWith('/projects/'))
</script>

<style scoped>
.drafting-shell { min-height: 100dvh; background: var(--studio-bg); color: var(--studio-text); }
.drafting-header { width: min(calc(100% - 64px), 1440px); min-height: 72px; margin: 0 auto; display: flex; align-items: center; gap: 48px; border-bottom: 1px solid var(--studio-border); }
.drafting-brand { display: inline-flex; align-items: center; gap: 12px; color: var(--studio-text); text-decoration: none; font:600 26px/1.4 var(--studio-font); white-space: nowrap; }
.drafting-brand svg { color: var(--studio-primary); }
.drafting-navigation { display: flex; align-items: stretch; gap: 30px; align-self: stretch; }
.drafting-navigation a { display: flex; align-items: center; border-bottom: 2px solid transparent; text-decoration: none; color: var(--studio-muted); font-size:18px; transition: color 120ms ease, border-color 120ms ease; }
.drafting-navigation a.router-link-exact-active, .drafting-navigation a.section-active { color: var(--studio-text); border-color: var(--studio-primary); font-weight: 600; }
.drafting-navigation a:hover { color: var(--studio-primary); }
.drafting-workspace-label { margin-left: auto; color: var(--studio-muted); font-size:16px; white-space: nowrap; }
.route-workspace { min-width: 0; }
.drafting-header a:focus-visible { outline: 2px solid var(--studio-primary); outline-offset: 4px; }
@media (max-width: 700px) {
  .drafting-header { width: calc(100% - 32px); gap: 14px; flex-wrap: wrap; padding: 17px 0 0; }
  .drafting-brand { font-size:26px; }
  .drafting-workspace-label { order: 1; }
  .drafting-navigation { order: 2; width: 100%; gap: 25px; min-height: 44px; }
}
@media (prefers-reduced-motion: reduce) { .drafting-navigation a { transition: none; } }
</style>
