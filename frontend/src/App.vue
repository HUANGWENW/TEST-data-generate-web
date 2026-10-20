<template>
  <div class="drafting-shell">
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
    <nav v-if="projectRoot" class="project-navigation" aria-label="当前项目导航">
      <span class="project-reference">项目 / {{ String(route.params.id).slice(0, 8) }}</span>
      <div class="project-route-links">
        <router-link v-for="item in projectLinks" :key="item.path" :to="projectRoot + item.path">{{ item.label }}</router-link>
      </div>
    </nav>
    <main class="route-workspace"><router-view /></main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const projectRoot = computed(() => route.params.id ? `/projects/${encodeURIComponent(String(route.params.id))}` : '')
const isProjectSection = computed(() => route.path === '/' || route.path.startsWith('/projects/'))
const projectLinks = [
  { path: '', label: '素材工作台' },
  { path: '/step/1', label: '01 提取 Mask' },
  { path: '/step/2', label: '02 透明零件' },
  { path: '/step/3', label: '03 合成数据' },
  { path: '/gallery', label: '结果阅览' },
  { path: '/dxf', label: 'DXF 文件' }
]
</script>

<style scoped>
.drafting-shell { min-height: 100dvh; background: var(--studio-bg); color: var(--studio-text); }
.drafting-header { width: min(calc(100% - 64px), 1440px); min-height: 72px; margin: 0 auto; display: flex; align-items: center; gap: 48px; border-bottom: 1px solid var(--studio-border); }
.drafting-brand { display: inline-flex; align-items: center; gap: 12px; color: var(--studio-text); text-decoration: none; font: 600 23px/1.4 var(--studio-serif); white-space: nowrap; }
.drafting-brand svg { color: var(--studio-primary); }
.drafting-navigation { display: flex; align-items: stretch; gap: 30px; align-self: stretch; }
.drafting-navigation a { display: flex; align-items: center; border-bottom: 2px solid transparent; text-decoration: none; color: var(--studio-muted); font-size: 14px; transition: color 120ms ease, border-color 120ms ease; }
.drafting-navigation a.router-link-exact-active, .drafting-navigation a.section-active { color: var(--studio-text); border-color: var(--studio-primary); font-weight: 600; }
.drafting-navigation a:hover { color: var(--studio-primary); }
.drafting-workspace-label { margin-left: auto; color: var(--studio-muted); font-size: 13px; white-space: nowrap; }
.project-navigation { width: min(calc(100% - 64px), 1440px); margin: 0 auto; display: flex; align-items: center; gap: 28px; min-height: 58px; border-bottom: 1px solid var(--studio-border); }
.project-reference { flex-shrink: 0; color: var(--studio-muted); font: 13px/1.6 var(--studio-mono); }
.project-route-links { display: flex; align-self: stretch; flex-wrap: wrap; gap: 0 24px; }
.project-route-links a { display: flex; align-items: center; min-height: 44px; color: var(--studio-muted); font-size: 13px; text-decoration: none; border-bottom: 2px solid transparent; }
.project-route-links a:hover { color: var(--studio-primary); }
.project-route-links a.router-link-exact-active { color: var(--studio-primary); border-bottom-color: var(--studio-primary); font-weight: 600; }
.route-workspace { min-width: 0; }
.drafting-header a:focus-visible, .project-navigation a:focus-visible { outline: 2px solid var(--studio-primary); outline-offset: 4px; }
@media (max-width: 1060px) { .project-navigation { align-items: flex-start; flex-direction: column; gap: 4px; padding-top: 13px; } }
@media (max-width: 700px) {
  .drafting-header { width: calc(100% - 32px); gap: 14px; flex-wrap: wrap; padding: 17px 0 0; }
  .drafting-brand { font-size: 22px; }
  .drafting-workspace-label { order: 1; }
  .drafting-navigation { order: 2; width: 100%; gap: 25px; min-height: 44px; }
  .project-navigation { width: calc(100% - 32px); }
  .project-route-links { width: 100%; gap: 0 20px; }
}
@media (prefers-reduced-motion: reduce) { .drafting-navigation a { transition: none; } }
</style>
