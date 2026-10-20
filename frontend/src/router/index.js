import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../views/DraftingDashboard.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import WorkflowStep from '../views/WorkflowStep.vue'
import Tasks from '../views/Tasks.vue'
import Guide from '../views/Guide.vue'
import DatasetGallery from '../views/DatasetGallery.vue'
import DxfWorkspace from '../views/DxfWorkspace.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { title: '项目管理' } },
    { path: '/projects/:id', component: ProjectDetail, meta: { title: '项目工作台' } },
    { path: '/projects/:id/step/:step', component: WorkflowStep, meta: { title: '生成流程' } },
    { path: '/projects/:id/dxf', component: DxfWorkspace, meta: { title: 'DXF 预处理' } },
    { path: '/projects/:id/gallery', component: DatasetGallery, meta: { title: '生成结果阅览' } },
    { path: '/tasks', component: Tasks, meta: { title: '任务中心' } },
    { path: '/guide', component: Guide, meta: { title: '使用指引' } }
  ]
})

export default router
