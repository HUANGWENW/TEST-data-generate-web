<template>
  <div class="page material-workbench">
    <header class="toolbar workbench-header">
      <div><div class="eyebrow">素材管理 <span>项目 · {{ String(projectId).slice(0, 8) }}</span></div><h2>{{ project?.name || '项目素材' }}</h2><p class="project-description">{{ project?.description || '查看原始尺寸与素材细节，继续下一步生成。' }}</p></div>
      <div class="toolbar-actions">
        <el-button :icon="Refresh" :loading="loading" :disabled="uploading" @click="loadAll()">刷新</el-button>
        <el-button :icon="Picture" @click="router.push('/projects/' + projectId + '/gallery')">生成结果<span v-if="datasetCount"> · {{ datasetCount }}</span></el-button>
        <el-button :type="assets.length ? '' : 'primary'" :icon="Upload" :disabled="loading || uploading" @click="openUpload">上传素材</el-button>
      </div>
    </header>
    <el-alert v-if="loadError" class="load-error" type="error" :closable="false" show-icon :title="loadError" />
    <Teleport to="#project-subnavigation"><nav class="material-categories" aria-label="素材分类"><button v-for="item in categories" :key="item.value" type="button" :class="{ active: category === item.value }" :aria-pressed="category === item.value" @click="category = item.value; query = ''">{{ item.label }}<span>{{ counts[item.value] }}</span></button></nav></Teleport>
    <div class="material-layout" :aria-busy="loading">
      <section class="material-library" aria-labelledby="library-heading">
        <div class="library-header">
          <h3 id="library-heading">{{ currentCategory.label }} <span>{{ filteredAssets.length }} 项</span></h3>
          <el-input v-model="query" :prefix-icon="Search" clearable placeholder="搜索文件名" aria-label="搜索素材文件名" />
          <div class="list-options"><span>{{ query ? '搜索结果' : '点击素材查看预览' }}</span><select v-model="sort" aria-label="素材排序"><option value="newest">最新在前</option><option value="oldest">最早在前</option><option value="name">按文件名</option></select></div>
        </div>
        <div v-if="loading && !assets.length" class="list-empty" role="status">正在读取素材…</div>
        <ul v-else-if="filteredAssets.length" class="material-list" aria-label="素材列表">
          <li v-for="asset in filteredAssets" :key="asset.id"><button class="material-row" type="button" :class="{ selected: selectedId === asset.id }" :aria-pressed="selectedId === asset.id" @click="selectedId = asset.id">
            <span class="asset-thumbnail" :class="{ 'mask-thumbnail': category === 'mask', 'transparent-thumbnail': category === 'part' }" aria-hidden="true"><img v-if="imageUrl(asset) && !thumbnailErrors[asset.id]" :src="imageUrl(asset)" alt="" loading="lazy" @error="thumbnailErrors[asset.id] = true" /><span v-else class="file-extension">{{ extension(asset) }}</span></span>
            <span class="asset-row-info"><strong>{{ asset.original_name }}</strong><span>{{ imageSize(asset) }}</span></span><span class="row-indicator" aria-hidden="true">›</span>
          </button></li>
        </ul>
        <div v-else class="list-empty"><span>{{ query ? '没有匹配的素材' : '还没有' + currentCategory.label }}</span><el-button v-if="query" plain @click="query = ''">清除搜索</el-button><p v-else>{{ currentCategory.emptyHint }}</p></div>
      </section>
      <section class="material-preview" aria-labelledby="material-preview-heading">
        <template v-if="selectedAsset">
          <header class="preview-header"><div class="preview-heading"><span class="eyebrow">{{ currentCategory.label }}预览</span><h3 id="material-preview-heading">{{ selectedAsset.original_name }}</h3></div><el-button type="primary" class="next-step-action" :icon="Right" @click="goNext">{{ currentCategory.action }}</el-button></header>
          <div class="preview-surface" :class="{ 'part-surface': category === 'part' }">
            <ProjectDrawing v-if="category === 'mask' || category === 'part'" :key="selectedAsset.id" :asset="selectedAsset" fit-preview @dimensions="recordDimensions" />
            <div v-else-if="imageUrl(selectedAsset)" class="image-stage">
              <div v-if="previewError" class="preview-message" role="alert"><el-icon><Warning /></el-icon><p>浏览器无法预览此图片，可继续前往生成步骤。</p><el-button plain @click="previewError = false; previewAttempt++">重新读取</el-button></div>
              <template v-else><img :key="selectedAsset.id + '-' + previewAttempt" :src="imageUrl(selectedAsset)" :alt="selectedAsset.original_name" @load="recordImageDimensions" @error="previewError = true" /><span class="preview-note">等比预览 · 原始文件保持不变</span></template>
            </div>
            <div v-else class="preview-message"><el-icon><Document /></el-icon><strong>{{ extension(selectedAsset) }} 文件</strong><p>在第一步提取轮廓后，即可查看 Mask 预览。</p></div>
          </div>
          <dl class="asset-details"><div><dt>原始像素</dt><dd>{{ imageSize(selectedAsset) }}</dd></div><div><dt>文件格式</dt><dd>{{ extension(selectedAsset) }}</dd></div><div><dt>添加时间</dt><dd>{{ formatDate(selectedAsset.created_at) }}</dd></div></dl>
          <p class="next-step-hint">{{ currentCategory.nextHint }}</p>
        </template>
        <div v-else class="preview-empty"><el-icon><Picture /></el-icon><h3 id="material-preview-heading">{{ query ? '换个文件名试试' : '添加' + currentCategory.label + '，开始准备素材' }}</h3><p>{{ query ? '可清除搜索，或切换上方的素材分类。' : currentCategory.emptyHint }}</p><el-button v-if="query" plain @click="query = ''">清除搜索</el-button><el-button v-else-if="category === 'part'" type="primary" :icon="Right" @click="router.push('/projects/' + projectId + '/step/2')">前往纹理填充</el-button><el-button v-else-if="assets.length" type="primary" :icon="Upload" :disabled="loading || uploading" @click="openUpload">上传{{ currentCategory.label }}</el-button></div>
      </section>
    </div>
    <el-dialog v-model="uploadDialog" title="上传项目素材" width="620px" :close-on-click-modal="!uploading" :close-on-press-escape="!uploading" :show-close="!uploading" :before-close="closeUpload">
      <div class="upload-type-field"><label for="material-upload-type">素材类型</label><select id="material-upload-type" v-model="uploadType" :disabled="uploading"><option value="input">输入文件 · GEN / 边缘图</option><option value="mask">已有 Mask</option><option value="texture">纹理图</option><option value="background">背景图</option></select></div>
      <p class="upload-hint">{{ uploadHint }}</p>
      <AssetDropzone :accept="uploadType === 'input' ? '.gen,image/*' : 'image/*'" :extensions="uploadType === 'input' ? inputExtensions : imageExtensions" :loading="uploading" @files="(files, skipped) => uploadFiles(uploadType, files, skipped)" />
      <p v-if="uploading" class="upload-progress" role="status">已处理 {{ uploadProgress.done }} / {{ uploadProgress.total }} 个文件，请保持页面打开。</p>
      <template #footer><el-button :disabled="uploading" @click="uploadDialog = false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document, Picture, Refresh, Right, Search, Upload, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getProject, listAssets, uploadAsset } from '../api/client'
import AssetDropzone from '../components/AssetDropzone.vue'
import ProjectDrawing from '../components/ProjectDrawing.vue'
import { storagePreviewUrl } from '../utils/maskPreview.mjs'

const route = useRoute(), router = useRouter()
const projectId = computed(() => route.params.id)
const project = ref(null), assets = ref([]), loading = ref(false), loadError = ref('')
const category = ref('input'), query = ref(''), sort = ref('newest'), selectedId = ref('')
const dimensions = ref({}), thumbnailErrors = ref({}), previewError = ref(false), previewAttempt = ref(0)
const uploadDialog = ref(false), uploadType = ref('input'), uploading = ref(false)
const uploadProgress = ref({ done: 0, total: 0 })
const imageExtensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff']
const inputExtensions = ['.gen', ...imageExtensions]
const categories = [
  { value: 'input', label: '输入文件', path: 'step/1', action: '前往提取 Mask', emptyHint: '上传 GEN 文件或边缘图，用于第一步提取轮廓。', nextHint: '前往第一步，选择输入文件并提取 Mask。' },
  { value: 'mask', label: 'Mask', path: 'step/2', action: '前往纹理填充', emptyHint: '可上传已有 Mask，或在第一步提取轮廓。', nextHint: '前往第二步，勾选所需 Mask 与纹理，生成透明零件。' },
  { value: 'texture', label: '纹理图', path: 'step/2', action: '前往纹理填充', emptyHint: '上传纹理图，用于第二步填充零件。', nextHint: '前往第二步，选择纹理与 Mask，并设置填充方式。' },
  { value: 'part', label: '透明零件', path: 'step/3', action: '前往合成数据', emptyHint: '在第二步使用 Mask 与纹理，生成透明零件。', nextHint: '前往第三步，勾选所需零件与背景，合成数据集。' },
  { value: 'background', label: '背景图', path: 'step/3', action: '前往合成数据', emptyHint: '上传背景图，用于第三步合成数据集。', nextHint: '前往第三步，选择背景与零件，设置合成参数。' }
]
const currentCategory = computed(() => categories.find(item => item.value === category.value))
const counts = computed(() => Object.fromEntries(categories.map(item => [item.value, assets.value.filter(asset => asset.asset_type === item.value).length])))
const datasetCount = computed(() => assets.value.filter(asset => asset.asset_type === 'dataset').length)
const filteredAssets = computed(() => {
  const search = query.value.trim().toLocaleLowerCase()
  return assets.value.filter(asset => asset.asset_type === category.value && (!search || asset.original_name?.toLocaleLowerCase().includes(search))).sort((a, b) => {
    if (sort.value === 'name') return (a.original_name || '').localeCompare(b.original_name || '', 'zh-CN', { numeric: true })
    const difference = (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0)
    return sort.value === 'oldest' ? -difference : difference
  })
})
const selectedAsset = computed(() => filteredAssets.value.find(asset => asset.id === selectedId.value) || null)
const uploadHint = computed(() => ({ input: '支持 GEN、PNG、JPG、BMP、TIF。图像应包含清晰的零件边缘。', mask: '支持 PNG、JPG、BMP、TIF。上传后可直接在第二步勾选使用。', background: '支持 PNG、JPG、BMP、TIF。将保存在当前项目的背景素材中。', texture: '支持 PNG、JPG、BMP、TIF。将保存在当前项目的纹理素材中。' }[uploadType.value]))
let loadVersion = 0
watch(filteredAssets, items => { if (!items.some(item => item.id === selectedId.value)) selectedId.value = items[0]?.id || '' }, { immediate: true })
watch(selectedId, () => { previewError.value = false; previewAttempt.value = 0 })
watch(projectId, () => {
  project.value = null; assets.value = []; selectedId.value = ''; category.value = 'input'; query.value = ''
  dimensions.value = {}; thumbnailErrors.value = {}; uploadDialog.value = false
  loadAll(true)
}, { immediate: true })
async function loadAll(chooseCategory = false) {
  const request = ++loadVersion, id = projectId.value
  loading.value = true; loadError.value = ''
  try {
    const [nextProject, nextAssets] = await Promise.all([getProject(id), listAssets(id)])
    if (request !== loadVersion) return false
    project.value = nextProject; assets.value = nextAssets
    if (chooseCategory && !nextAssets.some(asset => asset.asset_type === category.value)) category.value = categories.find(item => nextAssets.some(asset => asset.asset_type === item.value))?.value || 'input'
    return true
  } catch { if (request === loadVersion) loadError.value = '素材读取失败，请点击刷新重试。'; return false }
  finally { if (request === loadVersion) loading.value = false }
}
function goNext() { router.push('/projects/' + projectId.value + '/' + currentCategory.value.path) }
function openUpload() { uploadType.value = category.value === 'part' ? 'mask' : category.value; uploadDialog.value = true }
function closeUpload(done) { if (!uploading.value) done() }
function extension(asset) { return asset?.original_name?.split('.').pop()?.toUpperCase() || '文件' }
function imageUrl(asset) { return imageExtensions.some(suffix => asset?.original_name?.toLowerCase().endsWith(suffix)) ? storagePreviewUrl(asset.meta?.url, window.location.origin) : '' }
function imageSize(asset) {
  const size = dimensions.value[asset?.id] || asset?.meta
  return size?.width && size?.height ? size.width + ' × ' + size.height + ' px' : imageExtensions.some(suffix => asset?.original_name?.toLowerCase().endsWith(suffix)) ? '尺寸待预览' : '非图像文件'
}
function recordDimensions(value) { if (value && selectedAsset.value?.id === value.id) dimensions.value[value.id] = value }
function recordImageDimensions(event) { if (selectedAsset.value) dimensions.value[selectedAsset.value.id] = { width: event.target.naturalWidth, height: event.target.naturalHeight } }
function formatDate(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? '未记录' : date.toLocaleString('zh-CN', { hour12: false }) }
async function uploadFiles(assetType, files, skipped = 0) {
  if (uploading.value) return
  if (!files.length) { ElMessage.warning(skipped ? '已忽略 ' + skipped + ' 个不支持的文件' : '没有找到可上传的文件'); return }
  const id = projectId.value
  uploading.value = true; uploadProgress.value = { done: 0, total: files.length }
  let nextIndex = 0, succeeded = 0, failed = 0, firstUploaded = null
  try {
    const worker = async () => {
      while (nextIndex < files.length) {
        const file = files[nextIndex++]
        try { const asset = await uploadAsset(id, assetType, file); firstUploaded ||= asset; succeeded++ }
        catch { failed++ }
        finally { uploadProgress.value.done++ }
      }
    }
    await Promise.all(Array.from({ length: Math.min(4, files.length) }, worker))
    if (id !== projectId.value) return
    const refreshed = await loadAll()
    if (succeeded) {
      category.value = assetType; query.value = ''
      if (refreshed) selectedId.value = firstUploaded?.id || ''
      ElMessage.success('已上传 ' + succeeded + ' 个文件' + (skipped ? '，忽略 ' + skipped + ' 个不支持的文件' : ''))
    }
    if (failed) ElMessage.error(failed + ' 个文件上传失败，请重试')
    else if (refreshed) uploadDialog.value = false
  } finally { uploading.value = false }
}
</script>

<style scoped>
.workbench-header { align-items: center; margin-bottom: 24px; }
.eyebrow { color: var(--studio-primary); font-size: 16px; font-weight: 600; line-height: 1.6; }
.eyebrow > span { margin-left: 16px; color: var(--studio-muted); font-weight: 400; }
.project-description { margin: 0; color: var(--studio-muted); font-size: 18px; overflow-wrap: anywhere; }
.load-error { margin-bottom: 18px; }
.material-categories { display: flex; gap: 6px 12px; flex-wrap: wrap; margin: 0; animation: material-preview-enter 180ms ease-out; }
.material-categories button { display: flex; align-items: center; gap: 10px; min-height: 46px; padding: 8px 18px; border: 1px solid transparent; border-radius: 24px; background: transparent; color: #5f584e; cursor: pointer; font-size: 18px; transition: color 140ms ease, background-color 140ms ease, border-color 140ms ease; }
.material-categories button.active { color: #7a421d; background: #f0dfcb; border-color: #e4c6a6; font-weight: 700; }
.material-categories button:hover { color: #733f1d; }
.material-categories button > span { min-width: 25px; padding: 0 6px; color: var(--studio-muted); background: #eae6dc; font-size: 16px; border-radius: 3px; }
.material-categories button.active > span { color: #73370e; background: #e8c9a8; }
.material-layout { display: grid; grid-template-columns: 340px minmax(0, 1fr); align-items: start; gap: 24px; }
.material-library, .material-preview { min-width: 0; background: var(--studio-surface); border: 1px solid var(--studio-border); border-radius: 4px; }
.library-header { padding: 18px 18px 0; }
.library-header h3 { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin: 0 0 14px; font-size: 22px; font-weight: 600; }
.library-header h3 span, .list-options { color: var(--studio-muted); font-size: 16px; font-weight: 400; }
.list-options { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px 10px; margin: 10px 0; }
.list-options select { min-height: 44px; max-width: 100%; padding: 6px 24px 6px 8px; color: var(--studio-text); background: var(--studio-surface); border: 1px solid var(--studio-border); border-radius: 3px; cursor: pointer; font-size: 16px; }
.material-list { max-height: min(540px, 65vh); overflow-y: auto; overscroll-behavior: contain; list-style: none; margin: 0; padding: 0 8px 8px; scrollbar-gutter: stable; }
.material-row { display: flex; align-items: center; gap: 12px; width: 100%; min-height: 100px; padding: 12px 10px; text-align: left; color: var(--studio-text); border: 1px solid transparent; border-bottom-color: var(--el-border-color-light); background: transparent; cursor: pointer; border-radius: 3px; transition: background-color 140ms ease, border-color 140ms ease; }
.material-row:hover { background: #f5f1e7; }
.material-row.selected { border-color: #bf916b; background: #f5ece1; }
.material-row:focus-visible { outline-offset: -3px; }
.asset-thumbnail { display: flex; align-items: center; justify-content: center; flex-shrink: 0; width: 64px; height: 64px; background: #e9e5db; border: 1px solid var(--studio-border); border-radius: 2px; overflow: hidden; }
.asset-thumbnail img { display: block; width: 100%; height: 100%; object-fit: contain; }
.mask-thumbnail { background: #333b37; }
.transparent-thumbnail { background-color: #eeeae1; background-image: conic-gradient(#dcd8cf 25%, transparent 0 50%, #dcd8cf 0 75%, transparent 0); background-size: 16px 16px; }
.file-extension { padding: 3px; color: var(--studio-muted); font-size: 16px; }
.mask-thumbnail .file-extension { color: #fffdf8; }
.asset-row-info { display: flex; flex-direction: column; gap: 6px; min-width: 0; flex: 1; }
.asset-row-info strong { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; overflow-wrap: anywhere; font-size: 18px; font-weight: 500; line-height: 1.5; }
.asset-row-info > span { color: var(--studio-muted); font-size: 16px; overflow-wrap: anywhere; }
.row-indicator { color: var(--studio-primary); font-size: 26px; }
.list-empty { display: flex; flex-direction: column; align-items: flex-start; gap: 14px; padding: 28px 20px 36px; color: var(--studio-muted); font-size: 18px; }
.list-empty p { margin: 0; font-size: 16px; }
.preview-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 18px; padding: 20px 24px; border-bottom: 1px solid var(--studio-border); }
.preview-heading { min-width: 0; flex: 1 1 250px; }
.preview-heading h3 { margin: 6px 0 0; overflow-wrap: anywhere; font-size: 22px; font-weight: 600; line-height: 1.5; }
.next-step-action { min-height: 56px; font-size: 20px; white-space: normal; height: auto; }
.preview-surface { padding: 12px 24px; background: #f9f7f0; }
.preview-surface :deep(.drawing-view) { animation: material-preview-enter 180ms ease-out; }
.preview-surface :deep(.drawing-canvas) { max-height: 420px; }
.part-surface { background-color: #f6f3eb; background-image: conic-gradient(#eae6dc 25%, transparent 0 50%, #eae6dc 0 75%, transparent 0); background-size: 24px 24px; }
.image-stage { min-height: 340px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; animation: material-preview-enter 180ms ease-out; }
.image-stage > img { display: block; max-width: 100%; max-height: 400px; object-fit: contain; }
.preview-note { font-size: 16px; color: var(--studio-muted); }
.preview-message { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; min-height: 310px; padding: 24px; text-align: center; }
.preview-message > .el-icon, .preview-empty > .el-icon { color: #94785f; font-size: 40px; }
.preview-message p { margin: 0; color: var(--studio-muted); font-size: 18px; }
.asset-details { display: grid; grid-template-columns: 1.2fr .7fr 1.5fr; gap: 16px; margin: 0; padding: 20px 24px; border-top: 1px solid var(--studio-border); }
.asset-details > div { min-width: 0; }
.asset-details dt { margin-bottom: 6px; color: var(--studio-muted); font-size: 16px; }
.asset-details dd { margin: 0; font-size: 18px; overflow-wrap: anywhere; }
.next-step-hint { margin: 0; padding: 0 24px 20px; color: var(--studio-muted); font-size: 16px; }
.preview-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; min-height: 440px; padding: 36px; text-align: center; }
.preview-empty h3 { margin: 0; font-size: 26px; font-weight: 500; overflow-wrap: anywhere; }
.preview-empty p { margin: 0 0 6px; color: var(--studio-muted); font-size: 18px; }
.upload-type-field { display: flex; align-items: center; gap: 16px; }
.upload-type-field label { flex-shrink: 0; font-size: 18px; }
.upload-type-field select { flex: 1; min-width: 0; min-height: 48px; padding: 8px 12px; color: var(--studio-text); background: var(--studio-surface); border: 1px solid var(--studio-border); border-radius: 3px; font-size: 18px; }
.upload-hint, .upload-progress { font-size: 16px; color: var(--studio-muted); line-height: 1.7; }
@keyframes material-preview-enter { from { opacity: .5; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }
@media (min-width: 961px) and (max-width: 1240px) { .material-layout { grid-template-columns: 310px minmax(0, 1fr); gap: 20px; } .workbench-header { align-items: flex-start; } .workbench-header .toolbar-actions { justify-content: flex-end; max-width: 380px; } }
@media (max-width: 960px) { .material-layout { grid-template-columns: minmax(0, 1fr); gap: 20px; } .material-list { max-height: 300px; } .preview-header { padding: 20px; } .preview-surface { padding: 12px 16px; } .preview-empty { min-height: 320px; } }
@media (max-width: 700px) { .eyebrow > span { display: block; margin: 3px 0 0; } .workbench-header .toolbar-actions { gap: 8px; } .material-categories { gap: 6px; } .material-categories button { padding-inline: 12px; } .preview-heading { flex-basis: 100%; } .next-step-action { width: 100%; } .asset-details { grid-template-columns: minmax(0, 1fr); gap: 14px; padding: 20px; } .asset-details > div { display: grid; grid-template-columns: 90px minmax(0, 1fr); gap: 10px; align-items: baseline; } .asset-details dt { margin: 0; } .next-step-hint { padding-inline: 20px; } .image-stage { min-height: 240px; } .preview-message { min-height: 240px; padding: 12px; } .preview-empty { padding: 28px 20px; } }
@media (prefers-reduced-motion: reduce) { .material-categories button, .material-row { transition: none; } .preview-surface :deep(.drawing-view), .image-stage, .material-categories { animation: none; } }
</style>
