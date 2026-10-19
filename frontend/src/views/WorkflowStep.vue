<template>
  <div class="page">
    <div class="toolbar">
      <div>
        <el-button link :icon="ArrowLeft" @click="$router.push(`/projects/${projectId}`)">返回项目</el-button>
        <h2>{{ stepTitle }}</h2>
        <div class="muted">{{ project?.name || '项目' }} · {{ stepHint }}</div>
      </div>
      <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
    </div>

    <el-steps :active="currentStep - 1" finish-status="success" class="section workflow-steps">
      <el-step title="1. 提取 Mask" @click="goStep(1)" />
      <el-step title="2. 生成透明零件" @click="goStep(2)" />
      <el-step title="3. 合成数据集与标签" @click="goStep(3)" />
    </el-steps>

    <el-card v-if="currentStep === 1" class="task-page-card" shadow="never">
      <template #header><div class="card-title"><span>提取 Mask</span><el-tag type="info">中间产物</el-tag></div></template>
      <el-alert v-if="!inputAssets.length" title="请先在项目首页上传输入文件" type="warning" :closable="false" show-icon class="section-alert" />
      <el-form label-width="110px" class="task-form">
        <el-form-item label="输入文件"><el-select v-model="maskForm.asset_id" placeholder="选择输入文件" filterable><el-option v-for="item in inputAssets" :key="item.id" :label="item.original_name" :value="item.id" /></el-select></el-form-item>
        <el-form-item label="提取方式"><el-radio-group v-model="maskForm.mode"><el-radio-button label="extract_gen_masks">GEN 文件</el-radio-button><el-radio-button label="extract_edge_masks">边缘图</el-radio-button></el-radio-group></el-form-item>
        <template v-if="maskForm.mode === 'extract_gen_masks'">
          <el-form-item label="Mask 比例"><el-input-number v-model="maskForm.scale" :min="0.1" :max="30" :step="0.5" /></el-form-item>
          <el-form-item label="留白"><el-input-number v-model="maskForm.padding" :min="0" :max="200" /></el-form-item>
          <el-form-item label="最小宽高"><div class="inline-range"><el-input-number v-model="maskForm.min_width_mm" :min="0" /><span>和</span><el-input-number v-model="maskForm.min_height_mm" :min="0" /></div></el-form-item>
          <el-form-item label="面积/长宽比"><div class="inline-range"><el-input-number v-model="maskForm.min_area_mm2" :min="0" :step="100" /><span>和</span><el-input-number v-model="maskForm.max_aspect_ratio" :min="1" /></div></el-form-item>
        </template>
        <template v-else>
          <el-form-item label="边缘颜色"><el-select v-model="maskForm.edge_polarity"><el-option label="自动识别" value="auto" /><el-option label="白线 / 黑底" value="white" /><el-option label="黑线 / 白底" value="black" /></el-select></el-form-item>
          <el-form-item label="最小面积"><div class="field-with-note"><el-input-number v-model="maskForm.min_area" :min="1" :step="100" /><span class="hint">单位 px²；过滤小零件，内孔会保留。</span></div></el-form-item>
          <el-form-item label="断点修补核"><div class="field-with-note"><el-input-number v-model="maskForm.dilation_size" :min="1" :max="21" :step="2" :precision="0" /><span class="hint">1 表示不修补；较大值可连接小断点，也可能合并相邻轮廓。闭合轮廓按原图像素填充，内孔保持透明。</span></div></el-form-item>
        </template>
        <el-form-item><el-button type="primary" :icon="VideoPlay" @click="submitMaskTask">提交 Mask 提取</el-button></el-form-item>
      </el-form>
      <AssetReview title="Mask 验收" description="勾选轮廓完整、内孔正确的 Mask，作为第二步的输入。" :assets="maskAssets" :selected-ids="selectedMaskIds" @toggle="toggleMask" @select-all="selectAllMasks" @clear="clearSelectedMasks" />
      <div class="workflow-footer"><el-button type="primary" :icon="ArrowRight" icon-position="right" @click="nextFromMasks">进入第二步</el-button></div>
    </el-card>

    <el-card v-else-if="currentStep === 2" class="task-page-card" shadow="never">
      <template #header><div class="card-title"><span>Mask 生成透明零件</span><el-tag type="success">RGBA</el-tag></div></template>
      <el-alert v-if="!maskAssets.length" title="当前项目没有 Mask；可直接返回项目首页上传素材，或先执行第一步。" type="warning" :closable="false" show-icon class="section-alert" />
      <AssetReview title="选择输入 Mask" description="可从第二步开始。只会使用当前勾选的 Mask 生成透明零件。" :assets="maskAssets" :selected-ids="selectedMaskIds" @toggle="toggleMask" @select-all="selectAllMasks" @clear="clearSelectedMasks" />
      <el-divider />
      <el-form label-width="110px" class="task-form">
        <el-form-item label="纹理图"><el-select v-model="partForm.texture_asset_id" placeholder="选择纹理图" filterable><el-option v-for="item in textureAssets" :key="item.id" :label="item.original_name" :value="item.id" /></el-select></el-form-item>
        <el-form-item label="随机裁剪"><el-switch v-model="partForm.random_crop" /></el-form-item>
        <el-form-item label="输出最长边"><div class="field-with-note"><el-input-number v-model="partForm.max_side_pixels" :min="0" :step="500" :precision="0" /><span class="hint">0：保留输入 Mask 的原始尺寸和透明通道。正数：按此像素上限等比缩小，不放大。纹理不足时随机裁剪模式会平铺补足。</span></div></el-form-item>
        <el-form-item><el-button type="primary" :icon="VideoPlay" @click="submitPartTask">生成透明零件</el-button></el-form-item>
      </el-form>
      <AssetReview title="透明零件验收" description="生成完成后，在这里筛选适合参与合成的透明零件。" :assets="partAssets" :selected-ids="selectedPartIds" checkerboard @toggle="togglePart" @select-all="selectAllParts" @clear="clearSelectedParts" />
      <div class="workflow-footer"><el-button type="primary" :icon="ArrowRight" icon-position="right" @click="nextFromParts">进入第三步</el-button></div>
    </el-card>

    <section v-else class="dataset-workspace">
      <div class="dataset-hero">
        <div class="dataset-hero-icon"><el-icon><DataAnalysis /></el-icon></div>
        <div class="dataset-hero-copy">
          <div class="dataset-eyebrow">STEP 03 · DATASET COMPOSITION</div>
          <h3>合成数据集与标签</h3>
          <p>选择零件和背景，配置布局与标注规则，提交后在任务中心查看生成进度。</p>
        </div>
        <div class="dataset-hero-status">
          <el-tag effect="plain">{{ selectedPartIds.length }} 个零件</el-tag>
          <el-tag effect="plain" :type="selectedBackground ? 'success' : 'info'">{{ selectedBackground ? '背景已就绪' : '未选择背景' }}</el-tag>
          <el-tag effect="plain" type="warning">{{ labelFormatLabel }}</el-tag>
        </div>
      </div>

      <el-alert
        v-if="!partAssets.length || !backgroundAssets.length"
        title="生成所需素材尚未准备完整"
        description="至少需要一个透明零件和一张背景图。可返回项目工作台上传，也可以直接使用项目中的已有素材。"
        type="warning"
        :closable="false"
        show-icon
        class="dataset-alert"
      />

      <div class="dataset-assets-card">
        <div class="dataset-section-heading">
          <div>
            <span class="dataset-section-kicker">INPUT ASSETS</span>
            <h4>选择合成零件</h4>
          </div>
          <div class="dataset-section-summary">
            已选 <strong>{{ selectedPartIds.length }}</strong> / {{ partAssets.length }} 个
          </div>
        </div>
        <AssetReview
          title="零件素材"
          description="仅勾选的透明零件会参与本批次合成；棋盘格区域代表透明通道。"
          :assets="partAssets"
          :selected-ids="selectedPartIds"
          checkerboard
          @toggle="togglePart"
          @select-all="selectAllParts"
          @clear="clearSelectedParts"
        />
      </div>

      <div class="dataset-layout">
        <section class="dataset-settings-card">
          <div class="dataset-panel-heading">
            <div class="dataset-panel-icon"><el-icon><Setting /></el-icon></div>
            <div><h4>生成设置</h4><p>必要参数</p></div>
          </div>

          <el-form label-position="top" class="dataset-form">
            <el-form-item label="背景图" class="dataset-field-full">
              <el-select v-model="datasetForm.background_asset_id" placeholder="选择背景图" filterable>
                <el-option v-for="item in backgroundAssets" :key="item.id" :label="`${item.original_name} (${imageSize(item)})`" :value="item.id" />
              </el-select>
              <div v-if="selectedBackground" class="dataset-field-note"><el-icon><CircleCheckFilled /></el-icon>{{ imageSize(selectedBackground) }}</div>
            </el-form-item>

            <div class="dataset-form-grid">
              <el-form-item label="标签格式"><el-select v-model="datasetForm.label_format"><el-option label="YOLO HBB" value="yolo_hbb" /><el-option label="YOLO OBB" value="yolo_obb" /><el-option label="COCO Segmentation" value="coco" /></el-select></el-form-item>
              <el-form-item label="布局模式"><el-select v-model="datasetForm.layout_mode"><el-option label="随机放置" value="random" /><el-option label="紧凑放置" value="compact" /><el-option label="紧凑/宽松混合" value="mixed" /></el-select></el-form-item>
              <el-form-item label="生成数量"><el-input-number v-model="datasetForm.num_images" :min="1" :max="2000" controls-position="right" /></el-form-item>
              <el-form-item label="每张零件数"><div class="dataset-range"><el-input-number v-model="datasetForm.min_parts" :min="1" controls-position="right" /><span>—</span><el-input-number v-model="datasetForm.max_parts" :min="1" controls-position="right" /></div></el-form-item>
              <el-form-item label="旋转角度"><div class="dataset-range"><el-input-number v-model="datasetForm.angle_min" :min="0" :max="360" controls-position="right" /><span>—</span><el-input-number v-model="datasetForm.angle_max" :min="0" :max="360" controls-position="right" /></div></el-form-item>
              <el-form-item label="缩放比例"><div class="dataset-range"><el-input-number v-model="datasetForm.scale_min" :min="0.05" :max="10" :step="0.05" controls-position="right" /><span>—</span><el-input-number v-model="datasetForm.scale_max" :min="0.05" :max="10" :step="0.05" controls-position="right" /></div></el-form-item>
            </div>

            <div class="dataset-subsection-title"><span>可放置边距</span><small>单位：px</small></div>
            <div class="dataset-margin-grid">
              <label v-for="field in marginFields" :key="field.key" class="dataset-margin-field">
                <span>{{ field.label }}</span>
                <el-input-number v-model="datasetForm[field.key]" :min="0" controls-position="right" />
              </label>
            </div>

            <el-collapse class="dataset-advanced">
              <el-collapse-item name="output">
                <template #title><span class="dataset-collapse-title">高级输出设置 <small>JPEG {{ datasetForm.jpeg_quality }}</small></span></template>
                <el-form-item label="JPEG 质量"><div class="quality-control"><el-slider v-model="datasetForm.jpeg_quality" :min="60" :max="100" :step="1" show-input /><span class="hint">降低质量可减少文件体积并加快写入，95 可保持当前输出质量。</span></div></el-form-item>
              </el-collapse-item>
            </el-collapse>
          </el-form>

          <div class="dataset-preflight" :class="{ 'is-ready': datasetReady }">
            <div class="dataset-preflight-title">
              <el-icon><CircleCheckFilled v-if="datasetReady" /><WarningFilled v-else /></el-icon>
              <span>{{ datasetReady ? '生成前检查全部通过' : '生成前检查' }}</span>
            </div>
            <ul><li v-for="item in datasetPreflight" :key="item.label" :class="{ pass: item.pass }"><span>{{ item.pass ? '✓' : '!' }}</span>{{ item.label }}<small>{{ item.detail }}</small></li></ul>
          </div>

          <el-button class="dataset-submit" type="primary" size="large" :icon="VideoPlay" :disabled="!datasetReady" @click="submitDatasetTask">开始生成数据集</el-button>
        </section>

        <aside class="dataset-preview-card">
          <div class="dataset-panel-heading dataset-preview-heading">
            <div class="dataset-panel-icon is-cyan"><el-icon><PictureFilled /></el-icon></div>
            <div><h4>随机排布与标注预览</h4><p>真实背景 · 无碰撞放置 · 坐标归一化</p></div>
            <el-tag effect="dark" type="info">{{ layoutModeLabel }}</el-tag>
          </div>

          <div class="dataset-preview-frame" :style="placementCanvasStyle">
            <img v-if="placementPreviewUrl" :src="placementPreviewUrl" alt="所选背景图" />
            <div v-else class="dataset-preview-empty"><el-icon><PictureFilled /></el-icon><span>选择背景图后显示合成预览</span></div>
            <div v-if="selectedBackground" class="dataset-valid-area" :class="{ invalid: placementAreaInvalid }" :style="placementAreaStyle"><span>可放置区域 · {{ placementAreaSize }}</span></div>
            <template v-if="selectedBackground">
              <div v-for="(part, index) in previewParts" :key="part.id" class="dataset-preview-part" :style="previewPartStyle(index)">
                <img :src="part.meta?.url" :alt="part.original_name" />
                <span v-if="datasetForm.label_format !== 'coco'">0 {{ datasetForm.class_name }}</span>
              </div>
            </template>
          </div>

          <div class="dataset-preview-legend"><span><i class="legend-cyan"></i>有效标注</span><span><i class="legend-orange"></i>旋转边界</span><strong>{{ placementAreaSize }}</strong></div>

          <div class="dataset-flow">
            <div v-for="(item, index) in datasetFlow" :key="item.label" class="dataset-flow-node" :class="{ active: index === datasetFlow.length - 1 }"><span>{{ item.label }}</span><strong>{{ item.value }}</strong><i v-if="index < datasetFlow.length - 1">→</i></div>
          </div>

          <div class="dataset-contract">
            <div><span>标签输出示例</span><el-tag size="small" effect="plain">{{ labelFormatLabel }}</el-tag></div>
            <code>{{ labelContract }}</code>
          </div>

          <div class="dataset-run-summary">
            <div><span>生成规模</span><strong>{{ datasetForm.num_images }} 张</strong></div>
            <div><span>零件范围</span><strong>{{ datasetForm.min_parts }}–{{ datasetForm.max_parts }} 个/张</strong></div>
            <div><span>旋转范围</span><strong>{{ datasetForm.angle_min }}°–{{ datasetForm.angle_max }}°</strong></div>
          </div>
        </aside>
      </div>

      <div class="workflow-footer dataset-footer"><el-button @click="goStep(2)">返回第二步</el-button><el-button type="primary" plain @click="$router.push('/tasks')">查看任务中心</el-button></div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, CircleCheckFilled, DataAnalysis, PictureFilled, Refresh, Setting, VideoPlay, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createTask, getProject, listAssets } from '../api/client'
import AssetReview from '../components/AssetReview.vue'

const route = useRoute(); const router = useRouter(); const projectId = route.params.id
const project = ref(null); const assets = ref([]); const selectedMaskIds = ref([]); const selectedPartIds = ref([])
const maskTouched = ref(false); const partTouched = ref(false); let refreshTimer = null
const currentStep = computed(() => Math.min(3, Math.max(1, Number(route.params.step) || 1)))
const stepTitle = computed(() => ['提取 Mask', '生成透明零件', '合成数据集与标签'][currentStep.value - 1])
const stepHint = computed(() => ['提取并验收可用轮廓', '从已有 Mask 开始也可以', '从已有透明零件开始也可以'][currentStep.value - 1])
const inputAssets = computed(() => assets.value.filter(a => a.asset_type === 'input')); const maskAssets = computed(() => assets.value.filter(a => a.asset_type === 'mask')); const textureAssets = computed(() => assets.value.filter(a => a.asset_type === 'texture')); const partAssets = computed(() => assets.value.filter(a => a.asset_type === 'part')); const backgroundAssets = computed(() => assets.value.filter(a => a.asset_type === 'background'))
const selectedBackground = computed(() => backgroundAssets.value.find(a => a.id === datasetForm.background_asset_id))
const maskForm = reactive({ asset_id: '', mode: 'extract_edge_masks', dilation_size: 3, edge_polarity: 'auto', min_area: 5000, scale: 5, padding: 20, min_width_mm: 10, min_height_mm: 10, min_area_mm2: 100, max_aspect_ratio: 20 })
const partForm = reactive({ texture_asset_id: '', random_crop: true, max_side_pixels: 0 })
const datasetForm = reactive({ background_asset_id: '', label_format: 'yolo_hbb', layout_mode: 'random', num_images: 20, min_parts: 2, max_parts: 8, angle_min: 0, angle_max: 90, scale_min: 0.6, scale_max: 1, margin_top: 100, margin_bottom: 150, margin_left: 0, margin_right: 0, jpeg_quality: 95, class_id: 0, class_name: 'steel_part' })
const placementPreviewUrl = computed(() => selectedBackground.value?.meta?.url || '')
const backgroundWidth = computed(() => Math.max(1, Number(selectedBackground.value?.meta?.width) || 1000))
const backgroundHeight = computed(() => Math.max(1, Number(selectedBackground.value?.meta?.height) || 700))
const placementCanvasStyle = computed(() => ({ aspectRatio: `${backgroundWidth.value} / ${backgroundHeight.value}` }))
const placementAreaStyle = computed(() => ({
  top: `${Math.min(100, Math.max(0, datasetForm.margin_top / backgroundHeight.value * 100))}%`,
  right: `${Math.min(100, Math.max(0, datasetForm.margin_right / backgroundWidth.value * 100))}%`,
  bottom: `${Math.min(100, Math.max(0, datasetForm.margin_bottom / backgroundHeight.value * 100))}%`,
  left: `${Math.min(100, Math.max(0, datasetForm.margin_left / backgroundWidth.value * 100))}%`,
}))
const placementAreaSize = computed(() => {
  if (!selectedBackground.value) return '未选择背景图'
  const width = Math.max(0, backgroundWidth.value - datasetForm.margin_left - datasetForm.margin_right)
  const height = Math.max(0, backgroundHeight.value - datasetForm.margin_top - datasetForm.margin_bottom)
  return `${width} x ${height} px`
})
const marginFields = [
  { key: 'margin_top', label: '上' },
  { key: 'margin_bottom', label: '下' },
  { key: 'margin_left', label: '左' },
  { key: 'margin_right', label: '右' }
]
const placementAreaInvalid = computed(() => {
  if (!selectedBackground.value) return false
  return backgroundWidth.value - datasetForm.margin_left - datasetForm.margin_right <= 0
    || backgroundHeight.value - datasetForm.margin_top - datasetForm.margin_bottom <= 0
})
const selectedPartAssets = computed(() => {
  const selected = new Set(selectedPartIds.value)
  return partAssets.value.filter(item => selected.has(item.id))
})
const previewParts = computed(() => selectedPartAssets.value.slice(0, 5))
const previewLayouts = [
  { left: '12%', top: '27%', width: '18%', transform: 'rotate(-12deg)' },
  { left: '38%', top: '20%', width: '17%', transform: 'rotate(17deg)' },
  { left: '67%', top: '30%', width: '19%', transform: 'rotate(-6deg)' },
  { left: '26%', top: '58%', width: '17%', transform: 'rotate(9deg)' },
  { left: '57%', top: '60%', width: '18%', transform: 'rotate(-19deg)' }
]
const previewPartStyle = index => previewLayouts[index % previewLayouts.length]
const labelFormatLabel = computed(() => ({ yolo_hbb: 'YOLO HBB', yolo_obb: 'YOLO OBB', coco: 'COCO Segmentation' }[datasetForm.label_format] || datasetForm.label_format))
const layoutModeLabel = computed(() => ({ random: '随机放置', compact: '紧凑放置', mixed: '混合布局' }[datasetForm.layout_mode] || datasetForm.layout_mode))
const labelContract = computed(() => {
  if (datasetForm.label_format === 'yolo_obb') return '0 0.1824 0.2448 0.3152 0.2017 0.3421 0.3386 0.2079 0.3715'
  if (datasetForm.label_format === 'coco') return '{ "category_id": 0, "segmentation": [[x1, y1, x2, y2, ...]] }'
  return '0 0.2623 0.2866 0.1597 0.1421'
})
const datasetPreflight = computed(() => [
  { label: '背景图', pass: Boolean(selectedBackground.value), detail: selectedBackground.value ? imageSize(selectedBackground.value) : '请选择背景图' },
  { label: '透明零件', pass: selectedPartIds.value.length > 0, detail: selectedPartIds.value.length ? `${selectedPartIds.value.length} 个已选择` : '至少选择一个零件' },
  { label: '参数范围', pass: datasetForm.max_parts >= datasetForm.min_parts && datasetForm.angle_max >= datasetForm.angle_min && datasetForm.scale_max >= datasetForm.scale_min, detail: '数量、角度与缩放上下限' },
  { label: '可放置区域', pass: Boolean(selectedBackground.value) && !placementAreaInvalid.value, detail: placementAreaSize.value }
])
const datasetReady = computed(() => datasetPreflight.value.every(item => item.pass))
const datasetFlow = computed(() => [
  { label: '输入图', value: inputAssets.value.length || '—' },
  { label: 'Mask', value: maskAssets.value.length || '—' },
  { label: 'RGBA', value: selectedPartIds.value.length || '—' },
  { label: '合成图', value: datasetForm.num_images },
  { label: labelFormatLabel.value.replace('YOLO ', ''), value: datasetForm.num_images }
])
function syncSelections() { const masks = new Set(maskAssets.value.map(a => a.id)); const parts = new Set(partAssets.value.map(a => a.id)); selectedMaskIds.value = selectedMaskIds.value.filter(id => masks.has(id)); selectedPartIds.value = selectedPartIds.value.filter(id => parts.has(id)); if (!maskTouched.value && !selectedMaskIds.value.length) selectedMaskIds.value = [...masks]; if (!partTouched.value && !selectedPartIds.value.length) selectedPartIds.value = [...parts] }
async function loadAll() { project.value = await getProject(projectId); assets.value = await listAssets(projectId); syncSelections() }
function goStep(step) { router.push(`/projects/${projectId}/step/${step}`) }
function toggleMask({ id, checked }) { maskTouched.value = true; selectedMaskIds.value = checked ? [...new Set([...selectedMaskIds.value, id])] : selectedMaskIds.value.filter(v => v !== id) }
function selectAllMasks() { maskTouched.value = true; selectedMaskIds.value = maskAssets.value.map(a => a.id) } function clearSelectedMasks() { maskTouched.value = true; selectedMaskIds.value = [] }
function togglePart({ id, checked }) { partTouched.value = true; selectedPartIds.value = checked ? [...new Set([...selectedPartIds.value, id])] : selectedPartIds.value.filter(v => v !== id) }
function selectAllParts() { partTouched.value = true; selectedPartIds.value = partAssets.value.map(a => a.id) } function clearSelectedParts() { partTouched.value = true; selectedPartIds.value = [] }
async function submitMaskTask() {
  if (!maskForm.asset_id) return ElMessage.warning('请选择输入文件')
  if (maskForm.mode === 'extract_edge_masks' && (!Number.isInteger(maskForm.dilation_size) || maskForm.dilation_size % 2 === 0)) return ElMessage.warning('断点修补核必须是 1 到 21 之间的奇数')
  await createTask(projectId, maskForm.mode, { ...maskForm })
  maskTouched.value = false; selectedMaskIds.value = []
  ElMessage.success('Mask 提取任务已提交'); await loadAll()
}
async function submitPartTask() { if (!partForm.texture_asset_id) return ElMessage.warning('请选择纹理图'); if (!selectedMaskIds.value.length) return ElMessage.warning('请至少选择一个 Mask'); await createTask(projectId, 'masks_to_parts', { ...partForm, mask_asset_ids: selectedMaskIds.value }); partTouched.value = false; selectedPartIds.value = []; ElMessage.success('透明零件任务已提交'); await loadAll() }
async function submitDatasetTask() { const failedCheck = datasetPreflight.value.find(item => !item.pass); if (failedCheck) return ElMessage.warning(`${failedCheck.label}：${failedCheck.detail}`); await createTask(projectId, 'generate_dataset', { ...datasetForm, part_asset_ids: selectedPartIds.value }); ElMessage.success('数据集生成任务已提交'); router.push('/tasks') }
function nextFromMasks() { if (!selectedMaskIds.value.length) return ElMessage.warning('请先选择至少一个可用 Mask'); goStep(2) } function nextFromParts() { if (!selectedPartIds.value.length) return ElMessage.warning('请先选择至少一个透明零件'); goStep(3) } function imageSize(asset) { return asset?.meta?.width && asset?.meta?.height ? `${asset.meta.width} x ${asset.meta.height} px` : '-' }
watch(currentStep, loadAll); onMounted(() => { loadAll(); refreshTimer = window.setInterval(loadAll, 5000) }); onUnmounted(() => { if (refreshTimer) window.clearInterval(refreshTimer) })
</script>

<style scoped>
.workflow-steps {
  padding: 22px 28px;
  cursor: pointer;
  border: 1px solid #e1e7ef;
  border-radius: 12px;
  background: #fff;
}

.task-page-card { border-radius: 10px; }
.card-title { display: flex; align-items: center; justify-content: space-between; font-weight: 700; }
.section-alert { margin-bottom: 20px; }
.task-form { max-width: 980px; }
.field-with-note { display: flex; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.hint { max-width: 460px; color: #64748b; font-size: 12px; line-height: 1.55; }
.inline-range { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.workflow-footer { display: flex; justify-content: flex-end; gap: 10px; padding-top: 22px; margin-top: 22px; border-top: 1px solid #e8edf4; }

.dataset-workspace {
  --dataset-primary: #2563eb;
  --dataset-primary-soft: #eff6ff;
  --dataset-text: #172033;
  --dataset-muted: #64748b;
  --dataset-border: #dce3ec;
  color: var(--dataset-text);
}

.dataset-hero {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 92px;
  padding: 18px 22px;
  margin-bottom: 16px;
  overflow: hidden;
  border: 1px solid #dbe6f7;
  border-radius: 14px;
  background: linear-gradient(115deg, #fff 0%, #f7faff 65%, #edf5ff 100%);
  box-shadow: 0 8px 24px rgb(15 23 42 / 4%);
}

.dataset-hero-icon,
.dataset-panel-icon {
  display: grid;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 10px;
  color: var(--dataset-primary);
  background: var(--dataset-primary-soft);
  font-size: 20px;
}

.dataset-hero-copy { min-width: 0; }
.dataset-eyebrow,
.dataset-section-kicker { color: var(--dataset-primary); font-size: 10px; font-weight: 700; letter-spacing: .12em; }
.dataset-hero h3 { margin: 3px 0 4px; font-size: 21px; }
.dataset-hero p,
.dataset-panel-heading p { margin: 0; color: var(--dataset-muted); font-size: 12px; line-height: 1.5; }
.dataset-hero-status { display: flex; justify-content: flex-end; gap: 8px; margin-left: auto; flex-wrap: wrap; }
.dataset-alert { margin-bottom: 16px; border-radius: 10px; }

.dataset-assets-card,
.dataset-settings-card,
.dataset-preview-card {
  border: 1px solid var(--dataset-border);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 8px 24px rgb(15 23 42 / 4%);
}

.dataset-assets-card { padding: 20px; margin-bottom: 16px; }
.dataset-section-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.dataset-section-heading h4,
.dataset-panel-heading h4 { margin: 4px 0 0; font-size: 16px; }
.dataset-section-summary { color: var(--dataset-muted); font-size: 12px; }
.dataset-section-summary strong { color: var(--dataset-primary); font-size: 17px; }
.dataset-assets-card :deep(.asset-review) { margin-top: 14px; }
.dataset-assets-card :deep(.review-header) { margin-bottom: 10px; }
.dataset-assets-card :deep(.asset-grid) { grid-template-columns: repeat(auto-fill, minmax(128px, 1fr)); max-height: 248px; }
.dataset-assets-card :deep(.asset-tile) { border-radius: 10px; }

.dataset-layout {
  display: grid;
  grid-template-columns: minmax(390px, 430px) minmax(540px, 1fr);
  align-items: start;
  gap: 16px;
}

.dataset-settings-card,
.dataset-preview-card { padding: 20px; }
.dataset-preview-card { position: sticky; top: 16px; }
.dataset-panel-heading { display: flex; align-items: center; gap: 12px; padding-bottom: 16px; margin-bottom: 18px; border-bottom: 1px solid #e9eef5; }
.dataset-preview-heading > .el-tag { margin-left: auto; }
.dataset-panel-icon.is-cyan { color: #0891b2; background: #ecfeff; }

.dataset-form :deep(.el-form-item) { margin-bottom: 16px; }
.dataset-form :deep(.el-form-item__label) { padding-bottom: 7px; color: #374151; font-size: 12px; font-weight: 600; line-height: 1.3; }
.dataset-form :deep(.el-select),
.dataset-form :deep(.el-input-number) { width: 100%; }
.dataset-form :deep(.el-input__wrapper) { min-height: 40px; border-radius: 8px; box-shadow: 0 0 0 1px #dce3ec inset; }
.dataset-form :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px var(--dataset-primary) inset, 0 0 0 3px rgb(37 99 235 / 10%); }
.dataset-field-note { display: flex; align-items: center; gap: 5px; margin-top: 7px; color: #16a34a; font-size: 11px; }
.dataset-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 14px; }
.dataset-range { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; gap: 6px; width: 100%; }
.dataset-range > span { color: #94a3b8; }

.dataset-subsection-title { display: flex; align-items: center; justify-content: space-between; margin: 4px 0 10px; font-size: 12px; font-weight: 700; }
.dataset-subsection-title small { color: var(--dataset-muted); font-weight: 400; }
.dataset-margin-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.dataset-margin-field { display: block; padding: 9px; border: 1px solid #e3e9f1; border-radius: 9px; background: #f8fafc; }
.dataset-margin-field > span { display: block; margin-bottom: 6px; color: var(--dataset-muted); font-size: 11px; }
.dataset-margin-field :deep(.el-input__wrapper) { padding-left: 6px; padding-right: 30px; background: #fff; }

.dataset-advanced { margin-top: 18px; border-top: 1px solid #e9eef5; border-bottom: 1px solid #e9eef5; }
.dataset-advanced :deep(.el-collapse-item__header) { height: 48px; border-bottom: 0; }
.dataset-advanced :deep(.el-collapse-item__wrap) { border-bottom: 0; }
.dataset-collapse-title { display: flex; align-items: center; justify-content: space-between; width: 100%; padding-right: 10px; font-weight: 600; }
.dataset-collapse-title small { color: var(--dataset-muted); font-weight: 400; }
.quality-control { width: 100%; }
.quality-control :deep(.el-slider) { margin: 4px 12px 8px 0; }

.dataset-preflight { padding: 14px; margin-top: 18px; border: 1px solid #f4d79a; border-radius: 10px; background: #fffbeb; }
.dataset-preflight.is-ready { border-color: #bbebc8; background: #f0fdf4; }
.dataset-preflight-title { display: flex; align-items: center; gap: 7px; color: #b45309; font-size: 13px; font-weight: 700; }
.dataset-preflight.is-ready .dataset-preflight-title { color: #15803d; }
.dataset-preflight ul { display: grid; gap: 7px; padding: 0; margin: 12px 0 0; list-style: none; }
.dataset-preflight li { display: grid; grid-template-columns: 18px minmax(80px, auto) 1fr; align-items: center; color: #92400e; font-size: 11px; }
.dataset-preflight li.pass { color: #166534; }
.dataset-preflight li > span { display: grid; width: 15px; height: 15px; place-items: center; border-radius: 50%; color: #fff; background: #d97706; font-size: 9px; font-weight: 700; }
.dataset-preflight li.pass > span { background: #16a34a; }
.dataset-preflight li small { justify-self: end; color: var(--dataset-muted); }
.dataset-submit { width: 100%; height: 48px; margin-top: 16px; border-radius: 9px; font-weight: 700; }

.dataset-preview-frame {
  position: relative;
  display: grid;
  min-height: 300px;
  place-items: center;
  overflow: hidden;
  border: 1px solid #cfd8e5;
  border-radius: 10px;
  background: #111827;
}
.dataset-preview-frame > img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.dataset-preview-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; color: #94a3b8; font-size: 12px; }
.dataset-preview-empty .el-icon { font-size: 32px; }
.dataset-valid-area { position: absolute; z-index: 1; min-width: 2px; min-height: 2px; pointer-events: none; border: 2px dashed #22d3ee; background: rgb(34 211 238 / 5%); box-shadow: 0 0 0 1px rgb(255 255 255 / 35%) inset; }
.dataset-valid-area.invalid { border-color: #ef4444; background: rgb(239 68 68 / 10%); }
.dataset-valid-area span { position: absolute; top: 6px; left: 7px; padding: 3px 6px; border-radius: 4px; color: #ecfeff; background: rgb(8 145 178 / 88%); font-size: 10px; white-space: nowrap; }
.dataset-preview-part { position: absolute; z-index: 2; height: 20%; border: 2px solid #22d3ee; background: rgb(255 255 255 / 5%); box-shadow: 0 4px 12px rgb(15 23 42 / 35%); }
.dataset-preview-part:nth-of-type(even) { border-color: #f59e0b; }
.dataset-preview-part > img { width: 100%; height: 100%; object-fit: contain; }
.dataset-preview-part > span { position: absolute; top: -21px; left: -2px; padding: 2px 5px; color: #fff; background: #0891b2; font: 9px/1.4 Consolas, monospace; white-space: nowrap; }
.dataset-preview-part:nth-of-type(even) > span { background: #d97706; }
.dataset-preview-legend { display: flex; align-items: center; gap: 16px; padding: 11px 12px; margin-top: 10px; border-radius: 8px; color: var(--dataset-muted); background: #f8fafc; font-size: 11px; }
.dataset-preview-legend span { display: flex; align-items: center; gap: 6px; }
.dataset-preview-legend i { width: 16px; height: 3px; border-radius: 999px; }
.legend-cyan { background: #22d3ee; }
.legend-orange { background: #f59e0b; }
.dataset-preview-legend strong { margin-left: auto; color: #334155; }

.dataset-flow { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; margin-top: 18px; }
.dataset-flow-node { position: relative; min-width: 0; padding: 10px; border-radius: 8px; background: #f8fafc; }
.dataset-flow-node.active { color: var(--dataset-primary); background: var(--dataset-primary-soft); }
.dataset-flow-node span { display: block; overflow: hidden; color: var(--dataset-muted); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.dataset-flow-node strong { display: block; margin-top: 4px; font-size: 17px; }
.dataset-flow-node i { position: absolute; top: 24px; right: -8px; z-index: 1; color: #94a3b8; font-style: normal; }
.dataset-contract { padding: 13px; margin-top: 14px; border-radius: 8px; background: #0f172a; }
.dataset-contract > div { display: flex; align-items: center; justify-content: space-between; margin-bottom: 9px; color: #cbd5e1; font-size: 11px; }
.dataset-contract code { display: block; overflow-wrap: anywhere; color: #bae6fd; font: 11px/1.55 Consolas, monospace; }
.dataset-run-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }
.dataset-run-summary > div { padding: 11px; border: 1px solid #e6ebf2; border-radius: 8px; }
.dataset-run-summary span { display: block; color: var(--dataset-muted); font-size: 10px; }
.dataset-run-summary strong { display: block; margin-top: 5px; font-size: 12px; }
.dataset-footer { margin-top: 16px; }

@media (max-width: 1180px) {
  .dataset-layout { grid-template-columns: 1fr; }
  .dataset-preview-card { position: static; }
  .dataset-preview-frame { min-height: 340px; }
}

@media (max-width: 700px) {
  .workflow-steps { padding: 16px 10px; }
  .dataset-hero { align-items: flex-start; flex-wrap: wrap; }
  .dataset-hero-status { justify-content: flex-start; width: 100%; margin-left: 58px; }
  .dataset-section-heading { align-items: flex-start; flex-direction: column; }
  .dataset-settings-card,
  .dataset-preview-card,
  .dataset-assets-card { padding: 14px; }
  .dataset-form-grid { grid-template-columns: 1fr; }
  .dataset-margin-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dataset-flow { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dataset-flow-node i { display: none; }
  .dataset-run-summary { grid-template-columns: 1fr; }
  .dataset-preview-frame { min-height: 240px; }
  .dataset-preview-legend { align-items: flex-start; flex-direction: column; }
  .dataset-preview-legend strong { margin-left: 0; }
}
</style>
