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
.toolbar-actions{display:flex;gap:10px}.asset-summary,.workflow-entry-grid,.upload-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}.summary-item{min-height:72px;padding:14px 16px;border:1px solid #e6eaf2;border-radius:8px;background:#fff;display:flex;align-items:center;justify-content:space-between}.summary-item span,.muted,.hint{color:#6b7280}.summary-item strong{font-size:26px}.section-heading{display:flex;justify-content:space-between;align-items:end;margin-bottom:12px}.section-heading h3,.step-entry h3{margin:0 0 6px}.step-entry{position:relative;min-height:178px}.step-entry p{min-height:42px;color:#606266;line-height:1.6}.step-number{font-size:13px;color:#409eff;font-weight:700;margin-bottom:12px}.source-type-selector{display:flex;margin-bottom:14px}.source-type-selector :deep(.el-radio-button){flex:1}.source-type-selector :deep(.el-radio-button__inner){width:100%}.background-meta{display:flex;gap:10px;align-items:center;margin-top:14px}.background-meta img{width:72px;height:52px;object-fit:cover;border-radius:4px;border:1px solid #e5e7eb}.asset-name{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-bottom:6px}.hint{margin-top:12px;font-size:12px}.work-card{border-radius:8px}
</style>
