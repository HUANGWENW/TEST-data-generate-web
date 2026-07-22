<template>
  <el-container class="shell">
    <el-aside width="240px" class="aside">
      <div class="brand">
        <div class="brand-mark">P</div>
        <div><strong>零件数据</strong><span>生成控制台</span></div>
      </div>
      <div class="nav-caption">WORKSPACE</div>
      <el-menu router :default-active="$route.path" class="menu" background-color="transparent" text-color="#94a3b8" active-text-color="#ffffff">
        <el-menu-item index="/"><el-icon><Folder /></el-icon><span>项目总览</span></el-menu-item>
        <el-menu-item index="/tasks"><el-icon><Operation /></el-icon><span>任务中心</span></el-menu-item>
        <el-menu-item index="/guide"><el-icon><Reading /></el-icon><span>使用指引</span></el-menu-item>
      </el-menu>
      <div class="aside-status">
        <div><i></i><strong>系统运行正常</strong></div>
        <span>FastAPI · Redis · RQ</span>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title"><span>PARTS DATA STUDIO</span><strong>{{ $route.meta.title || '工作台' }}</strong></div>
        <div class="header-actions">
          <div class="header-health"><i></i>服务在线</div>
          <div class="operator"><span>操作员</span><strong>01</strong></div>
        </div>
      </el-header>
      <el-main class="workspace-main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.shell { min-height: 100vh; background: #f3f6fa; }
.aside { position: sticky; top: 0; z-index: 10; display: flex; flex-direction: column; height: 100vh; color: #fff; background: #0f172a; box-shadow: 8px 0 30px rgb(15 23 42 / 9%); }
.brand { display: flex; align-items: center; gap: 12px; height: 76px; padding: 0 20px; border-bottom: 1px solid rgb(148 163 184 / 13%); }
.brand-mark { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 9px; background: #2563eb; box-shadow: 0 7px 18px rgb(37 99 235 / 30%); font-size: 18px; font-weight: 800; }
.brand strong,.brand span { display: block; }
.brand strong { font-size: 15px; letter-spacing: .02em; }
.brand span { margin-top: 3px; color: #94a3b8; font-size: 11px; }
.nav-caption { padding: 24px 22px 9px; color: #64748b; font-size: 10px; font-weight: 700; letter-spacing: .14em; }
.menu { padding: 0 12px; border-right: none; }
.menu :deep(.el-menu-item) { height: 46px; margin: 4px 0; border-radius: 8px; }
.menu :deep(.el-menu-item:hover) { color: #e2e8f0; background: rgb(255 255 255 / 6%); }
.menu :deep(.el-menu-item.is-active) { background: #2563eb; box-shadow: 0 7px 18px rgb(37 99 235 / 24%); }
.menu :deep(.el-menu-item .el-icon) { font-size: 17px; }
.aside-status { padding: 14px; margin: auto 16px 18px; border: 1px solid rgb(148 163 184 / 12%); border-radius: 10px; background: #162238; }
.aside-status div { display: flex; align-items: center; gap: 8px; }
.aside-status i,.header-health i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 4px rgb(34 197 94 / 13%); }
.aside-status strong { font-size: 12px; }
.aside-status span { display: block; margin-top: 9px; color: #94a3b8; font-size: 10px; }
.header { display: flex; align-items: center; justify-content: space-between; height: 72px; padding: 0 28px; border-bottom: 1px solid #e2e8f0; background: rgb(255 255 255 / 94%); backdrop-filter: blur(12px); }
.header-title span,.header-title strong { display: block; }
.header-title span { margin-bottom: 3px; color: #94a3b8; font-size: 9px; font-weight: 700; letter-spacing: .13em; }
.header-title strong { color: #172033; font-size: 16px; }
.header-actions { display: flex; align-items: center; gap: 16px; }
.header-health { display: flex; align-items: center; gap: 8px; padding: 7px 11px; border: 1px solid #dcefe2; border-radius: 999px; color: #15803d; background: #f0fdf4; font-size: 11px; font-weight: 600; }
.operator { display: flex; align-items: center; gap: 9px; color: #64748b; font-size: 11px; }
.operator strong { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 50%; color: #fff; background: #334155; font-size: 11px; }
.workspace-main { padding: 0; overflow: visible; }

@media (max-width: 700px) {
  .shell { flex-direction: column; }
  .aside { position: static; display: flex; align-items: stretch; width: 100% !important; min-height: 52px; height: auto; background: #0f172a; }
  .brand { flex: 0 0 auto; height: 52px; padding: 0 13px; white-space: nowrap; }
  .brand-mark { width: 30px; height: 30px; font-size: 14px; }
  .brand span,.nav-caption,.aside-status { display: none; }
  .menu { display: flex; flex: 1; min-width: 0; }
  .menu :deep(.el-menu-item) { flex: 1; justify-content: center; min-width: 0; height: 44px; padding: 0 8px; }
  .menu :deep(.el-menu-item span) { overflow: hidden; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
  .shell > .el-container { width: 100%; }
  .header { height: 54px; padding: 0 14px; }
  .header-title span,.header-health,.operator > span { display: none; }
}
</style>
