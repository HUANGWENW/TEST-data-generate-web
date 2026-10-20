<template>
  <div class="page dxf-page">
    <div class="toolbar">
      <div>
        <el-button link :icon="ArrowLeft" @click="$router.push(`/projects/${projectId}`)">返回项目</el-button>
        <h2>DXF 预处理</h2>
        <div class="muted">{{ project?.name || '当前项目' }} · DXF 转边缘图算法待接入</div>
      </div>
      <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
    </div>

    <el-alert title="当前页面只保存 DXF 原文件，不会创建解析任务或生成边缘图。" type="info" :closable="false" show-icon class="section" />

    <el-card shadow="never" class="dxf-upload-card section">
      <template #header><div class="card-title"><span>上传 DXF 文件</span><el-tag type="warning">待接入</el-tag></div></template>
      <el-upload accept=".dxf" :auto-upload="false" :show-file-list="false" :on-change="onUpload">
        <el-button type="primary" :icon="Upload" :loading="uploading">选择 DXF 文件</el-button>
      </el-upload>
      <div class="hint">仅接受 <code>.dxf</code> 文件。后续接入解析算法后，边缘图将作为第一步“边缘图”的输入资产。</div>
    </el-card>

    <section class="section">
      <div class="section-heading"><div><h3>已保存的 DXF</h3><div class="muted">{{ dxfAssets.length }} 个文件，均处于待解析状态。</div></div></div>
      <el-table :data="dxfAssets" v-loading="loading">
        <el-table-column prop="original_name" label="文件名" min-width="280" />
        <el-table-column label="大小" width="140"><template #default="{ row }">{{ formatBytes(row.size_bytes) }}</template></el-table-column>
        <el-table-column label="状态" width="140"><template #default><el-tag type="warning">待解析</el-tag></template></el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="220" />
      </el-table>
    </section>

    <section class="output-contract">
      <div class="contract-icon"><el-icon><Picture /></el-icon></div>
      <div><strong>未来输出契约</strong><p>每个 DXF 解析任务将输出一张白色边缘图，并自动登记为第一步可选择的“边缘图”输入文件。</p></div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Picture, Refresh, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getProject, listAssets, uploadAsset } from '../api/client'

const route = useRoute()
const projectId = route.params.id
const project = ref(null)
const assets = ref([])
const loading = ref(false)
const uploading = ref(false)
const dxfAssets = computed(() => assets.value.filter(asset => asset.asset_type === 'dxf'))

async function loadAll() {
  loading.value = true
  try {
    project.value = await getProject(projectId)
    assets.value = await listAssets(projectId)
  } finally { loading.value = false }
}

async function onUpload(file) {
  uploading.value = true
  try {
    await uploadAsset(projectId, 'dxf', file.raw)
    ElMessage.success('DXF 文件已保存，等待后续解析算法接入')
    await loadAll()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'DXF 上传失败')
  } finally { uploading.value = false }
}

function formatBytes(bytes) { if (!bytes) return '0 B'; const units = ['B', 'KB', 'MB', 'GB']; let value = bytes; let index = 0; while (value >= 1024 && index < units.length - 1) { value /= 1024; index += 1 } return `${value.toFixed(index ? 1 : 0)} ${units[index]}` }
onMounted(loadAll)
</script>

<style scoped>
.dxf-page { max-width: 1244px; }
.card-title { display: flex; justify-content: space-between; align-items: center; gap: 12px; font-weight: 600; }
.hint { margin-top: 16px; color: var(--studio-muted); font-size: 14px; line-height: 1.7; }
.hint code { font-family: var(--studio-mono); }
.section-heading { margin: 28px 0 14px; }
.section-heading h3 { margin: 0 0 6px; font: 600 23px/1.4 var(--studio-serif); }
.output-contract { display: flex; gap: 14px; align-items: flex-start; padding: 18px 0; border-top: 1px solid var(--studio-border); color: var(--studio-muted); }
.contract-icon { display: grid; flex-shrink: 0; place-items: center; width: 38px; height: 38px; border: 1px solid var(--studio-border); color: var(--studio-primary); font-size: 20px; }
.output-contract strong { display: block; color: var(--studio-text); font-weight: 600; }
.output-contract p { margin: 5px 0 0; font-size: 14px; line-height: 1.7; }
</style>
