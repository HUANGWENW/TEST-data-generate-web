<template>
  <section class="project-navigation" aria-label="项目功能导航">
    <div class="folder-rail">
      <div class="folder-caption"><span class="project-reference">项目 / {{ String(route.params.id).slice(0, 8) }}</span><div v-if="navOverflow" class="folder-scroll-actions"><button type="button" aria-label="向左查看项目导航" :disabled="!canScrollLeft" @click="panNavigation(-1)">‹</button><button type="button" aria-label="向右查看项目导航" :disabled="!canScrollRight" @click="panNavigation(1)">›</button></div></div>
      <div ref="scrollport" class="folder-scrollport" @scroll.passive="updateScrollState">
        <nav ref="track" class="project-route-links" aria-label="当前项目导航">
          <span v-if="indicator.width" class="folder-indicator" :class="{ 'is-moving': moving }" :style="indicatorStyle" aria-hidden="true" />
          <router-link v-for="item in projectLinks" :key="item.path" :to="root + item.path"><span class="tab-status" aria-hidden="true" />{{ item.label }}</router-link>
        </nav>
      </div>
    </div>
    <div id="project-subnavigation" class="project-subnavigation">
      <nav v-if="sections.length" :key="route.path" class="context-links" aria-label="当前页面内容导航">
        <button v-for="item in sections" :key="item.id" type="button" :class="{ active: selectedSection === item.id }" :aria-pressed="selectedSection === item.id" @click="goToSection(item.id)">{{ item.label }}</button>
      </nav>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({ root: { type: String, required: true } })
const route = useRoute()
const scrollport = ref(null), track = ref(null)
const indicator = ref({ left: 0, width: 0 }), moving = ref(false), activeSection = ref('')
const navOverflow = ref(false), canScrollLeft = ref(false), canScrollRight = ref(false)
let resizeObserver = null, disposed = false
const projectLinks = [
  { path: '', label: '素材管理' },
  { path: '/step/1', label: '01 提取 Mask' },
  { path: '/step/2', label: '02 透明零件' },
  { path: '/step/3', label: '03 合成数据' },
  { path: '/gallery', label: '结果阅览' },
  { path: '/dxf', label: 'DXF 文件' }
]
const sectionMap = {
  '/step/1': [{ id: 'mask-extract-settings', label: '提取设置' }, { id: 'mask-review', label: 'Mask 验收' }],
  '/step/2': [{ id: 'part-mask-input', label: '选择 Mask' }, { id: 'part-fill-settings', label: '纹理填充' }, { id: 'part-review', label: '零件验收' }],
  '/step/3': [{ id: 'dataset-parts', label: '选择零件' }, { id: 'dataset-settings', label: '背景与参数' }, { id: 'dataset-preview', label: '排布预览' }],
  '/gallery': [{ id: 'gallery-batches', label: '选择批次' }, { id: 'gallery-results', label: '生成结果' }],
  '/dxf': [{ id: 'dxf-upload', label: '上传 DXF' }, { id: 'dxf-files', label: '已保存文件' }]
}
const sections = computed(() => sectionMap[route.path.slice(props.root.length)] || [])
const selectedSection = computed(() => activeSection.value || sections.value[0]?.id)
const indicatorStyle = computed(() => ({ width: `${indicator.value.width}px`, transform: `translateX(${indicator.value.left}px)` }))
function measureIndicator(animate = false, reveal = false) {
  if (disposed || !track.value) return
  const active = track.value.querySelector('.router-link-exact-active')
  if (!active) { indicator.value = { left: 0, width: 0 }; return }
  moving.value = animate
  indicator.value = { left: active.offsetLeft, width: active.offsetWidth }
  if (reveal && scrollport.value) {
    const port = scrollport.value
    const left = active.offsetLeft, right = left + active.offsetWidth
    if (left < port.scrollLeft || right > port.scrollLeft + port.clientWidth) port.scrollTo({ left: Math.max(0, left - (port.clientWidth - active.offsetWidth) / 2), behavior: 'instant' })
  }
  updateScrollState()
}
function updateScrollState() {
  const port = scrollport.value
  if (!port) return
  navOverflow.value = port.scrollWidth > port.clientWidth + 1
  canScrollLeft.value = port.scrollLeft > 1
  canScrollRight.value = port.scrollLeft + port.clientWidth < port.scrollWidth - 1
}
function panNavigation(direction) {
  const port = scrollport.value
  if (port) port.scrollBy({ left: direction * Math.max(160, port.clientWidth * .7), behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' })
}
function goToSection(id) {
  const element = document.getElementById(id)
  if (!element) return
  activeSection.value = id
  element.scrollIntoView({ block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' })
}
watch(() => route.path, async () => {
  activeSection.value = ''
  await nextTick()
  measureIndicator(true, true)
})
onMounted(async () => {
  await nextTick()
  if (disposed || !scrollport.value || !track.value) return
  measureIndicator(false, true)
  resizeObserver = new ResizeObserver(() => measureIndicator(false, true))
  resizeObserver.observe(scrollport.value)
  resizeObserver.observe(track.value)
  document.fonts?.ready.then(() => measureIndicator(false, true))
})
onBeforeUnmount(() => { disposed = true; resizeObserver?.disconnect() })
</script>

<style scoped>
.project-navigation { --folder-brown: #583825; --folder-paper: #fffdf8; width: min(calc(100% - 64px), 1440px); margin: 14px auto 0; }
.folder-rail { display: flex; align-items: flex-end; gap: 18px; padding: 12px 12px 0; background: var(--folder-brown); border: 1px solid #4d2e1e; border-bottom: 0; border-radius: 6px 6px 0 0; }
.folder-caption { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-shrink: 0; align-self: center; margin-bottom: 10px; }
.project-reference { flex-shrink: 0; padding: 5px 18px 5px 4px; border-right: 1px solid #99745a; color: #f1e3d2; font: 16px/1.6 var(--studio-font); }
.folder-scroll-actions { display: flex; align-items: center; gap: 6px; }
.folder-scroll-actions button { display: grid; place-items: center; width: 44px; height: 44px; padding: 0; border: 1px solid #a07c60; border-radius: 5px; background: transparent; color: #fff4e4; font: 28px/1 var(--studio-font); cursor: pointer; }
.folder-scroll-actions button:hover:not(:disabled) { background: #774d32; }
.folder-scroll-actions button:disabled { opacity: .4; cursor: default; }
.folder-scroll-actions button:focus-visible { outline: 2px solid #efba85; outline-offset: 2px; }
.folder-scrollport { min-width: 0; flex: 1; overflow-x: auto; overflow-y: hidden; scrollbar-width: none; }
.folder-scrollport::-webkit-scrollbar { display: none; }
.project-route-links { position: relative; display: flex; align-items: stretch; width: max-content; min-width: 100%; }
.project-route-links a { position: relative; z-index: 1; display: flex; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0; min-height: 54px; padding: 12px 20px 10px; color: #f9f1e5; font-size: 18px; font-weight: 600; line-height: 1.5; text-decoration: none; white-space: nowrap; transition: color 160ms ease; }
.project-route-links a:hover { color: #ffdbb1; }
.project-route-links a.router-link-exact-active { color: #623b22; }
.project-route-links a:focus-visible { outline: 2px solid #efba85; outline-offset: -7px; border-radius: 9px 9px 0 0; }
.tab-status { width: 6px; height: 6px; flex-shrink: 0; border-radius: 50%; background: currentColor; opacity: 0; transition: opacity 160ms ease; }
.router-link-exact-active .tab-status { opacity: 1; }
.folder-indicator { position: absolute; z-index: 0; inset: 0 auto 0 0; background: var(--folder-paper); border-radius: 12px 12px 0 0; clip-path: polygon(14px 0, calc(100% - 14px) 0, 100% 100%, 0 100%); }
.folder-indicator.is-moving { transition: transform 240ms cubic-bezier(.22,.68,.2,1), width 240ms cubic-bezier(.22,.68,.2,1); }
.project-subnavigation { position: relative; z-index: 2; min-height: 66px; padding: 9px 20px; border: 1px solid #e0d7c9; border-top: 0; border-radius: 0 0 16px 16px; background: var(--folder-paper); box-shadow: 0 5px 12px rgb(77 46 30 / 7%); }
.context-links { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; animation: context-arrive 180ms ease-out; }
.context-links button { min-height: 46px; padding: 8px 18px; border: 1px solid transparent; border-radius: 24px; background: transparent; color: #5f584e; font: 18px/1.5 var(--studio-font); cursor: pointer; transition: color 140ms ease, background-color 140ms ease; }
.context-links button:hover { background: #f5eee4; color: #733f1d; }
.context-links button.active { background: #f0dfcb; color: #7a421d; border-color: #e4c6a6; font-weight: 600; }
.context-links button:active { transform: translateY(1px); }
@keyframes context-arrive { from { opacity: .5; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 1180px) { .folder-rail { display: block; padding-top: 8px; } .folder-caption { min-height: 36px; margin: 0 4px 8px; } .project-reference { padding: 2px 0; border-right: 0; } }
@media (max-width: 700px) { .project-navigation { width: calc(100% - 32px); } .folder-rail { padding-inline: 4px; } .folder-caption { margin-inline: 10px; } .project-route-links a { min-height: 52px; padding-inline: 18px; } .project-subnavigation { padding: 10px 12px; border-radius: 0 0 12px 12px; } .context-links { gap: 6px; } .context-links button { padding-inline: 14px; } }
@media (prefers-reduced-motion: reduce) { .folder-indicator.is-moving, .project-route-links a, .tab-status, .context-links button { transition: none; } .context-links { animation: none; } .context-links button:active { transform: none; } }
</style>
