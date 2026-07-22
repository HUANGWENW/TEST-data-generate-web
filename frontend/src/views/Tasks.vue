<template>
  <div class="page tasks-page">
    <div class="toolbar">
      <div><span class="page-kicker">BACKGROUND JOBS</span><h2>任务中心</h2><div class="muted">任务状态每 3 秒自动刷新，可在完成后直接进入结果图库。</div></div>
      <el-button :icon="Refresh" :loading="loading" @click="load">立即刷新</el-button>
    </div>

    <div class="task-stats">
      <article v-for="item in taskStats" :key="item.key" class="task-stat"><i :class="item.key"></i><div><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div></article>
    </div>

    <section class="tasks-panel">
      <div class="panel-heading"><div><h3>任务列表</h3><p>包含 Mask 提取、透明零件生成和数据集合成任务。</p></div><el-tag effect="plain">共 {{ tasks.length }} 项</el-tag></div>
      <el-table :data="tasks" v-loading="loading" empty-text="暂无后台任务">
        <el-table-column label="任务" min-width="210">
          <template #default="{ row }"><div class="task-name"><div class="task-icon"><el-icon><DataAnalysis /></el-icon></div><div><strong>{{ taskTypeLabel(row.task_type) }}</strong><small>{{ row.id.slice(0, 8) }} · {{ formatDate(row.created_at) }}</small></div></div></template>
        </el-table-column>
        <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="statusType(row.status)" effect="light">{{ statusLabel(row.status) }}</el-tag></template></el-table-column>
        <el-table-column label="进度" min-width="180"><template #default="{ row }"><div class="task-progress"><el-progress :percentage="row.progress" :status="row.status === 'failed' ? 'exception' : row.status === 'succeeded' ? 'success' : ''" /><small>{{ row.message || '等待更新' }}</small></div></template></el-table-column>
        <el-table-column label="结果与耗时" min-width="220">
          <template #default="{ row }">
            <div v-if="row.task_type === 'generate_dataset' && row.status === 'succeeded'" class="task-result"><el-button link type="primary" @click="openGallery(row.project_id)">查看生成结果 →</el-button><el-tooltip v-if="row.result?.performance" :content="performanceDetail(row.result.performance)"><span>总计 {{ formatDuration(row.result.performance.total_seconds) }} · {{ formatDuration(row.result.performance.average_image_seconds) }}/张</span></el-tooltip></div>
            <span v-else-if="row.error" class="task-error">{{ row.error }}</span>
            <span v-else class="task-placeholder">任务完成后显示</span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="155"><template #default="{ row }">{{ formatDate(row.updated_at || row.created_at) }}</template></el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { DataAnalysis, Refresh } from '@element-plus/icons-vue'
import { listTasks } from '../api/client'

const tasks = ref([])
const loading = ref(false)
const router = useRouter()
let timer = null
const taskStats = computed(() => [
  { key: 'running', label: '运行中', value: tasks.value.filter(item => item.status === 'running').length },
  { key: 'queued', label: '排队中', value: tasks.value.filter(item => item.status === 'queued').length },
  { key: 'succeeded', label: '已完成', value: tasks.value.filter(item => item.status === 'succeeded').length },
  { key: 'failed', label: '失败', value: tasks.value.filter(item => item.status === 'failed').length }
])

function statusType(status) { if (status === 'succeeded') return 'success'; if (status === 'failed') return 'danger'; if (status === 'running') return 'warning'; return 'info' }
function statusLabel(status) { return ({ queued: '排队中', running: '生成中', succeeded: '已完成', failed: '失败' }[status] || status) }
function taskTypeLabel(type) { return ({ extract_gen_masks: 'GEN Mask 提取', extract_edge_masks: '边缘图 Mask 提取', masks_to_parts: '透明零件生成', generate_dataset: '合成数据集与标签' }[type] || type) }
function openGallery(projectId) { router.push(`/projects/${projectId}/gallery`) }
function formatDate(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-' }
function formatDuration(seconds) { if (seconds === undefined || seconds === null) return '-'; return seconds >= 60 ? `${(seconds / 60).toFixed(1)} 分钟` : `${Number(seconds).toFixed(2)} 秒` }
function performanceDetail(performance) { return `预加载 ${formatDuration(performance.preload_seconds)}；合成 ${formatDuration(performance.composition_seconds)}；图片写入 ${formatDuration(performance.image_write_seconds)}；标签写入 ${formatDuration(performance.label_write_seconds)}；生成信息写入 ${formatDuration(performance.metadata_write_seconds)}` }

async function load() { loading.value = true; try { tasks.value = await listTasks() } finally { loading.value = false } }
onMounted(() => { load(); timer = window.setInterval(load, 3000) })
onUnmounted(() => { if (timer) window.clearInterval(timer) })
</script>

<style scoped>
.page-kicker { color: #2563eb; font-size: 10px; font-weight: 700; letter-spacing: .14em; }
.task-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 18px; }
.task-stat { display: flex; align-items: center; gap: 12px; padding: 16px 18px; border: 1px solid #dce3ec; border-radius: 11px; background: #fff; box-shadow: 0 8px 24px rgb(15 23 42 / 4%); }
.task-stat i { width: 10px; height: 10px; border-radius: 50%; background: #2563eb; box-shadow: 0 0 0 5px rgb(37 99 235 / 10%); }
.task-stat i.running { background: #d97706; box-shadow: 0 0 0 5px rgb(217 119 6 / 10%); }
.task-stat i.succeeded { background: #16a34a; box-shadow: 0 0 0 5px rgb(22 163 74 / 10%); }
.task-stat i.failed { background: #dc2626; box-shadow: 0 0 0 5px rgb(220 38 38 / 10%); }
.task-stat span,.task-stat strong { display: block; }
.task-stat span { color: #64748b; font-size: 11px; }
.task-stat strong { margin-top: 2px; font-size: 23px; }
.tasks-panel { padding: 20px; border: 1px solid #dce3ec; border-radius: 14px; background: #fff; box-shadow: 0 8px 24px rgb(15 23 42 / 4%); }
.panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.panel-heading h3 { margin: 0 0 5px; font-size: 17px; }
.panel-heading p { margin: 0; color: #64748b; font-size: 12px; }
.tasks-panel :deep(.el-table) { box-shadow: none; }
.task-name { display: flex; align-items: center; gap: 11px; }
.task-icon { display: grid; flex: 0 0 auto; width: 38px; height: 38px; place-items: center; border-radius: 9px; color: #2563eb; background: #eff6ff; }
.task-name strong,.task-name small { display: block; }
.task-name small,.task-progress small,.task-result span,.task-placeholder { margin-top: 3px; color: #64748b; font-size: 10px; }
.task-progress :deep(.el-progress-bar__outer) { background: #e8eef6; }
.task-result { display: flex; flex-direction: column; align-items: flex-start; }
.task-result .el-button { min-height: auto; padding: 0; }
.task-error { color: #dc2626; font-size: 11px; }

@media(max-width: 820px) { .task-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } .panel-heading { align-items: flex-start; flex-direction: column; } }
</style>
