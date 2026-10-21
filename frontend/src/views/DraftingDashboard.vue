<template>
  <div class="drafting-dashboard">
    <aside class="project-directory" aria-labelledby="directory-title">
      <header class="directory-heading"><h1 id="directory-title">项目总览</h1><span>{{ state.projects.length }} 个项目</span></header>
      <el-button class="create-project" :icon="Plus" :disabled="state.creating || Boolean(state.deletingProjectId)" @click="dialogVisible = true">新建项目</el-button>
      <div v-if="state.listError" class="list-error" role="alert"><p>{{ state.listError }}</p><el-button plain size="small" @click="refresh">重新加载</el-button></div>
      <div v-else-if="state.loading && !state.projects.length" class="directory-loading" role="status"><el-icon class="loading-turn"><Loading /></el-icon>正在读取项目</div>
      <div v-else-if="!state.projects.length" class="directory-empty"><el-icon><FolderOpened /></el-icon><p>还没有项目</p><span>新建项目后，从上传素材开始。</span></div>
      <div v-if="state.projects.length" class="project-options" role="group" aria-label="选择项目" :aria-busy="state.loading">
        <button v-for="project in state.projects" :key="project.id" class="project-option" :class="{ selected: project.id === state.selectedProjectId }" :aria-pressed="project.id === state.selectedProjectId" :aria-label="`选择项目 ${project.name}（${project.id.slice(0, 8)}）`" :disabled="Boolean(state.deletingProjectId)" @click="controller.selectProject(project.id)">
          <span class="option-heading"><strong>{{ project.name }}</strong><el-icon><ArrowRight /></el-icon></span>
          <span class="option-meta"><span>{{ project.id.slice(0, 8) }}</span><time>{{ shortDate(project.created_at) }}</time></span>
          <span class="option-description" :title="project.description || '暂无项目说明'">{{ project.description || '暂无项目说明' }}</span>
        </button>
      </div>
      <footer class="directory-footer"><span>创建时间倒序</span><span>今日新建 {{ todayProjects }}</span><el-button class="directory-refresh" link :icon="Refresh" :loading="state.loading" :disabled="Boolean(state.deletingProjectId)" @click="refresh">刷新项目</el-button></footer>
    </aside>

    <main class="selected-project">
      <div v-if="!selectedProject" class="workspace-empty"><el-icon><FolderOpened /></el-icon><h2>{{ state.loading ? '正在读取项目' : '从一个项目开始' }}</h2><p>{{ state.listError ? '项目暂未读取成功，请重新加载。' : '在左侧创建或选择项目，查看零件轮廓并继续生成。' }}</p><el-button v-if="!state.loading && !state.listError" type="primary" :icon="Plus" @click="dialogVisible = true">新建项目</el-button></div>
      <template v-else>
        <header class="selected-project-header"><div class="project-title"><h2>{{ selectedProject.name }}</h2><span class="project-id" :title="selectedProject.id">项目 · {{ selectedProject.id.slice(0, 8) }}</span></div><el-button class="enter-project" type="primary" :disabled="Boolean(state.deletingProjectId)" @click="enterProject">进入工作台<el-icon class="button-arrow"><ArrowRight /></el-icon></el-button></header>

        <section class="preview-sheet" aria-labelledby="preview-heading">
          <header class="preview-heading"><h3 id="preview-heading">{{ state.previewKind === 'mask' ? '零件轮廓' : '透明零件' }}</h3><div v-if="!state.assetError && state.assets.length" class="preview-tabs" role="group" aria-label="预览类型"><span class="preview-tab-marker" :class="{ 'at-parts': state.previewKind === 'part' }" aria-hidden="true"></span><button :aria-pressed="state.previewKind === 'mask'" :disabled="!maskCount || state.assetLoading" @click="controller.selectPreviewKind('mask')">Mask <span>{{ maskCount }}</span></button><button :aria-pressed="state.previewKind === 'part'" :disabled="!partCount || state.assetLoading" @click="controller.selectPreviewKind('part')">零件 <span>{{ partCount }}</span></button></div><span v-else-if="!state.assetLoading && !state.assetError" class="preview-note">素材预览</span></header>

          <div v-if="state.assetLoading" class="preview-state" role="status"><el-icon class="loading-turn"><Loading /></el-icon><h4>正在读取素材</h4><p>预览将保留原图的长宽比例。</p></div>
          <div v-else-if="state.assetError" class="preview-state" role="alert"><el-icon><Warning /></el-icon><h4>素材暂未读取成功</h4><p>{{ state.assetError }}</p><el-button plain @click="controller.selectProject(state.selectedProjectId, { force: true })">重新加载素材</el-button></div>
          <div v-else-if="!selectedAsset" class="preview-state"><el-icon><Picture /></el-icon><h4>还没有可预览的零件</h4><p>上传已有 Mask，或在第一步提取轮廓后，便可在这里预览。</p><el-button plain :disabled="Boolean(state.deletingProjectId)" @click="enterProject">进入项目上传素材</el-button></div>
          <ProjectDrawing v-else :asset="selectedAsset" />

          <div v-if="selectedAsset && !state.assetLoading && !state.assetError" class="preview-file"><span class="file-name" :title="selectedAsset.original_name">{{ selectedAsset.original_name }}</span><div v-if="candidates.length > 1" class="file-choice"><label for="drawing-file">预览素材</label><el-select id="drawing-file" v-model="state.previewAssetId" aria-label="预览素材" size="small"><el-option v-for="asset in candidates" :key="asset.id" :label="asset.original_name" :value="asset.id" /></el-select></div><span v-else class="preview-note">等比预览</span></div>
        </section>

        <section class="project-details" aria-label="项目详情"><div class="project-description"><span class="detail-label">项目说明</span><p>{{ selectedProject.description || '暂无项目说明' }}</p></div><div class="project-created"><span class="detail-label">创建时间</span><time>{{ formatDate(selectedProject.created_at) }}</time></div><el-button class="delete-project" type="danger" link :icon="Delete" :loading="state.deletingProjectId === selectedProject.id" :disabled="Boolean(state.deletingProjectId)" :aria-label="`删除项目 ${selectedProject.name}`" @click="removeSelectedProject">删除项目</el-button></section>

        <nav class="project-workflow" aria-label="生成流程"><span>生成流程</span><div><router-link :to="`/projects/${selectedProject.id}/step/1`"><span>1</span>提取 Mask</router-link><i aria-hidden="true"></i><router-link :to="`/projects/${selectedProject.id}/step/2`"><span>2</span>纹理填充</router-link><i aria-hidden="true"></i><router-link :to="`/projects/${selectedProject.id}/step/3`"><span>3</span>合成数据集</router-link></div></nav>
      </template>
    </main>

    <el-dialog v-model="dialogVisible" class="drafting-dialog" title="新建项目" width="min(520px, calc(100vw - 32px))" :close-on-click-modal="!state.creating" :close-on-press-escape="!state.creating" :show-close="!state.creating">
      <el-form :model="form" label-position="top" :disabled="state.creating" @submit.prevent="submit"><el-form-item label="项目名称"><el-input v-model="form.name" placeholder="例如：武穴钢板零件" maxlength="160" show-word-limit /></el-form-item><el-form-item label="项目说明"><el-input v-model="form.description" type="textarea" :rows="4" placeholder="记录零件类型或本批次用途" /></el-form-item></el-form>
      <template #footer><el-button :disabled="state.creating" @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="state.creating" @click="submit">创建并进入</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Delete, FolderOpened, Loading, Picture, Plus, Refresh, Warning } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '../api/client'
import ProjectDrawing from '../components/ProjectDrawing.vue'
import { createDashboardController, dashboardState, errorDetail, previewAssets } from '../composables/draftingDashboard.mjs'

const route = useRoute(); const router = useRouter()
const state = reactive(dashboardState())
const controller = createDashboardController(api, state)
const dialogVisible = ref(false)
const confirmingDeletion = ref(false)
const form = reactive({ name: '', description: '' })
const selectedProject = computed(() => state.projects.find(project => project.id === state.selectedProjectId))
const maskCount = computed(() => previewAssets(state, 'mask').length)
const partCount = computed(() => previewAssets(state, 'part').length)
const candidates = computed(() => previewAssets(state))
const selectedAsset = computed(() => candidates.value.find(asset => asset.id === state.previewAssetId))
const todayProjects = computed(() => state.projects.filter(project => new Date(project.created_at).toDateString() === new Date().toDateString()).length)

function shortDate(value) { return value ? new Date(value).toLocaleDateString('zh-CN') : '—' }
function formatDate(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '—' }
function enterProject() { if (selectedProject.value && !state.deletingProjectId) router.push(`/projects/${selectedProject.value.id}`) }
function refresh() { return controller.loadProjects(typeof route.query.project === 'string' ? route.query.project : '') }
async function submit() {
  if (state.creating) return
  if (!form.name.trim()) return ElMessage.warning('请输入项目名称')
  try {
    const project = await controller.createProject({ name: form.name.trim(), description: form.description })
    if (!project) return
    dialogVisible.value = false; form.name = ''; form.description = ''
    ElMessage.success('项目已创建')
    router.push(`/projects/${project.id}`)
  } catch (error) { ElMessage.error(errorDetail(error, '项目创建失败，已保留填写内容，请重试')) }
}
async function removeSelectedProject() {
  const project = selectedProject.value
  if (!project || state.deletingProjectId || confirmingDeletion.value) return
  confirmingDeletion.value = true
  try {
    await ElMessageBox.confirm(`确定删除项目“${project.name}”？项目内的所有素材、生成结果和任务记录也将删除，无法撤销。`, '删除项目', { confirmButtonText: '删除整个项目', cancelButtonText: '取消', type: 'warning', confirmButtonClass: 'el-button--danger', customClass: 'drafting-confirm' })
  } catch { return }
  finally { confirmingDeletion.value = false }
  try { if (await controller.removeProject(project.id)) ElMessage.success('项目已删除') }
  catch (error) { ElMessage.error(errorDetail(error, '项目删除失败，请稍后重试')) }
}
onMounted(refresh)
watch(() => state.selectedProjectId, id => {
  if (state.creating || route.path !== '/' || route.query.project === id || (!id && !route.query.project)) return
  const query = { ...route.query }
  if (id) query.project = id
  else delete query.project
  router.replace({ path: '/', query })
})
watch(() => route.query.project, id => {
  if (typeof id === 'string' && id !== state.selectedProjectId && state.projects.some(project => project.id === id)) controller.selectProject(id)
})
onBeforeUnmount(controller.dispose)
</script>

<style scoped>
.drafting-dashboard{--draft-ink:#252a30;--draft-muted:#636c5f;--draft-border:#d5d1c5;--draft-accent:#a85b21;width:min(calc(100% - 64px),1440px);margin:0 auto;display:grid;grid-template-columns:minmax(245px,292px) minmax(0,1fr);min-height:calc(100dvh - 72px);font-size:18px;line-height:1.6}.project-directory{padding:27px 22px 25px 0;border-right:1px solid var(--draft-border);min-width:0}.directory-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:20px}.directory-heading h1{margin:0;font:600 30px/1.4 var(--studio-font)}.directory-heading>span{white-space:nowrap;color:var(--draft-muted);font-size:16px}.create-project{width:100%;margin-bottom:20px;border-color:#c9c4b6;background:transparent;color:#475044}.project-options{display:flex;flex-direction:column;max-height:calc(100dvh - 270px);min-height:190px;overflow:auto;scrollbar-gutter:stable;gap:0}.project-option{width:100%;display:block;flex-shrink:0;padding:16px 12px;border:1px solid transparent;border-bottom-color:#dedacf;border-radius:0;background:transparent;text-align:left;color:var(--draft-ink);cursor:pointer;transition:background-color 140ms ease,border-color 140ms ease}.project-option:hover{background:#eeeae0}.project-option.selected{background:#eee5d7;border-color:#d6c6b2;border-radius:4px}.project-option:focus-visible{outline:2px solid var(--draft-accent);outline-offset:-3px}.project-option:disabled{cursor:wait}.option-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.option-heading strong{font-size:18px;font-weight:600;overflow-wrap:anywhere;line-height:1.5}.option-heading .el-icon{color:#8e806b;flex-shrink:0;margin-top:5px}.option-meta{display:flex;justify-content:space-between;gap:9px;margin-top:7px;font:16px/1.6 var(--studio-font);color:#626d60}.option-meta time{white-space:nowrap}.option-description{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:7px;color:#687060;font-size:16px;line-height:1.6}.directory-footer{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;margin:20px 12px 0;font-size:16px;color:var(--draft-muted)}.list-error{padding:12px;line-height:1.6;color:#9b4c38}.list-error p{margin:0 0 12px}.directory-loading{padding:35px 10px;display:flex;align-items:center;justify-content:center;gap:10px;color:var(--draft-muted)}.directory-empty{padding:32px 12px;color:var(--draft-muted);text-align:center}.directory-empty .el-icon{font-size:32px;color:#9e8d72}.directory-empty p{margin:12px 0 7px;font-weight:600;color:#475044}.directory-empty span{font-size:16px}.directory-refresh{width:100%;justify-content:flex-start;margin:0!important;padding:0;min-height:32px;color:#7f4d25;font-size:16px}
.selected-project{min-width:0;padding:27px 0 35px 30px;animation:sheet-enter 220ms ease-out}.selected-project-header{display:flex;align-items:center;justify-content:space-between;gap:24px;margin-bottom:22px}.project-title{min-width:0}.project-title h2{font:600 clamp(30px,2.5vw,36px)/1.35 var(--studio-font);letter-spacing:-.3px;margin:0 0 7px;overflow-wrap:anywhere}.project-id{font:16px/1.6 var(--studio-font);color:var(--draft-muted)}.enter-project{flex-shrink:0;min-height:40px;padding-inline:17px}.button-arrow{margin-left:4px;transition:transform 130ms ease}.enter-project:hover .button-arrow{transform:translateX(2px)}.enter-project:active{transform:translateY(1px)}.preview-sheet{border:1px solid #d7d2c5;background:#fffdf8;min-width:0}.preview-heading{display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap;min-height:53px;padding:10px 20px;border-bottom:1px solid #e9e4d9}.preview-heading h3{font-size:18px;font-weight:600;margin:0;color:#4b564a}.preview-tabs{position:relative;display:grid;grid-template-columns:1fr 1fr;width:188px;padding:2px;background:#f2eee5;border:1px solid #e0d9ca;border-radius:4px;isolation:isolate}.preview-tab-marker{position:absolute;inset:2px auto 2px 2px;width:calc(50% - 2px);border-radius:2px;background:#e9dbc6;z-index:-1;transition:transform 160ms ease-out}.preview-tab-marker.at-parts{transform:translateX(100%)}.preview-tabs button{border:0;background:transparent;min-height:27px;padding:1px 8px;color:#676e60;cursor:pointer;font-size:16px;white-space:nowrap}.preview-tabs button[aria-pressed="true"]{color:#82451b;font-weight:600}.preview-tabs button span{margin-left:4px;font-family:var(--studio-font)}.preview-tabs button:disabled{opacity:.55;cursor:default}.preview-tabs button:focus-visible{outline:2px solid var(--draft-accent);outline-offset:1px}.preview-note{font-size:16px;color:var(--draft-muted)}.preview-state{min-height:290px;padding:28px;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;color:var(--draft-muted)}.preview-state>.el-icon{font-size:32px;color:#998468}.preview-state h4{margin:14px 0 6px;font-size:18px;font-weight:600;color:#475044}.preview-state p{max-width:420px;margin:0 0 17px;font-size:18px;line-height:1.7}.preview-file{border-top:1px solid #eee8dc;min-height:53px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px 20px;padding:10px 20px;font-size:16px;color:var(--draft-muted)}.file-name{max-width:100%;overflow-wrap:anywhere;font-family:var(--studio-font)}.file-choice{display:flex;align-items:center;gap:9px;max-width:100%;margin-left:auto}.file-choice label{white-space:nowrap;font-size:16px}.file-choice :deep(.el-select){width:175px;max-width:100%}.file-choice :deep(.el-select__wrapper){border-radius:3px;background:#fffdf8;box-shadow:0 0 0 1px #d3ccbe inset}
.project-details{display:flex;align-items:flex-start;gap:22px;padding:21px 0;border-bottom:1px solid var(--draft-border)}.project-description{min-width:0;flex:1}.detail-label{display:block;color:var(--draft-muted);font-size:16px;margin-bottom:6px}.project-description p{margin:0;overflow-wrap:anywhere;color:#414c42;font-size:18px;line-height:1.7}.project-created{flex-shrink:0}.project-created time{color:#414c42;font:18px/1.7 var(--studio-font);white-space:nowrap}.delete-project{margin-left:auto;align-self:center;flex-shrink:0;color:#a05242;min-height:38px;padding-inline:0;font-size:16px}.project-workflow{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:19px}.project-workflow>span{font-size:16px;color:var(--draft-muted);white-space:nowrap}.project-workflow>div{display:flex;align-items:center;justify-content:flex-end;gap:13px;flex-wrap:wrap}.project-workflow a{display:inline-flex;align-items:center;gap:7px;min-height:38px;color:#4f5b4e;text-decoration:none;font-size:18px;border-bottom:1px solid transparent}.project-workflow a:hover{color:var(--draft-accent);border-bottom-color:#b57c4c}.project-workflow a:focus-visible{outline:2px solid var(--draft-accent);outline-offset:3px}.project-workflow a span{font:16px var(--studio-font);color:#a16d42}.project-workflow i{height:1px;width:20px;background:#c4bba9}.workspace-empty{min-height:490px;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;padding:40px 20px;color:var(--draft-muted)}.workspace-empty>.el-icon{font-size:48px;color:#9f8c6d}.workspace-empty h2{margin:20px 0 8px;font:600 30px/1.4 var(--studio-font);color:#333d34}.workspace-empty p{max-width:390px;margin:0 0 22px;font-size:18px;line-height:1.7}.loading-turn{animation:draft-turn 1s linear infinite}
:global(.drafting-dialog),:global(.drafting-confirm){--el-color-primary:#a85b21;--el-color-primary-light-9:#f5ece1;--el-color-primary-dark-2:#89481a;--el-border-radius-base:4px;color:#252a30;border-radius:5px;background:#fffdf8}:global(.drafting-dialog .el-dialog__title){font-family:var(--studio-font);font-size:26px}:global(.drafting-dialog .el-form-item__label){font-size:18px;color:#475044}:global(.drafting-dialog .el-button--primary),:global(.drafting-confirm .el-button--primary){box-shadow:none}:global(.drafting-confirm .el-button--danger){background:#a34e43;border-color:#a34e43;color:#fff}:global(.drafting-confirm .el-message-box__message){font-size:18px;line-height:1.7}
@keyframes sheet-enter{from{opacity:.4;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}@keyframes draft-turn{to{transform:rotate(360deg)}}
@media(max-width:1060px){.drafting-dashboard{grid-template-columns:minmax(210px,245px) minmax(0,1fr)}.project-directory{padding-right:18px}.selected-project{padding-left:22px}.project-details{flex-wrap:wrap;gap:17px}.project-description{flex-basis:100%}.project-created{margin-right:auto}.project-workflow{align-items:flex-start;flex-direction:column;gap:6px}.project-workflow>div{justify-content:flex-start}}
@media(max-width:760px){.drafting-dashboard{grid-template-columns:minmax(0,1fr)}.project-directory{padding:23px 0 22px;border-right:0;border-bottom:1px solid var(--draft-border)}.directory-heading{margin-bottom:15px}.project-options{max-height:240px;min-height:0}.create-project{margin-bottom:16px}.directory-footer{margin-top:15px}.selected-project{padding:24px 0 30px}.selected-project-header{align-items:flex-start;gap:16px}.project-title h2{font-size:30px}.preview-heading{padding-inline:14px}.preview-file{padding-inline:14px}.workspace-empty{min-height:280px}.preview-state{min-height:240px}}
@media(max-width:700px){.drafting-dashboard{width:calc(100% - 32px);min-height:0}}
@media(max-width:430px){.selected-project-header{flex-wrap:wrap}.enter-project{margin-left:auto}.file-choice{width:100%;margin-left:0}.file-choice :deep(.el-select){flex:1;width:auto;min-width:0}.project-workflow>div{gap:8px}.project-workflow i{width:10px}.project-workflow a{font-size:16px;gap:5px}}
@media(prefers-reduced-motion:reduce){.selected-project,.loading-turn{animation:none}.project-option,.preview-tab-marker,.button-arrow{transition:none}.enter-project:active,.enter-project:hover .button-arrow{transform:none}}
</style>
