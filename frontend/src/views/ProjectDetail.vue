<template>
  <div class="page">
    <div class="toolbar">
      <div>
        <h2>{{ project?.name || '项目工作台' }}</h2>
        <div class="muted">{{ project?.description || '管理素材，并从任意步骤开始零件数据生成。' }}</div>
      </div>
      <div class="toolbar-actions">
        <el-button :icon="Picture" @click="$router.push(`/projects/${projectId}/gallery`)">浏览生成结果</el-button>
        <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
      </div>
    </div>

    <div class="asset-summary section">
      <div class="summary-item"><span>第一步输入</span><strong>{{ inputAssets.length }}</strong></div>
      <div class="summary-item"><span>Mask</span><strong>{{ maskAssets.length }}</strong></div>
      <div class="summary-item"><span>透明零件</span><strong>{{ partAssets.length }}</strong></div>
      <div class="summary-item"><span>数据集</span><strong>{{ datasetAssets.length }}</strong></div>
    </div>

    <section class="section">
      <div class="section-heading"><div><h3>素材上传</h3><div class="muted">背景、纹理与输入文件会保存在当前项目内。</div></div></div>
      <div class="upload-grid">
        <el-card shadow="never" class="work-card">
          <template #header>输入文件</template>
          <el-radio-group v-model="sourceUploadType" class="source-type-selector">
            <el-radio-button label="input">第一步：GEN / 白线图</el-radio-button>
            <el-radio-button label="mask">第二步：已有 Mask</el-radio-button>
          </el-radio-group>
          <AssetDropzone
            :accept="sourceUploadType === 'input' ? '.gen,image/*' : 'image/*'"
            :extensions="sourceUploadType === 'input' ? inputExtensions : imageExtensions"
            :loading="uploading"
            @files="(files, skipped) => uploadFiles(sourceUploadType, files, skipped)"
          />
          <div class="hint">{{ sourceUploadType === 'mask' ? '已上传的 Mask 会直接出现在第二步的可选 Mask 列表中。' : '用于第一步提取 Mask：GEN 文件或白色边缘图。' }}</div>
        </el-card>
        <el-card shadow="never" class="work-card">
          <template #header>背景图</template>
          <AssetDropzone accept="image/*" :extensions="imageExtensions" :loading="uploading" @files="(files, skipped) => uploadFiles('background', files, skipped)" />
          <div v-if="latestBackground" class="background-meta">
            <img v-if="latestBackground.meta?.url" :src="latestBackground.meta.url" alt="背景预览" />
            <div>
              <div class="asset-name">{{ latestBackground.original_name }}</div>
              <el-tag type="success">{{ imageSize(latestBackground) }}</el-tag>
            </div>
          </div>
          <div v-else class="hint">上传后将在这里显示背景预览及像素尺寸。</div>
        </el-card>
        <el-card shadow="never" class="work-card">
          <template #header>纹理图</template>
          <AssetDropzone accept="image/*" :extensions="imageExtensions" :loading="uploading" @files="(files, skipped) => uploadFiles('texture', files, skipped)" />
          <div v-if="latestTexture" class="background-meta">
            <img v-if="latestTexture.meta?.url" :src="latestTexture.meta.url" alt="纹理预览" />
            <div>
              <div class="asset-name">{{ latestTexture.original_name }}</div>
              <el-tag type="success">{{ imageSize(latestTexture) }}</el-tag>
            </div>
          </div>
          <div v-else class="hint">可拖入一张或整个纹理素材文件夹。</div>
        </el-card>
      </div>
    </section>

    <section class="section">
      <div class="section-heading">
        <div><h3>生成流程</h3><div class="muted">可从 DXF 预处理、第一步提取轮廓，或从已有 Mask、透明零件继续。</div></div>
      </div>
      <div class="workflow-entry-grid">
        <el-card v-for="item in steps" :key="item.key" shadow="never" class="step-entry">
          <div class="step-number">{{ item.step }}</div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
          <el-button type="primary" @click="goWorkflow(item)">{{ item.action }}</el-button>
        </el-card>
      </div>
    </section>

  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Picture, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getProject, listAssets, uploadAsset } from '../api/client'
import AssetDropzone from '../components/AssetDropzone.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id
const project = ref(null)
const assets = ref([])
const uploading = ref(false)
const sourceUploadType = ref('input')
const imageExtensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff']
const inputExtensions = ['.gen', ...imageExtensions]
const steps = [
  { key: 'dxf', step: '预留', title: 'DXF 预处理', description: '保存 DXF 文件，待后续接入 DXF 转边缘图算法。', action: '打开 DXF 窗格', path: 'dxf' },
  { key: 'step-1', step: '1', title: '提取 Mask', description: '从 GEN 文件或白色边缘图提取可用轮廓。', action: '进入第一步', path: 'step/1' },
  { key: 'step-2', step: '2', title: '生成透明零件', description: '选取已有 Mask，以纹理生成 RGBA 零件。', action: '进入第二步', path: 'step/2' },
  { key: 'step-3', step: '3', title: '合成数据集与标签', description: '选取零件与背景，生成 YOLO 或 COCO 数据。', action: '进入第三步', path: 'step/3' }
]
const inputAssets = computed(() => assets.value.filter(item => item.asset_type === 'input'))
const maskAssets = computed(() => assets.value.filter(item => item.asset_type === 'mask'))
const partAssets = computed(() => assets.value.filter(item => item.asset_type === 'part'))
const datasetAssets = computed(() => assets.value.filter(item => item.asset_type === 'dataset'))
const latestBackground = computed(() => assets.value.find(item => item.asset_type === 'background'))
const latestTexture = computed(() => assets.value.find(item => item.asset_type === 'texture'))

async function loadAll() {
  project.value = await getProject(projectId)
  assets.value = await listAssets(projectId)
}
function goWorkflow(item) { router.push(`/projects/${projectId}/${item.path}`) }
async function uploadFiles(assetType, files, skipped = 0) {
  if (!files.length) {
    ElMessage.warning(skipped ? `已忽略 ${skipped} 个不支持的文件` : '没有找到可上传的文件')
    return
  }
  uploading.value = true
  try {
    let nextIndex = 0
    let succeeded = 0
    let failed = 0
    const worker = async () => {
      while (nextIndex < files.length) {
        const file = files[nextIndex++]
        try { await uploadAsset(projectId, assetType, file); succeeded += 1 }
        catch { failed += 1 }
      }
    }
    await Promise.all(Array.from({ length: Math.min(4, files.length) }, worker))
    await loadAll()
    if (succeeded) ElMessage.success(`已上传 ${succeeded} 个文件${skipped ? `，忽略 ${skipped} 个不支持的文件` : ''}`)
    if (failed) ElMessage.error(`${failed} 个文件上传失败，请重试`)
  } finally { uploading.value = false }
}
function imageSize(asset) { return asset?.meta?.width && asset?.meta?.height ? `${asset.meta.width} x ${asset.meta.height} px` : '-' }
onMounted(loadAll)
</script>

<style scoped>
.asset-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); padding: 0 20px; border-block: 1px solid var(--studio-border); }
.summary-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-width: 0; min-height: 76px; padding: 12px 24px; border-right: 1px solid var(--studio-border); }
.summary-item:first-child { padding-left: 0; }
.summary-item:last-child { border-right: 0; padding-right: 0; }
.summary-item span, .hint { color: var(--studio-muted); font-size: 13px; }
.summary-item strong { font: 26px/1.4 var(--studio-mono); }
.section-heading { display: flex; justify-content: space-between; align-items: end; gap: 16px; margin: 30px 0 14px; }
.section-heading h3 { margin: 0 0 5px; font: 600 23px/1.4 var(--studio-serif); }
.upload-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
.work-card { min-width: 0; }
.source-type-selector { display: flex; margin-bottom: 14px; }
.source-type-selector :deep(.el-radio-button) { flex: 1; min-width: 0; }
.source-type-selector :deep(.el-radio-button__inner) { width: 100%; padding: 8px; font-size: 13px; }
.background-meta { display: flex; gap: 12px; align-items: center; margin-top: 16px; }
.background-meta > div { min-width: 0; }
.background-meta img { width: 72px; height: 52px; object-fit: cover; border: 1px solid var(--studio-border); }
.asset-name { overflow-wrap: anywhere; margin-bottom: 6px; color: var(--studio-text); font-size: 13px; }
.hint { margin-top: 12px; line-height: 1.7; }
.workflow-entry-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; }
.step-entry { position: relative; min-width: 0; }
.step-entry :deep(.el-card__body) { display: flex; flex-direction: column; height: 100%; }
.step-number { margin-bottom: 18px; color: var(--studio-primary); font: 15px/1.5 var(--studio-mono); }
.step-entry h3 { margin: 0 0 8px; font: 600 21px/1.4 var(--studio-serif); }
.step-entry p { flex: 1; margin: 0 0 20px; color: var(--studio-muted); font-size: 14px; line-height: 1.7; }
.step-entry :deep(.el-button) { width: 100%; }
@media (max-width: 1120px) { .upload-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .workflow-entry-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 700px) {
  .asset-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); padding: 0; }
  .summary-item { padding: 12px; min-height: 64px; }
  .summary-item:first-child { padding-left: 12px; }
  .summary-item:nth-child(2) { border-right: 0; }
  .summary-item:nth-child(-n+2) { border-bottom: 1px solid var(--studio-border); }
  .summary-item:last-child { padding-right: 12px; }
  .upload-grid { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 430px) { .workflow-entry-grid { grid-template-columns: minmax(0, 1fr); } }
</style>
