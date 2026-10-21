<template>
  <section class="asset-review">
    <div class="review-header">
      <div><h3>{{ title }}</h3><div class="hint">{{ description }}</div><div class="hint selection-count">已选 {{ selectedAssets.length }} / {{ assets.length }} 个</div></div>
      <div class="review-actions">
        <el-button size="small" :disabled="deleting" @click="$emit('select-all')">全选</el-button>
        <el-button size="small" :disabled="deleting" @click="$emit('clear')">清空</el-button>
        <el-button v-if="deletable" size="small" type="danger" plain :icon="Delete" :disabled="!selectedAssets.length || deleting" @click="$emit('delete', selectedAssets.map(asset => asset.id))">删除已选（{{ selectedAssets.length }}）</el-button>
      </div>
    </div>
    <el-empty v-if="!assets.length" description="暂无可选择的文件" />
    <div v-else class="asset-grid">
      <label v-for="asset in assets" :key="asset.id" class="asset-tile" :class="{ selected: selectedIds.includes(asset.id) }">
        <div class="asset-tile-top"><el-checkbox :model-value="selectedIds.includes(asset.id)" :disabled="deleting" :aria-label="`选择 ${asset.original_name}`" @change="checked => $emit('toggle', { id: asset.id, checked })" /><span>{{ imageSize(asset) }}</span></div>
        <img v-if="asset.meta?.url" class="asset-preview" :class="{ checkerboard }" :src="asset.meta.url" :alt="asset.original_name" />
        <div class="asset-name" :title="asset.original_name">{{ asset.original_name }}</div>
        <div v-if="deletable" class="asset-delete"><el-button type="danger" link size="small" :icon="Delete" :disabled="deleting" :aria-label="`删除 ${asset.original_name}`" @click.stop.prevent="$emit('delete', [asset.id])">删除</el-button></div>
      </label>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Delete } from '@element-plus/icons-vue'
const props = defineProps({ title: String, description: String, assets: { type: Array, default: () => [] }, selectedIds: { type: Array, default: () => [] }, checkerboard: Boolean, deletable: Boolean, deleting: Boolean })
defineEmits(['toggle', 'select-all', 'clear', 'delete'])
const selectedAssets = computed(() => { const selected = new Set(props.selectedIds); return props.assets.filter(asset => selected.has(asset.id)) })
function imageSize(asset) { return asset?.meta?.width && asset?.meta?.height ? `${asset.meta.width} x ${asset.meta.height}` : '-' }
</script>

<style scoped>
.asset-review { margin-top: 24px; }
.review-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
.review-header > div:first-child { min-width: 0; }
.review-header h3 { margin: 0 0 6px; color: var(--studio-text); font:600 26px/1.4 var(--studio-font); }
.hint { color: var(--studio-muted); font-size:16px; line-height: 1.7; }
.selection-count { margin-top: 6px; color: var(--studio-primary); font-family:var(--studio-font); }
.review-actions { display: flex; gap: 8px; flex-shrink: 0; flex-wrap: wrap; justify-content: flex-end; max-width: 100%; }
.asset-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); gap: 14px; max-height: 560px; overflow: auto; padding: 3px; scrollbar-gutter: stable; }
.asset-tile { min-width: 0; border: 1px solid var(--studio-border); border-radius: 4px; background: var(--studio-surface); padding: 10px; cursor: pointer; transition: border-color 140ms ease, background-color 140ms ease; }
.asset-tile:hover { border-color: #b89572; }
.asset-tile:focus-within { outline: 2px solid var(--studio-primary); outline-offset: 1px; }
.asset-tile.selected { border-color: var(--studio-primary); background: var(--studio-primary-soft); }
.asset-tile-top { display: flex; align-items: center; justify-content: space-between; gap: 6px; color: var(--studio-muted); font:16px/1.6 var(--studio-font); margin-bottom: 8px; flex-wrap: wrap; }
.asset-tile-top :deep(.el-checkbox) { height: 24px; }
.asset-preview { display: block; width: 100%; aspect-ratio: 1; object-fit: contain; border: 1px solid #e9e5da; border-radius: 2px; background: #fff; }
.checkerboard { background: repeating-conic-gradient(#e2e1da 0% 25%, #fff 0% 50%) 50% / 16px 16px; }
.asset-name { margin-top: 9px; color: #475044; font-size:16px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.asset-delete { display: flex; justify-content: flex-end; margin-top: 5px; }
@media (max-width: 700px) { .review-header { flex-direction: column; } .review-actions { justify-content: flex-start; } .asset-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; } }
@media (max-width: 360px) { .asset-grid { grid-template-columns: minmax(0, 1fr); } }
@media (prefers-reduced-motion: reduce) { .asset-tile { transition: none; } }
</style>
