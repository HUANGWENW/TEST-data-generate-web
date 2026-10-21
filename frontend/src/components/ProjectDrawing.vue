<template>
  <div class="drawing-view" :aria-busy="loading">
    <div v-if="loading" class="drawing-state" role="status"><el-icon class="loading-icon"><Loading /></el-icon><span>正在读取预览</span></div>
    <div v-else-if="error" class="drawing-state" role="alert"><el-icon><Warning /></el-icon><span>{{ error }}</span><el-button plain size="small" @click="renderAsset">重新读取</el-button></div>
    <svg v-else-if="imageUrl && frame" class="drawing-canvas" :viewBox="previewViewBox" role="img" :aria-label="`${asset.original_name}，${width} × ${height} 像素`">
      <defs><marker :id="markerId" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M10 0 0 5 10 10" fill="none" stroke="currentColor" stroke-width="1.4" /></marker></defs>
      <g class="extension-lines" aria-hidden="true"><path :d="`M${frame.x} ${frame.y - 32}V${frame.y + frame.height + 5} M${frame.x + frame.width} ${frame.y - 32}V${frame.y + frame.height + 5}`"/><path :d="`M${frame.x + frame.width + 4} ${frame.y}h37 M${frame.x + frame.width + 4} ${frame.y + frame.height}h37`"/></g>
      <g class="dimension-lines" :marker-start="`url(#${markerId})`" :marker-end="`url(#${markerId})`" aria-hidden="true"><path :d="`M${frame.x + 3} ${frame.y - 23}H${frame.x + frame.width - 3}`"/><path :d="`M${frame.x + frame.width + 31} ${frame.y + 3}V${frame.y + frame.height - 3}`"/></g>
      <g class="dimension-text" aria-hidden="true"><text :x="frame.x + frame.width / 2" :y="frame.y - 35" text-anchor="middle">{{ width }} px</text><text :transform="`translate(${frame.x + frame.width + 49}, ${frame.y + frame.height / 2}) rotate(-90)`" text-anchor="middle">{{ height }} px</text></g>
      <image :href="imageUrl" :x="frame.x" :y="frame.y" :width="frame.width" :height="frame.height" preserveAspectRatio="xMidYMid meet" />
    </svg>
    <div v-if="!loading && !error" class="drawing-caption"><span>{{ asset.asset_type === 'mask' ? '轮廓与内孔' : '纹理与透明通道' }}</span><span class="dimension-value">{{ width }} × {{ height }} px</span></div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, useId, watch } from 'vue'
import { Loading, Warning } from '@element-plus/icons-vue'
import { drawingFrame, maskDrawingPixels, storagePreviewUrl } from '../utils/maskPreview.mjs'

const props = defineProps({ asset: { type: Object, required: true }, fitPreview: { type: Boolean, default: false } })
const emit = defineEmits(['dimensions'])
const markerId = `drawing-dimension-${useId().replaceAll(':', '')}`
const loading = ref(false); const error = ref(''); const imageUrl = ref('')
const width = ref(0); const height = ref(0)
const frame = computed(() => drawingFrame(width.value, height.value))
// Fit the display frame to the part while keeping dimension labels in view.
// This changes only the preview, never the stored image or its pixel dimensions.
const previewViewBox = computed(() => {
  const area = frame.value
  return props.fitPreview && area ? `${area.x - 16} ${area.y - 58} ${area.width + 95} ${area.height + 78}` : '0 0 800 330'
})
let version = 0
let currentImage = null

function cancelImage() {
  if (!currentImage) return
  currentImage.onload = null; currentImage.onerror = null; currentImage.src = ''; currentImage = null
}
function renderAsset() {
  const request = ++version
  cancelImage()
  const asset = props.asset
  const url = storagePreviewUrl(asset.meta?.url, window.location.origin)
  loading.value = true; error.value = ''; imageUrl.value = ''; width.value = 0; height.value = 0
  emit('dimensions', null)
  if (!url) { error.value = '素材预览路径不可用'; loading.value = false; return }
  const image = new Image()
  currentImage = image
  image.onload = () => {
    if (request !== version) return
    try {
      const scale = Math.min(1, 1400 / image.naturalWidth, 800 / image.naturalHeight)
      const canvas = document.createElement('canvas')
      canvas.width = Math.max(1, Math.round(image.naturalWidth * scale)); canvas.height = Math.max(1, Math.round(image.naturalHeight * scale))
      const context = canvas.getContext('2d', { willReadFrequently: asset.asset_type === 'mask' })
      if (!context) throw new Error('Canvas is unavailable')
      context.drawImage(image, 0, 0, canvas.width, canvas.height)
      if (asset.asset_type === 'mask') {
        const pixels = context.getImageData(0, 0, canvas.width, canvas.height)
        pixels.data.set(maskDrawingPixels(pixels.data, canvas.width, canvas.height))
        if (!pixels.data.some((value, index) => index % 4 === 3 && value > 0)) throw new Error('Empty mask')
        context.putImageData(pixels, 0, 0)
      }
      imageUrl.value = canvas.toDataURL('image/png')
      width.value = image.naturalWidth; height.value = image.naturalHeight
      emit('dimensions', { id: asset.id, width: width.value, height: height.value })
    } catch { error.value = '无法读取图片预览，请进入项目检查素材' }
    finally { if (request === version) loading.value = false }
  }
  image.onerror = () => { if (request === version) { loading.value = false; error.value = '图片加载失败，请重试或进入项目检查素材' } }
  image.src = url
}
watch(() => [props.asset.id, props.asset.meta?.url, props.asset.asset_type], renderAsset, { immediate: true })
onBeforeUnmount(() => { ++version; cancelImage() })
</script>

<style scoped>
.drawing-view{position:relative;min-height:290px;display:flex;flex-direction:column;justify-content:center}.drawing-canvas{display:block;width:100%;max-height:360px;min-height:180px;color:#9a602f;animation:drawing-arrive 200ms ease-out}.extension-lines{fill:none;stroke:#c8c0af;stroke-width:1}.dimension-lines{fill:none;stroke:#a85b21;stroke-width:1}.dimension-text{fill:#87542a;font:18px var(--studio-font)}.drawing-caption{display:flex;justify-content:space-between;gap:16px;padding:0 20px 15px;color:#626b5e;font-size:16px;line-height:1.6}.dimension-value{font-family:var(--studio-font);white-space:nowrap}.drawing-state{min-height:270px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:14px;padding:28px;text-align:center;color:#66705f;font-size:18px;line-height:1.6}.drawing-state .el-icon{font-size:30px}.loading-icon{animation:drawing-turn 1s linear infinite}@keyframes drawing-arrive{from{opacity:.35;transform:translateY(3px)}to{opacity:1;transform:translateY(0)}}@keyframes drawing-turn{to{transform:rotate(360deg)}}@media(max-width:620px){.dimension-text{display:none}.drawing-view{min-height:230px}.drawing-canvas{min-height:150px}.drawing-caption{padding-inline:12px;flex-wrap:wrap}.drawing-state{min-height:230px}}@media(prefers-reduced-motion:reduce){.drawing-canvas,.loading-icon{animation:none}}
</style>
