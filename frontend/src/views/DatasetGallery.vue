<template>
  <div class="page gallery-page">
    <div class="toolbar">
      <div>
        <el-button link :icon="ArrowLeft" @click="$router.push(`/projects/${projectId}`)">返回项目</el-button>
        <h2>生成结果阅览</h2>
        <div class="muted">按生成批次查看、预览和下载合成图，以及对应的标签与生成记录。</div>
      </div>
      <div class="toolbar-actions">
        <el-dropdown :disabled="!gallery?.files.length || loading || Boolean(batchDownloading)" @command="downloadBatch">
          <el-button type="primary" :icon="Download" :loading="Boolean(batchDownloading)">
            {{ batchDownloading ? '正在打包' : '批量下载' }}
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="images">全部图片</el-dropdown-item>
              <el-dropdown-item command="labels">全部标签 TXT</el-dropdown-item>
              <el-dropdown-item command="all" divided>图片 + 标签</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button :icon="Refresh" @click="loadRuns">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never" class="run-selector section">
      <el-form inline>
        <el-form-item label="数据集批次">
          <el-select v-model="selectedDatasetId" placeholder="选择一次已完成的数据生成" filterable @change="loadFiles">
            <el-option v-for="run in datasetRuns" :key="run.id" :label="runLabel(run)" :value="run.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="gallery">
          <el-tag type="success">{{ gallery.total_images }} 张图</el-tag>
          <el-tag class="run-tag">{{ gallery.label_format || '-' }}</el-tag>
          <el-tag class="run-tag" type="info">{{ gallery.layout_mode || '-' }}</el-tag>
        </el-form-item>
      </el-form>
    </el-card>

    <el-empty v-if="!datasetRuns.length && !loading" description="暂无已完成的数据集，请先执行第三步" />
    <el-empty v-else-if="gallery && !gallery.files.length" description="该批次尚未找到生成图像" />
    <div v-else v-loading="loading" class="gallery-grid">
      <el-card v-for="file in pagedFiles" :key="file.file_name" shadow="never" class="result-card">
        <button class="image-button" type="button" @click="openImage(file)">
          <img :src="file.image_url" :alt="file.file_name" loading="lazy" />
        </button>
        <div class="result-name" :title="file.file_name">{{ file.file_name }}</div>
        <div class="result-actions">
          <el-tooltip content="查看图片"><el-button circle :icon="View" @click="openImage(file)" /></el-tooltip>
          <el-tooltip content="下载图片"><el-button circle :icon="Download" @click="downloadFile(file.image_url, file.file_name)" /></el-tooltip>
          <el-tooltip v-if="file.label_url" content="查看标签 TXT"><el-button circle :icon="Document" @click="openText(file.label_url, `${file.file_name} 标签`)" /></el-tooltip>
          <el-tooltip v-if="file.label_url" content="下载标签 TXT"><el-button circle :icon="Download" @click="downloadFile(file.label_url, `${baseName(file.file_name)}.txt`)" /></el-tooltip>
          <el-tooltip v-if="file.metadata_url" content="查看生成信息 TXT"><el-button circle :icon="Tickets" @click="openText(file.metadata_url, `${file.file_name} 生成信息`)" /></el-tooltip>
          <el-tooltip v-if="file.metadata_url" content="下载生成信息 TXT"><el-button circle :icon="Download" @click="downloadFile(file.metadata_url, `${baseName(file.file_name)}_metadata.txt`)" /></el-tooltip>
        </div>
      </el-card>
    </div>

    <div v-if="gallery?.files.length" class="pagination-wrap">
      <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="gallery.files.length" layout="total, prev, pager, next" background />
    </div>

    <el-dialog v-model="imageDialogVisible" :title="activeFile?.file_name || '图片预览'" width="min(960px, 92vw)">
      <img v-if="activeFile" class="dialog-image" :src="activeFile.image_url" :alt="activeFile.file_name" />
      <template #footer><el-button :icon="Download" @click="downloadFile(activeFile.image_url, activeFile.file_name)">下载图片</el-button></template>
    </el-dialog>
    <el-dialog v-model="textDialogVisible" :title="textTitle" width="min(900px, 92vw)">
      <div v-loading="textLoading" class="text-viewer"><pre>{{ textContent }}</pre></div>
      <template #footer><el-button :icon="Download" @click="downloadFile(activeTextUrl, textTitle.endsWith('标签') ? 'label.txt' : 'metadata.txt')">下载 TXT</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowDown, ArrowLeft, Document, Download, Refresh, Tickets, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { downloadDatasetArchive, listAssets, listDatasetFiles } from '../api/client'

const route = useRoute()
const projectId = route.params.id
const datasetRuns = ref([])
const selectedDatasetId = ref('')
const gallery = ref(null)
const loading = ref(false)
const currentPage = ref(1)
const pageSize = 24
const activeFile = ref(null)
const imageDialogVisible = ref(false)
const textDialogVisible = ref(false)
const textLoading = ref(false)
const textContent = ref('')
const textTitle = ref('')
const activeTextUrl = ref('')
const batchDownloading = ref('')
const pagedFiles = computed(() => gallery.value?.files.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize) || [])

async function loadRuns() {
  loading.value = true
  try {
    datasetRuns.value = await listAssets(projectId, 'dataset')
    if (!datasetRuns.value.some(item => item.id === selectedDatasetId.value)) selectedDatasetId.value = datasetRuns.value[0]?.id || ''
    if (selectedDatasetId.value) await loadFiles()
    else gallery.value = null
  } finally { loading.value = false }
}
async function loadFiles() {
  if (!selectedDatasetId.value) return
  loading.value = true
  try { gallery.value = await listDatasetFiles(projectId, selectedDatasetId.value); currentPage.value = 1 }
  finally { loading.value = false }
}
function runLabel(run) { return `${formatDate(run.created_at)} · ${run.meta?.images || 0} 张 · ${run.meta?.label_format || 'dataset'}` }
function formatDate(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-' }
function baseName(name) { return name.replace(/\.[^.]+$/, '') }
function archiveNameFromHeader(header, fallback) {
  const utf8Name = header?.match(/filename\*=utf-8''([^;]+)/i)?.[1]
  if (utf8Name) return decodeURIComponent(utf8Name)
  return header?.match(/filename="?([^";]+)"?/i)?.[1] || fallback
}
async function downloadBatch(content) {
  if (!selectedDatasetId.value || batchDownloading.value) return
  batchDownloading.value = content
  try {
    const response = await downloadDatasetArchive(projectId, selectedDatasetId.value, content)
    const fallback = `dataset_${content}.zip`
    const filename = archiveNameFromHeader(response.headers['content-disposition'], fallback)
    const url = URL.createObjectURL(response.data)
    downloadFile(url, filename)
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    ElMessage.success(`批量文件已打包：${filename}`)
  } catch (error) {
    ElMessage.error(error.response?.status === 404 ? '当前批次没有可下载的对应文件' : '批量下载失败，请稍后重试')
  } finally { batchDownloading.value = '' }
}
function openImage(file) { activeFile.value = file; imageDialogVisible.value = true }
async function openText(url, title) {
  textTitle.value = title; activeTextUrl.value = url; textContent.value = ''; textDialogVisible.value = true; textLoading.value = true
  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    textContent.value = await response.text()
  } catch (error) { textContent.value = `无法读取文件：${error.message}`; ElMessage.error('TXT 读取失败') }
  finally { textLoading.value = false }
}
function downloadFile(url, name) { const link = document.createElement('a'); link.href = url; link.download = name; document.body.appendChild(link); link.click(); link.remove() }
onMounted(loadRuns)
</script>

<style scoped>
.dropdown-icon { margin-left: 8px; }
.run-selector :deep(.el-form) { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; }
.run-selector :deep(.el-form-item) { margin: 0; max-width: 100%; }
.run-selector :deep(.el-form-item__content) { min-width: 0; }
.run-selector :deep(.el-select) { width: 390px; max-width: 100%; }
.run-tag { margin-left: 8px; }
.gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 18px; min-height: 200px; }
.result-card { min-width: 0; }
.image-button { display: block; width: 100%; padding: 8px; border: 1px solid var(--el-border-color-light); background: var(--studio-bg); cursor: zoom-in; }
.image-button img { display: block; width: 100%; aspect-ratio: 4 / 3; object-fit: contain; }
.result-name { margin: 13px 0 12px; font: 13px/1.6 var(--studio-mono); overflow-wrap: anywhere; color: #475044; }
.result-actions { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; padding-top: 12px; border-top: 1px solid var(--el-border-color-light); }
.result-actions :deep(.el-button) { width: 38px; border-radius: 3px; margin: 0; justify-self: center; }
.pagination-wrap { display: flex; justify-content: center; margin: 28px 0; }
.dialog-image { display: block; max-width: 100%; max-height: 70vh; object-fit: contain; margin: auto; }
.text-viewer { min-height: 180px; max-height: 65vh; overflow: auto; background: #252a30; border-radius: 3px; padding: 18px; }
.text-viewer pre { margin: 0; color: #eee9dc; font: 13px/1.7 var(--studio-mono); white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 700px) {
  .run-selector :deep(.el-form) { display: block; }
  .run-selector :deep(.el-form-item) { display: block; margin-bottom: 12px; }
  .run-selector :deep(.el-form-item:last-child) { margin-bottom: 0; }
  .run-selector :deep(.el-form-item__label) { display: block; padding: 0 0 7px; height: auto; text-align: left; line-height: 1.6; }
  .run-selector :deep(.el-form-item__content) { margin-left: 0 !important; }
  .run-selector :deep(.el-select) { width: 100%; }
  .gallery-grid { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
}
</style>
