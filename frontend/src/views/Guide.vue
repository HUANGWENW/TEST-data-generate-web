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
              <div class="mock-upload"><div class="file-token">GEN</div><div><strong>选择输入文件</strong><small>支持文件夹批量上传</small></div><button>上传</button></div>
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
            <li><b>验收</b><span>保留外轮廓完整、内部孔洞正确的 Mask，取消勾选不合格项。</span></li>
          </ol>
          <div class="step-result"><el-icon><CircleCheck /></el-icon><span>输出：已勾选的 Mask，可直接进入第二步。</span></div>
        </div>
        <div class="guide-visual mask-visual" role="img" aria-label="Mask 提取与验收界面示意">
          <div class="mock-window">
            <div class="mock-titlebar"><i></i><i></i><i></i><span>提取 Mask</span></div>
            <div class="mock-body">
              <div class="mask-controls"><span class="input-bar">选择输入文件</span><span class="mode-chip selected">GEN 文件</span><span class="mode-chip">边缘图</span><button>提交提取</button></div>
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
          <p>将选中的 Mask 与纹理图组合成 RGBA 零件。随机裁剪开启时，同一纹理可产生不同的表面区域。</p>
          <ol class="action-list">
            <li><b>入口</b><span>生成流程中的“2. 生成透明零件”。</span></li>
            <li><b>选择</b><span>勾选 Mask，选择纹理图，再决定是否随机裁剪。</span></li>
            <li><b>验收</b><span>在棋盘格预览中保留边缘干净、纹理合适的透明零件。</span></li>
          </ol>
          <div class="step-result"><el-icon><CircleCheck /></el-icon><span>输出：已勾选的 RGBA 零件，可直接用于合成。</span></div>
        </div>
        <div class="guide-visual part-visual" role="img" aria-label="透明零件生成与验收界面示意">
          <div class="mock-window">
            <div class="mock-titlebar"><i></i><i></i><i></i><span>生成透明零件</span></div>
            <div class="mock-body part-body">
              <div class="texture-swatch"><span>纹理图</span></div><el-icon class="conversion-arrow"><ArrowRight /></el-icon><div class="rgba-piece"><i></i></div>
              <div class="part-options"><span>随机裁剪</span><b></b><button>生成透明零件</button></div>
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
          <p>选择背景、零件和标签格式后创建任务。边距预览中的蓝框就是零件能够放置的范围；完成后进入图库查看图片与 TXT。</p>
          <ol class="action-list">
            <li><b>选择</b><span>设置背景、YOLO/COCO 标签、布局、数量、旋转和缩放范围。</span></li>
            <li><b>预览</b><span>调整上下、左右边距，确认背景中的蓝色可放置区域。</span></li>
            <li><b>阅览</b><span>在任务中心或结果图库下载合成图、标签 TXT 和生成信息 TXT。</span></li>
          </ol>
          <div class="step-result"><el-icon><CircleCheck /></el-icon><span>输出：合成图片、标签、逐图生成信息和可下载的索引文件。</span></div>
        </div>
        <div class="guide-visual dataset-visual" role="img" aria-label="数据集合成与结果阅览界面示意">
          <div class="mock-window">
            <div class="mock-titlebar"><i></i><i></i><i></i><span>合成数据集与标签</span></div>
            <div class="mock-body dataset-body">
              <div class="dataset-form"><span>背景图</span><span>YOLO HBB</span><span>随机放置</span><button>生成数据集</button></div>
              <div class="placement-demo"><div class="safe-area"><i></i><b></b><em></em><small>可放置区域</small></div></div>
              <div class="output-files"><div class="output-image"><i></i></div><span>synthetic.jpg</span><span>labels.txt</span><span>metadata.txt</span></div>
            </div>
          </div>
          <div class="callout callout-one"><b>1</b><span>设定参数</span></div>
          <div class="callout callout-two"><b>2</b><span>查看蓝框区域</span></div>
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
.guide-page{max-width:1180px}.guide-overview{display:grid;grid-template-columns:minmax(230px,.8fr) minmax(0,1.8fr);gap:28px;align-items:center;margin-bottom:28px;padding:22px 24px;border:1px solid #dfe7f1;background:#fff}.eyebrow,.step-kicker span{color:#277ac1;font-size:12px;font-weight:700}.overview-copy h3{margin:5px 0 8px;font-size:19px}.overview-copy p{margin:0;color:#64748b;font-size:13px;line-height:1.6}.overview-flow{display:flex;align-items:center;gap:8px}.overview-node{flex:1;min-width:0}.overview-node>span{display:block;margin-bottom:7px;color:#5b8fc3;font-size:12px;font-family:Consolas,monospace}.overview-node strong{display:block;color:#24364b;font-size:14px}.overview-node small{display:block;margin-top:5px;color:#7b8797;font-size:11px;line-height:1.4}.overview-arrow{flex:0 0 16px;color:#9badc1}.guide-list{display:flex;flex-direction:column;gap:22px}.guide-step{display:grid;grid-template-columns:minmax(290px,.85fr) minmax(480px,1.15fr);gap:28px;align-items:center;padding:24px;border:1px solid #e0e7f0;background:#fff}.guide-step:nth-child(even) .step-copy{order:2}.step-kicker{display:flex;align-items:center;gap:10px}.step-kicker em{font-style:normal;color:#a5b3c2;font:700 12px Consolas,monospace}.step-copy h3{margin:8px 0 9px;color:#1f2f43;font-size:21px}.step-copy>p{margin:0 0 15px;color:#586779;font-size:13px;line-height:1.75}.action-list{display:grid;gap:8px;margin:0;padding:0;list-style:none}.action-list li{display:grid;grid-template-columns:44px 1fr;gap:8px;color:#5e6d7e;font-size:12px;line-height:1.6}.action-list b{color:#334b63;font-size:12px}.step-result{display:flex;gap:7px;align-items:flex-start;margin-top:16px;padding-top:13px;border-top:1px solid #edf1f5;color:#397058;font-size:12px;line-height:1.5}.step-result .el-icon{margin-top:1px;color:#39a46a;font-size:15px}.guide-visual{position:relative;min-width:0;padding:16px 22px 30px;background:#f6f8fb;border:1px solid #e4eaf2}.mock-window{overflow:hidden;border:1px solid #cfdbe8;background:#fff;box-shadow:0 8px 18px rgba(48,69,94,.08)}.mock-titlebar{display:flex;align-items:center;gap:5px;height:28px;padding:0 10px;background:#1c2b3c;color:#e7f0fa;font-size:11px}.mock-titlebar i{width:5px;height:5px;border-radius:50%;background:#8ba2ba}.mock-titlebar span{margin-left:5px}.mock-body{padding:13px}.mock-tabs{display:flex;gap:5px;border-bottom:1px solid #e6ecf3;padding-bottom:9px}.mock-tabs span,.mode-chip{padding:4px 6px;border:1px solid #dce6f0;color:#728094;font-size:10px}.mock-tabs .selected,.mode-chip.selected{border-color:#409eff;background:#edf6ff;color:#277ac1}.mock-upload{display:flex;align-items:center;gap:10px;margin-top:12px;padding:9px;border:1px dashed #a9bed4}.file-token{display:grid;place-items:center;width:30px;height:30px;background:#202f43;color:#72d4a0;font:700 9px Consolas,monospace}.mock-upload strong,.mock-upload small{display:block;font-size:10px}.mock-upload strong{color:#405165}.mock-upload small{margin-top:3px;color:#97a5b3}.mock-window button{margin-left:auto;border:0;background:#409eff;color:#fff;padding:5px 8px;font-size:10px}.mock-assets{display:flex;gap:7px;margin-top:12px}.mock-assets span{flex:1;padding:8px 5px;background:#f1f5f9;color:#617286;font-size:10px;text-align:center}.callout{position:absolute;display:flex;align-items:center;gap:5px;color:#4b627a;font-size:10px;white-space:nowrap}.callout b{display:grid;place-items:center;width:18px;height:18px;border-radius:50%;background:#3287d8;color:#fff;font-size:11px}.callout-one{top:42px;left:10px}.callout-two{top:108px;right:10px}.callout-three{bottom:7px;left:50%;transform:translateX(-50%)}.mask-controls{display:flex;align-items:center;gap:5px}.input-bar{flex:1;padding:6px;border:1px solid #dce6f0;color:#99a7b4;font-size:10px}.mask-controls button{margin-left:3px}.mask-review{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:13px}.mask-tile{position:relative;height:63px;border:1px solid #dce5ee;background:#fafcff}.mask-tile.checked{border-color:#7db8ef}.mask-tile b,.piece-tile b{position:absolute;right:4px;top:4px;display:grid;place-items:center;width:13px;height:13px;border-radius:2px;background:#409eff;color:#fff;font-size:10px}.mask-shape{position:absolute;display:block;background:#253142}.shape-a{width:52px;height:32px;left:18px;top:15px;border-radius:42% 58% 46% 34%;box-shadow:inset -12px 0 #fff}.shape-b{width:54px;height:40px;left:15px;top:12px;border-radius:47% 33% 54% 45%;clip-path:polygon(0 0,100% 8%,82% 100%,10% 78%)}.shape-c{width:48px;height:27px;left:18px;top:18px;border-radius:50%;background:#9caaba}.part-body{display:grid;grid-template-columns:1fr 22px 1fr;gap:9px;align-items:center}.texture-swatch,.rgba-piece,.piece-tile{background:repeating-conic-gradient(#e6ebf1 0% 25%,#fff 0% 50%) 50% / 14px 14px}.texture-swatch{display:grid;place-items:center;height:69px;background:#63859c;color:#fff;font-size:10px;box-shadow:inset 0 -22px rgba(39,64,79,.25)}.conversion-arrow{color:#6f91b1}.rgba-piece{position:relative;height:69px}.rgba-piece i,.piece-tile i{position:absolute;display:block;width:57%;height:48%;left:21%;top:25%;border-radius:38% 58% 41% 47%;background:#4694cc;transform:rotate(-13deg);box-shadow:inset -9px -6px #276da6}.part-options{grid-column:1/-1;display:flex;align-items:center;gap:7px;margin-top:2px;color:#617286;font-size:10px}.part-options b{width:23px;height:12px;border-radius:7px;background:#409eff}.part-options b::after{content:'';display:block;width:8px;height:8px;margin:2px 2px 0 auto;border-radius:50%;background:#fff}.part-review{grid-column:1/-1;display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:4px}.piece-tile{position:relative;height:38px;border:1px solid #dce5ee}.piece-tile.selected{border-color:#7db8ef}.piece-tile i{width:39%;height:46%;left:30%;top:26%}.dataset-body{display:grid;grid-template-columns:82px 1fr;gap:10px}.dataset-form{display:grid;align-content:start;gap:6px}.dataset-form span{padding:6px;background:#f1f5f9;color:#627487;font-size:9px}.dataset-form button{margin:0;padding:7px 4px;font-size:9px}.placement-demo{position:relative;height:104px;background:#bed0ac;border:1px solid #9eb490;box-shadow:inset 0 38px #dbe8f0}.safe-area{position:absolute;inset:17px 12px 20px;border:2px solid #409eff;background:rgba(64,158,255,.12)}.safe-area i,.safe-area b,.safe-area em{position:absolute;display:block;background:#3e88c4;transform:rotate(-13deg)}.safe-area i{width:21px;height:16px;left:26%;top:34%}.safe-area b{width:18px;height:14px;left:56%;top:24%;background:#d78540}.safe-area em{width:16px;height:18px;right:14%;bottom:22%;background:#4d9c82}.safe-area small{position:absolute;left:4px;top:4px;padding:2px 4px;background:#3183cd;color:#fff;font-size:8px}.output-files{grid-column:1/-1;display:flex;align-items:center;gap:7px;margin-top:2px;color:#67788b;font:10px Consolas,monospace}.output-image{position:relative;width:38px;height:25px;background:#bfd0ad;border:1px solid #a2b58f;box-shadow:inset 0 9px #dbe8f0}.output-image i{position:absolute;width:9px;height:7px;left:14px;top:11px;background:#3885c4;transform:rotate(-14deg)}.guide-note{display:flex;gap:10px;align-items:center;margin-top:24px;padding:15px 17px;border:1px solid #cfe3f5;background:#f2f8fd;color:#365f84;font-size:13px;line-height:1.6}.guide-note .el-icon{flex:0 0 auto;font-size:18px}@media(max-width:900px){.guide-overview{grid-template-columns:1fr}.guide-step{grid-template-columns:1fr}.guide-step:nth-child(even) .step-copy{order:initial}.guide-visual{max-width:620px}.overview-flow{justify-content:space-between}}@media(max-width:620px){.guide-page{padding-left:14px;padding-right:14px}.overview-flow{display:grid;grid-template-columns:1fr 18px 1fr;gap:14px}.overview-node:nth-of-type(5){grid-column:1}.overview-arrow{align-self:center}.guide-step{padding:17px}.guide-visual{padding:12px 16px 29px}.callout-one{left:5px}.callout-two{right:5px}.dataset-body{grid-template-columns:70px 1fr}}
</style>
