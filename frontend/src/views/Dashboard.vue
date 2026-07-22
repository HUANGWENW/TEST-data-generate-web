<template>
  <div class="page dashboard-page">
    <div class="toolbar dashboard-toolbar">
      <div><span class="page-kicker">PROJECT WORKSPACE</span><h2>项目总览</h2><div class="muted">集中管理输入素材、Mask、透明零件、合成数据和标签。</div></div>
      <el-button type="primary" :icon="Plus" size="large" @click="dialogVisible = true">新建项目</el-button>
    </div>

    <div class="dashboard-stats">
      <article class="stat-card"><div class="stat-icon"><el-icon><FolderOpened /></el-icon></div><div><span>项目总数</span><strong>{{ projects.length }}</strong><small>个生产项目</small></div></article>
      <article class="stat-card"><div class="stat-icon is-green"><el-icon><CircleCheckFilled /></el-icon></div><div><span>今日创建</span><strong>{{ todayProjects }}</strong><small>个新项目</small></div></article>
      <article class="stat-card"><div class="stat-icon is-cyan"><el-icon><DataAnalysis /></el-icon></div><div><span>标准流程</span><strong>3</strong><small>个生成步骤</small></div></article>
    </div>

    <section class="projects-panel">
      <div class="panel-heading"><div><h3>最近项目</h3><p>按创建时间倒序排列，进入项目后可继续任意生成步骤。</p></div><el-tag effect="plain">{{ projects.length }} 个项目</el-tag></div>
      <el-table v-if="projects.length || loading" :data="projects" v-loading="loading">
        <el-table-column label="项目名称" min-width="240">
          <template #default="{ row }"><div class="project-name"><span>{{ row.name.slice(0, 1).toUpperCase() }}</span><div><strong>{{ row.name }}</strong><small>项目 ID · {{ row.id.slice(0, 8) }}</small></div></div></template>
        </el-table-column>
        <el-table-column label="说明" min-width="300"><template #default="{ row }"><span class="project-description">{{ row.description || '暂无项目说明' }}</span></template></el-table-column>
        <el-table-column label="创建时间" width="190"><template #default="{ row }">{{ formatDate(row.created_at) }}</template></el-table-column>
        <el-table-column label="状态" width="120"><template #default><el-tag type="success" effect="light">可用</el-tag></template></el-table-column>
        <el-table-column label="操作" width="130"><template #default="{ row }"><el-button type="primary" link @click="$router.push(`/projects/${row.id}`)">进入工作台 →</el-button></template></el-table-column>
      </el-table>
      <el-empty v-else description="还没有项目，先创建一个生产项目" />
    </section>

    <el-dialog v-model="dialogVisible" title="新建生产项目" width="520px">
      <div class="dialog-hint">创建后将自动建立素材、Mask、零件和数据集目录。</div>
      <el-form :model="form" label-position="top">
        <el-form-item label="项目名称"><el-input v-model="form.name" placeholder="例如：M104P106P 钢板零件" maxlength="160" show-word-limit /></el-form-item>
        <el-form-item label="项目说明"><el-input v-model="form.description" type="textarea" :rows="4" placeholder="说明零件类型、目标标注格式或本批次用途" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="submit">创建并进入</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CircleCheckFilled, DataAnalysis, FolderOpened, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { createProject, listProjects } from '../api/client'

const projects = ref([])
const router = useRouter()
const loading = ref(false)
const dialogVisible = ref(false)
const form = reactive({ name: '', description: '' })
const todayProjects = computed(() => projects.value.filter(item => new Date(item.created_at).toDateString() === new Date().toDateString()).length)

function formatDate(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-' }

async function load() {
  loading.value = true
  try { projects.value = await listProjects() }
  finally { loading.value = false }
}

async function submit() {
  if (!form.name.trim()) return ElMessage.warning('请输入项目名称')
  const project = await createProject({ name: form.name, description: form.description })
  dialogVisible.value = false
  form.name = ''
  form.description = ''
  ElMessage.success('项目已创建')
  await load()
  if (project?.id) router.push(`/projects/${project.id}`)
}

onMounted(load)
</script>

<style scoped>
.page-kicker { color: #2563eb; font-size: 10px; font-weight: 700; letter-spacing: .14em; }
.dashboard-toolbar { align-items: center; }
.dashboard-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
.stat-card { display: flex; align-items: center; gap: 14px; min-height: 104px; padding: 18px; border: 1px solid #dce3ec; border-radius: 12px; background: #fff; box-shadow: 0 8px 24px rgb(15 23 42 / 4%); }
.stat-icon { display: grid; flex: 0 0 auto; width: 42px; height: 42px; place-items: center; border-radius: 10px; color: #2563eb; background: #eff6ff; font-size: 20px; }
.stat-icon.is-green { color: #16a34a; background: #f0fdf4; }
.stat-icon.is-cyan { color: #0891b2; background: #ecfeff; }
.stat-card span,.stat-card small,.project-name small { display: block; color: #64748b; font-size: 11px; }
.stat-card strong { display: inline-block; margin: 2px 7px 1px 0; color: #172033; font-size: 26px; }
.stat-card small { display: inline; }
.projects-panel { padding: 20px; border: 1px solid #dce3ec; border-radius: 14px; background: #fff; box-shadow: 0 8px 24px rgb(15 23 42 / 4%); }
.panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.panel-heading h3 { margin: 0 0 5px; font-size: 17px; }
.panel-heading p { margin: 0; color: #64748b; font-size: 12px; }
.projects-panel :deep(.el-table) { box-shadow: none; }
.project-name { display: flex; align-items: center; gap: 11px; }
.project-name > span { display: grid; flex: 0 0 auto; width: 36px; height: 36px; place-items: center; border-radius: 9px; color: #2563eb; background: #eff6ff; font-weight: 700; }
.project-name strong,.project-name small { display: block; }
.project-name small { margin-top: 2px; }
.project-description { color: #64748b; }
.dialog-hint { padding: 11px 13px; margin-bottom: 18px; border-radius: 8px; color: #1d4ed8; background: #eff6ff; font-size: 12px; }

@media(max-width: 820px) { .dashboard-stats { grid-template-columns: 1fr; } .panel-heading { align-items: flex-start; flex-direction: column; } }
</style>
