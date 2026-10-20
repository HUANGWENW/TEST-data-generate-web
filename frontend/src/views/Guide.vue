<template>
  <div class="page guide-page">
    <div class="toolbar">
      <div>
        <h2>使用指引</h2>
        <div class="muted">按素材、Mask、透明零件、合成数据集的顺序完成一次生成，也可从已有 Mask 或透明零件直接开始。</div>
      </div>
      <el-button type="primary" :icon="FolderOpened" @click="$router.push('/')">进入项目</el-button>
    </div>

    <section class="guide-overview" aria-label="生成流程总览">
      <div class="overview-copy"><span class="eyebrow">推荐顺序</span><h3>从来源文件到可阅览的数据集</h3><p>每一步完成后先检查并勾选合格结果，再进入下一步。</p></div>
      <div class="overview-flow">
        <template v-for="(item, index) in flowItems" :key="item.number">
          <div class="overview-node"><span>{{ item.number }}</span><strong>{{ item.title }}</strong><small>{{ item.output }}</small></div>
          <el-icon v-if="index < flowItems.length - 1" class="overview-arrow"><ArrowRight /></el-icon>
        </template>
      </div>
    </section>

    <section class="guide-list" aria-label="分步操作说明">
      <article class="guide-step source-step">
        <div class="step-copy">
          <div class="step-kicker"><span>准备</span><em>01</em></div>
          <h3>上传并整理素材</h3>
          <p>在项目首页先准备来源文件、背景图和纹理图。已有黑白 Mask 时，选择“已有 Mask”即可跳过第一步。</p>
          <ol class="action-list">
            <li><b>入口</b><span>项目首页的“素材上传”。</span></li>
            <li><b>选择</b><span>GEN 文件或白色边缘图；也可切换为已有 Mask。</span></li>
            <li><b>上传</b><span>背景图会显示像素尺寸，文件夹按钮可批量添加来源文件。</span></li>
          </ol>
          <div class="step-result"><el-icon><CircleCheck /></el-icon><span>输出：可在后续步骤选择的输入、Mask、背景和纹理资产。</span></div>
        </div>
        <div class="guide-visual source-visual" role="img" aria-label="素材上传界面示意">
          <div class="mock-window">
            <div class="mock-titlebar"><i></i><i></i><i></i><span>素材上传</span></div>
            <div class="mock-body">
              <div class="mock-tabs"><span class="selected">第一步：GEN / 边缘图</span><span>已有 Mask</span></div>
              <div class="mock-upload"><div class="file-token">GEN</div><div><strong>选择输入文件</strong><small>支持文件夹批量上传</small></div><button type="button" tabindex="-1" aria-hidden="true">上传</button></div>
              <div class="mock-assets"><span>背景图</span><span>纹理图</span><span>DXF 预处理</span></div>
            </div>
          </div>
          <div class="callout callout-one"><b>1</b><span>选来源</span></div>
          <div class="callout callout-two"><b>2</b><span>选类型</span></div>
          <div class="callout callout-three"><b>3</b><span>上传</span></div>
        </div>
      </article>

      <article class="guide-step mask-step">
        <div class="step-copy">
          <div class="step-kicker"><span>第一步</span><em>02</em></div>
          <h3>提取并验收 Mask</h3>
          <p>从 GEN 文件或边缘图中提取轮廓。边缘图模式只需根据图像断线情况调整膨胀核，默认值适合大多数输入。</p>
          <ol class="action-list">
            <li><b>入口</b><span>生成流程中的“1. 提取 Mask”。</span></li>
            <li><b>提取</b><span>选择输入文件和提取方式，然后提交 Mask 提取任务。</span></li>
            <li><b>验收</b><span>保留外轮廓完整、内部孔洞正确的 Mask，不需要的可取消勾选或删除。</span></li>
          </ol>
          <div class="step-result"><el-icon><CircleCheck /></el-icon><span>输出：已勾选的 Mask，可直接进入第二步。</span></div>
        </div>
        <div class="guide-visual mask-visual" role="img" aria-label="Mask 提取与验收界面示意">
          <div class="mock-window">
            <div class="mock-titlebar"><i></i><i></i><i></i><span>提取 Mask</span></div>
            <div class="mock-body">
              <div class="mask-controls"><span class="input-bar">选择输入文件</span><span class="mode-chip selected">GEN 文件</span><span class="mode-chip">边缘图</span><button type="button" tabindex="-1" aria-hidden="true">提交提取</button></div>
              <div class="mask-review"><div class="mask-tile checked"><i class="mask-shape shape-a"></i><b>✓</b></div><div class="mask-tile checked"><i class="mask-shape shape-b"></i><b>✓</b></div><div class="mask-tile"><i class="mask-shape shape-c"></i></div></div>
            </div>
          </div>
          <div class="callout callout-one"><b>1</b><span>选方式</span></div>
          <div class="callout callout-two"><b>2</b><span>提交提取</span></div>
          <div class="callout callout-three"><b>3</b><span>勾选合格 Mask</span></div>
        </div>
      </article>

      <article class="guide-step part-step">
        <div class="step-copy">
          <div class="step-kicker"><span>第二步</span><em>03</em></div>
          <h3>生成并筛选透明零件</h3>
          <p>将选中的 Mask 与纹理图组合成 RGBA 零件。纹理尺寸较小时，可选原尺寸裁剪/平铺，或拉伸宽高填满轮廓。</p>
          <ol class="action-list">
            <li><b>入口</b><span>生成流程中的“2. 生成透明零件”。</span></li>
            <li><b>选择</b><span>勾选 Mask 和纹理图，选择裁剪/平铺或拉伸宽高，并设置输出最长边。</span></li>
            <li><b>验收</b><span>在棋盘格预览中保留边缘干净、纹理合适的透明零件。</span></li>
          </ol>
          <div class="step-result"><el-icon><CircleCheck /></el-icon><span>输出：已勾选的 RGBA 零件，可直接用于合成。</span></div>
        </div>
        <div class="guide-visual part-visual" role="img" aria-label="透明零件生成与验收界面示意">
          <div class="mock-window">
            <div class="mock-titlebar"><i></i><i></i><i></i><span>生成透明零件</span></div>
            <div class="mock-body part-body">
              <div class="texture-swatch"><span>纹理图</span></div><el-icon class="conversion-arrow"><ArrowRight /></el-icon><div class="rgba-piece"><i></i></div>
              <div class="part-options"><span>纹理填充</span><em>拉伸宽高</em><button type="button" tabindex="-1" aria-hidden="true">生成透明零件</button></div>
              <div class="part-review"><div class="piece-tile selected"><i></i><b>✓</b></div><div class="piece-tile"><i></i></div><div class="piece-tile"><i></i></div></div>
            </div>
          </div>
          <div class="callout callout-one"><b>1</b><span>选纹理</span></div>
          <div class="callout callout-two"><b>2</b><span>生成 RGBA</span></div>
          <div class="callout callout-three"><b>3</b><span>筛选零件</span></div>
        </div>
      </article>

      <article class="guide-step dataset-step">
        <div class="step-copy">
          <div class="step-kicker"><span>第三步</span><em>04</em></div>
          <h3>合成数据并阅览结果</h3>
          <p>选择背景、零件和标签格式后创建任务。边距预览中的青色虚线框就是零件能够放置的范围；完成后进入图库查看图片与 TXT。</p>
          <ol class="action-list">
            <li><b>选择</b><span>设置背景、YOLO/COCO 标签、布局、数量、旋转和缩放范围。</span></li>
            <li><b>预览</b><span>调整上下、左右边距，确认背景中的青色可放置区域。</span></li>
            <li><b>阅览</b><span>在任务中心或结果图库下载合成图、标签 TXT 和生成信息 TXT。</span></li>
          </ol>
          <div class="step-result"><el-icon><CircleCheck /></el-icon><span>输出：合成图片、标签、逐图生成信息和可下载的索引文件。</span></div>
        </div>
        <div class="guide-visual dataset-visual" role="img" aria-label="数据集合成与结果阅览界面示意">
          <div class="mock-window">
            <div class="mock-titlebar"><i></i><i></i><i></i><span>合成数据集与标签</span></div>
            <div class="mock-body dataset-body">
              <div class="dataset-form"><span>背景图</span><span>YOLO HBB</span><span>随机放置</span><button type="button" tabindex="-1" aria-hidden="true">生成数据集</button></div>
              <div class="placement-demo"><div class="safe-area"><i></i><b></b><em></em><small>可放置区域</small></div></div>
              <div class="output-files"><div class="output-image"><i></i></div><span>synthetic.jpg</span><span>labels.txt</span><span>metadata.txt</span></div>
            </div>
          </div>
          <div class="callout callout-one"><b>1</b><span>设定参数</span></div>
          <div class="callout callout-two"><b>2</b><span>查看放置区域</span></div>
          <div class="callout callout-three"><b>3</b><span>阅览与下载</span></div>
        </div>
      </article>
    </section>

    <section class="guide-note">
      <el-icon><InfoFilled /></el-icon><span>任务中心显示进度和各阶段耗时；数据生成完成后，可在结果图库中逐张预览并下载合成图、标签 TXT 和生成信息 TXT。</span>
    </section>
  </div>
</template>

<script setup>
import { ArrowRight, CircleCheck, FolderOpened, InfoFilled } from '@element-plus/icons-vue'

const flowItems = [
  { number: '01', title: '上传素材', output: '输入 / 背景 / 纹理' },
  { number: '02', title: '提取 Mask', output: '验收后勾选' },
  { number: '03', title: '透明零件', output: 'RGBA 预览' },
  { number: '04', title: '合成与阅览', output: '图片 / 标签 / 信息' },
]
</script>

<style scoped>
.guide-page { max-width: 1320px; }
.guide-overview { display: grid; grid-template-columns: minmax(230px, .8fr) minmax(0, 1.8fr); gap: 30px; align-items: center; margin-bottom: 32px; padding: 24px 0; border-block: 1px solid var(--studio-border); }
.eyebrow, .step-kicker span { color: var(--studio-primary); font-size: 13px; font-weight: 600; }
.overview-copy h3 { margin: 6px 0 10px; font: 600 23px/1.4 var(--studio-serif); }
.overview-copy p { margin: 0; color: var(--studio-muted); font-size: 14px; line-height: 1.7; }
.overview-flow { display: flex; align-items: center; gap: 12px; }
.overview-node { flex: 1; min-width: 0; }
.overview-node > span { display: block; margin-bottom: 10px; color: var(--studio-primary); font: 14px var(--studio-mono); }
.overview-node strong { display: block; color: var(--studio-text); font-size: 15px; }
.overview-node small { display: block; margin-top: 6px; color: var(--studio-muted); font-size: 13px; line-height: 1.6; }
.overview-arrow { flex: 0 0 16px; color: #9a9586; }
.guide-list { display: flex; flex-direction: column; gap: 28px; }
.guide-step { display: grid; grid-template-columns: minmax(290px, .85fr) minmax(0, 1.15fr); gap: 32px; align-items: center; padding: 28px; border: 1px solid var(--studio-border); background: var(--studio-surface); border-radius: 4px; }
.step-kicker { display: flex; align-items: center; gap: 12px; }
.step-kicker em { font: 14px var(--studio-mono); color: #948975; }
.step-copy h3 { margin: 9px 0 12px; font: 600 26px/1.4 var(--studio-serif); }
.step-copy > p { margin: 0 0 18px; color: #475044; font-size: 14px; line-height: 1.8; }
.action-list { display: grid; gap: 9px; margin: 0; padding: 0; list-style: none; }
.action-list li { display: grid; grid-template-columns: 32px 1fr; gap: 10px; color: var(--studio-muted); font-size: 13px; line-height: 1.7; }
.action-list b { color: #475044; font-weight: 600; }
.step-result { display: flex; gap: 8px; align-items: flex-start; margin-top: 20px; padding-top: 15px; border-top: 1px solid var(--el-border-color-light); color: #4e785c; font-size: 13px; line-height: 1.7; }
.step-result .el-icon { margin-top: 3px; flex-shrink: 0; font-size: 15px; }
.guide-visual { position: relative; min-width: 0; padding: 24px 22px 38px; background: var(--studio-bg); border: 1px solid var(--el-border-color-light); }
.mock-window { overflow: hidden; border: 1px solid #bbb4a3; background: #fffdf8; }
.mock-titlebar { display: flex; align-items: center; gap: 5px; min-height: 32px; padding: 0 10px; border-bottom: 1px solid #d5d1c5; background: #ede9de; color: #475044; font-size: 12px; }
.mock-titlebar i { width: 5px; height: 5px; border-radius: 50%; background: #aaa08c; }
.mock-titlebar span { margin-left: 6px; }
.mock-body { padding: 14px; }
.mock-tabs { display: flex; gap: 6px; border-bottom: 1px solid #e2ded3; padding-bottom: 10px; }
.mock-tabs span, .mode-chip { padding: 4px 6px; border: 1px solid #d5d1c5; color: #636c5f; font-size: 12px; }
.mock-tabs .selected, .mode-chip.selected { border-color: #a85b21; background: #f5ece1; color: #89481a; }
.mock-upload { display: flex; align-items: center; gap: 10px; margin-top: 14px; padding: 10px; border: 1px dashed #b7b2a4; }
.mock-upload > div { min-width: 0; }
.file-token { display: grid; flex: 0 0 34px; place-items: center; height: 34px; background: #252a30; color: #eee9dc; font: 12px var(--studio-mono); }
.mock-upload strong, .mock-upload small { display: block; font-size: 12px; line-height: 1.6; }
.mock-upload strong { color: #475044; }
.mock-upload small { margin-top: 3px; color: #636c5f; }
.mock-window button { flex-shrink: 0; margin-left: auto; border: 0; border-radius: 2px; background: #a85b21; color: #fff; padding: 6px 8px; font-size: 12px; }
.mock-assets { display: flex; gap: 7px; margin-top: 14px; }
.mock-assets span { flex: 1; padding: 8px 5px; background: #f1eee5; color: #636c5f; font-size: 12px; text-align: center; }
.callout { position: absolute; display: flex; align-items: center; gap: 5px; color: #636c5f; font-size: 12px; white-space: nowrap; }
.callout b { display: grid; place-items: center; width: 19px; height: 19px; border-radius: 50%; background: #a85b21; color: #fff; font: 12px var(--studio-mono); }
.callout-one { top: 10px; left: 10px; }
.callout-two { top: 63px; right: 7px; }
.callout-three { bottom: 8px; left: 50%; transform: translateX(-50%); }
.mask-controls { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; }
.input-bar { flex: 1 1 100%; padding: 6px; border: 1px solid #d5d1c5; color: #636c5f; font-size: 12px; }
.mask-controls button { margin-left: auto; }
.mask-review { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; margin-top: 14px; }
.mask-tile { position: relative; height: 70px; border: 1px solid #d5d1c5; background: #fff; }
.mask-tile.checked { border-color: #a85b21; }
.mask-tile b, .piece-tile b { position: absolute; right: 4px; top: 4px; display: grid; place-items: center; width: 15px; height: 15px; border-radius: 2px; background: #a85b21; color: #fff; font-size: 12px; }
.mask-shape { position: absolute; display: block; background: #252a30; }
.shape-a { width: 55%; height: 42%; left: 20%; top: 28%; border-radius: 42% 58% 46% 34%; box-shadow: inset -10px 0 #fff; }
.shape-b { width: 60%; height: 58%; left: 18%; top: 24%; clip-path: polygon(0 0, 100% 8%, 82% 100%, 10% 78%); }
.shape-c { width: 52%; height: 42%; left: 23%; top: 28%; border-radius: 50%; background: #a2a396; }
.part-body { display: grid; grid-template-columns: 1fr 22px 1fr; gap: 10px; align-items: center; }
.texture-swatch, .rgba-piece, .piece-tile { background: repeating-conic-gradient(#e2e1da 0% 25%, #fff 0% 50%) 50% / 14px 14px; }
.texture-swatch { display: grid; place-items: center; height: 76px; background: #858c7c; color: #fff; font-size: 12px; box-shadow: inset 0 -22px rgb(37 42 48 / 15%); }
.conversion-arrow { color: #95856f; }
.rgba-piece { position: relative; height: 76px; }
.rgba-piece i, .piece-tile i { position: absolute; display: block; width: 57%; height: 48%; left: 21%; top: 25%; border-radius: 38% 58% 41% 47%; background: #8d9681; transform: rotate(-13deg); box-shadow: inset -9px -6px #68725e; }
.part-options { grid-column: 1 / -1; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 3px; color: #636c5f; font-size: 12px; }
.part-options em { padding: 3px 6px; border: 1px solid #d1a47f; background: #f5ece1; color: #89481a; font-style: normal; }
.part-review { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; margin-top: 5px; }
.piece-tile { position: relative; height: 48px; border: 1px solid #d5d1c5; }
.piece-tile.selected { border-color: #a85b21; }
.piece-tile i { width: 39%; height: 46%; left: 30%; top: 26%; }
.dataset-body { display: grid; grid-template-columns: 94px 1fr; gap: 10px; }
.dataset-form { display: grid; align-content: start; gap: 7px; }
.dataset-form span { padding: 6px; background: #f1eee5; color: #636c5f; font-size: 12px; }
.dataset-form button { margin: 0; padding: 7px 4px; font-size: 12px; }
.placement-demo { position: relative; height: 146px; background: #bdc3ac; border: 1px solid #9da98d; box-shadow: inset 0 44px #e2e5de; }
.safe-area { position: absolute; inset: 17px 12px 20px; border: 2px dashed #0891b2; background: rgb(34 211 238 / 10%); }
.safe-area i, .safe-area b, .safe-area em { position: absolute; display: block; background: #5e827a; transform: rotate(-13deg); }
.safe-area i { width: 21px; height: 16px; left: 26%; top: 44%; }
.safe-area b { width: 18px; height: 14px; left: 56%; top: 35%; background: #b98655; }
.safe-area em { width: 16px; height: 18px; right: 14%; bottom: 20%; background: #7d9275; }
.safe-area small { position: absolute; left: 4px; top: 4px; padding: 2px 4px; background: #087d96; color: #fff; font-size: 12px; }
.output-files { grid-column: 1 / -1; display: flex; flex-wrap: wrap; align-items: center; gap: 7px; margin-top: 3px; color: #636c5f; font: 12px var(--studio-mono); }
.output-image { position: relative; width: 38px; height: 25px; background: #bdc3ac; border: 1px solid #9da98d; box-shadow: inset 0 9px #e2e5de; }
.output-image i { position: absolute; width: 9px; height: 7px; left: 14px; top: 11px; background: #5e827a; transform: rotate(-14deg); }
.guide-note { display: flex; gap: 12px; align-items: flex-start; margin-top: 28px; padding: 18px 0; border-top: 1px solid var(--studio-border); color: var(--studio-muted); font-size: 14px; line-height: 1.7; }
.guide-note .el-icon { flex: 0 0 auto; margin-top: 3px; color: var(--studio-primary); font-size: 18px; }
@media (max-width: 1060px) { .guide-overview, .guide-step { grid-template-columns: minmax(0, 1fr); } .guide-visual { max-width: 620px; } .overview-flow { justify-content: space-between; } }
@media (max-width: 620px) {
  .guide-step { padding: 18px; gap: 24px; }
  .overview-flow { display: grid; grid-template-columns: 1fr 18px 1fr; gap: 16px; }
  .overview-arrow:nth-of-type(2) { display: none; }
  .overview-arrow { align-self: center; }
  .guide-visual { padding: 28px 8px 38px; }
  .mock-body { padding: 10px; }
  .callout-two { top: 64px; }
  .dataset-body { grid-template-columns: 78px minmax(0, 1fr); }
  .dataset-form span, .dataset-form button { padding: 6px 3px; }
  .mock-upload { flex-wrap: wrap; }
  .part-options button { margin-left: 0; }
}
</style>
