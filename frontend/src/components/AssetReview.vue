<template>
  <section class="asset-review">
    <div class="review-header"><div><h3>{{ title }}</h3><div class="hint">{{ description }}</div></div><div class="review-actions"><el-button size="small" @click="$emit('select-all')">全选</el-button><el-button size="small" @click="$emit('clear')">清空</el-button></div></div>
    <el-empty v-if="!assets.length" description="暂无可选择的文件" />
    <div v-else class="asset-grid">
      <label v-for="asset in assets" :key="asset.id" class="asset-tile" :class="{ selected: selectedIds.includes(asset.id) }">
        <div class="asset-tile-top"><el-checkbox :model-value="selectedIds.includes(asset.id)" @change="checked => $emit('toggle', { id: asset.id, checked })" /><span>{{ imageSize(asset) }}</span></div>
        <img v-if="asset.meta?.url" class="asset-preview" :class="{ checkerboard }" :src="asset.meta.url" :alt="asset.original_name" />
        <div class="asset-name" :title="asset.original_name">{{ asset.original_name }}</div>
      </label>
    </div>
  </section>
</template>

<script setup>
defineProps({ title: String, description: String, assets: { type: Array, default: () => [] }, selectedIds: { type: Array, default: () => [] }, checkerboard: Boolean })
defineEmits(['toggle', 'select-all', 'clear'])
function imageSize(asset) { return asset?.meta?.width && asset?.meta?.height ? `${asset.meta.width} x ${asset.meta.height}` : '-' }
</script>

<style scoped>
.asset-review{margin-top:20px}.review-header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:12px}.review-header h3{margin:0 0 6px;font-size:15px}.hint{color:#6b7280;font-size:12px;line-height:1.5}.review-actions{display:flex;gap:8px;flex-shrink:0}.asset-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:12px;max-height:520px;overflow:auto;padding:2px}.asset-tile{border:1px solid #e3e8f0;border-radius:8px;background:#fbfcff;padding:8px;cursor:pointer}.asset-tile:hover{border-color:#94bfff}.asset-tile.selected{border-color:#409eff;background:#f0f7ff}.asset-tile-top{display:flex;align-items:center;justify-content:space-between;gap:6px;color:#4b5563;font-size:12px;margin-bottom:6px}.asset-preview{width:100%;aspect-ratio:1;object-fit:contain;border-radius:5px;background:#fff}.checkerboard{background:linear-gradient(45deg,#e5e7eb 25%,transparent 25%),linear-gradient(-45deg,#e5e7eb 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#e5e7eb 75%),linear-gradient(-45deg,transparent 75%,#e5e7eb 75%);background-size:16px 16px;background-position:0 0,0 8px,8px -8px,-8px 0}.asset-name{margin-top:6px;color:#374151;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}@media (max-width:600px){.review-header{flex-direction:column}.asset-grid{grid-template-columns:repeat(auto-fill,minmax(124px,1fr))}}
</style>
