<template>
  <div class="page guide-page">
    <header class="guide-header">
      <div><h1>使用指引</h1><p>选好起点，按顺序生成并下载数据。</p></div>
      <router-link class="guide-start" to="/">打开项目总览 <span aria-hidden="true">→</span></router-link>
    </header>

    <fieldset class="guide-entry">
      <legend>你现在有什么素材？</legend>
      <select v-model="entry" class="guide-mobile-entry" aria-label="选择素材起点" @change="updateEntry">
        <option v-for="option in entryOptions" :key="option.id" :value="option.id">{{ option.title }} · {{ option.hint }}</option>
      </select>
      <div class="guide-options" :style="{ '--entry-index': entryIndex }">
        <span class="guide-option-indicator" aria-hidden="true"></span>
        <label v-for="option in entryOptions" :key="option.id" class="guide-option" :class="{ selected: entry === option.id }">
          <input v-model="entry" type="radio" name="guide-entry" :value="option.id" :aria-label="option.title" @change="updateEntry" />
          <span class="guide-option-copy"><strong>{{ option.title }}</strong><span>{{ option.hint }}</span></span>
          <span class="guide-option-check" aria-hidden="true">{{ entry === option.id ? '✓' : '' }}</span>
        </label>
      </div>
    </fieldset>

    <div class="guide-preparation" role="status" aria-live="polite" aria-atomic="true">
      <strong>需要准备</strong><span>{{ currentEntry.materials }}</span>
      <span v-if="entry !== 'full'" class="guide-shortcut">{{ currentEntry.shortcut }}</span>
    </div>

    <div class="guide-layout">
      <section class="guide-process" aria-labelledby="guide-process-title">
        <div class="guide-section-heading"><h2 id="guide-process-title">{{ currentEntry.flowTitle }}</h2><span>{{ visibleSteps.length }} 步完成</span></div>
        <ol class="guide-flow">
          <li v-for="(step, index) in visibleSteps" :key="step.id" class="guide-step">
            <span class="guide-step-number" aria-hidden="true">{{ index + 1 }}</span>
            <div class="guide-step-copy">
              <div class="guide-step-heading"><h3>{{ step.title }}</h3><span class="guide-step-location">{{ step.location }}</span></div>
              <p v-for="line in step.lines" :key="line"><span v-for="(piece, pieceIndex) in instructionParts(line)" :key="pieceIndex" :class="{ 'guide-control-name': piece.startsWith('「') && piece.length <= 12 }">{{ piece }}</span></p>
              <p v-if="step.note" class="guide-step-note">{{ step.note }}</p>
              <div class="guide-visuals" :class="{ 'is-formula': step.formula, 'is-collection': step.id === 'prepare' }" :style="{ '--visual-count': step.visuals.length }" :aria-label="step.visualLabel">
                <figure v-for="(visual, visualIndex) in step.visuals" :key="visual.id" class="guide-visual" :class="{ 'is-output': step.formula && visualIndex === 2 }">
                  <span v-if="(step.formula || step.id === 'mask') && visualIndex" class="guide-visual-connector" aria-hidden="true">{{ step.formula && visualIndex === 1 ? '+' : '→' }}</span>
                  <button type="button" class="guide-photo" :class="{ 'is-transparent': visual.id === 'part', 'is-screen': visual.id === 'download' }" :aria-label="'放大查看：' + visual.label" @click="openPicture(visual)">
                    <img :src="visual.src" :alt="visual.alt" :width="visual.width" :height="visual.height" loading="lazy" decoding="async" />
                    <span class="guide-photo-zoom" aria-hidden="true">↗</span>
                  </button>
                  <figcaption>{{ visual.label }}</figcaption>
                </figure>
              </div>
            </div>
          </li>
        </ol>
        <div class="guide-finish"><span>完成后，可随时回到项目继续生成新批次。</span><router-link to="/tasks">查看任务进度 <span aria-hidden="true">→</span></router-link></div>
      </section>

      <aside class="guide-help" aria-labelledby="guide-help-title">
        <h2 id="guide-help-title">需要时再看</h2>
        <details class="guide-answer">
          <summary>标签格式怎么选？<span aria-hidden="true">+</span></summary>
          <div class="guide-answer-body"><dl><div><dt>YOLO HBB</dt><dd>普通矩形检测框。</dd></div><div><dt>YOLO OBB</dt><dd>随零件方向旋转的检测框。</dd></div><div><dt>COCO Segmentation</dt><dd>分割轮廓标注。</dd></div></dl><p>当前结果页支持下载 YOLO 标签 TXT，暂不提供 COCO JSON 下载入口。</p></div>
        </details>
        <details class="guide-answer">
          <summary>纹理与零件尺寸怎么设？<span aria-hidden="true">+</span></summary>
          <div class="guide-answer-body"><p>「原尺寸裁剪/平铺」保留纹理像素，纹理不够大时重复平铺。「拉伸宽高」用整张纹理填满轮廓，纹理比例可能改变。</p><p>「输出最长边」填 0 保留 Mask 原尺寸；填正数只会等比缩小，不会放大。</p></div>
        </details>
        <details class="guide-answer">
          <summary>合成参数先改哪些？<span aria-hidden="true">+</span></summary>
          <div class="guide-answer-body"><p>先选背景与零件，设置「生成数量」「每张零件数」，再按需要调整布局、旋转角度和缩放比例。</p><p>上下左右边距单位是 px。确认预览中的青色虚线区域有效，且零件能放入其中。</p></div>
        </details>
        <details class="guide-answer">
          <summary>提交后没看到结果怎么办？<span aria-hidden="true">+</span></summary>
          <div class="guide-answer-body"><p>到「任务中心」查看状态：排队中或生成中时继续等待；失败时查看该行错误信息。</p><p>Mask 和透明零件生成后，在对应步骤的验收区查看；数据集完成后点「查看生成结果」。结果页未更新时点「刷新」。</p></div>
        </details>
        <details class="guide-answer">
          <summary>DXF 能直接转成 Mask 吗？<span aria-hidden="true">+</span></summary>
          <div class="guide-answer-body"><p>目前不能。「DXF 文件」只保存原文件，不生成边缘图或 Mask。提取轮廓请使用 GEN 文件或已有边缘图。</p></div>
        </details>
        <p class="guide-upload-note">文件与文件夹均可批量上传；选择或拖入文件后即开始上传。</p>
      </aside>
    </div>
    <el-dialog v-model="pictureOpen" :title="activePicture?.label || '素材图片'" width="min(1000px, calc(100vw - 32px))" class="guide-picture-dialog" align-center>
      <div v-if="activePicture" class="guide-picture-stage" :class="{ 'is-transparent': activePicture.id === 'part' }"><img :src="activePicture.src" :alt="activePicture.alt" /></div>
      <p v-if="activePicture" class="guide-picture-description">{{ activePicture.alt }}</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import edgeImage from '../assets/guide/edge.webp'
import maskImage from '../assets/guide/mask.webp'
import textureImage from '../assets/guide/texture.webp'
import partImage from '../assets/guide/part.webp'
import backgroundImage from '../assets/guide/background.webp'
import datasetImage from '../assets/guide/dataset.webp'
import downloadImage from '../assets/guide/download.webp'

const route = useRoute()
const router = useRouter()
const pictureOpen = ref(false)
const activePicture = ref(null)
function openPicture(picture) { activePicture.value = picture; pictureOpen.value = true }
const pictures = {
  edge: { id: 'edge', label: '边缘图', src: edgeImage, width: 409, height: 437, alt: '黑底白线的零件边缘图，外轮廓和四个孔位清晰可见。' },
  mask: { id: 'mask', label: 'Mask', src: maskImage, width: 405, height: 434, alt: '提取后的 Mask：白色为零件实体，黑色为背景与孔洞。' },
  texture: { id: 'texture', label: '纹理图', src: textureImage, width: 800, height: 600, alt: '浅色金属表面纹理，用于填充零件的实体区域。' },
  part: { id: 'part', label: '透明零件', src: partImage, width: 405, height: 434, alt: '填入金属纹理的透明零件，外部与四个孔位保留透明。' },
  background: { id: 'background', label: '背景图', src: backgroundImage, width: 1200, height: 879, alt: '深色工业台面背景，用于放置透明零件。' },
  dataset: { id: 'dataset', label: '合成结果', src: datasetImage, width: 1600, height: 1172, alt: '实际生成的图片：浅色零件被放置在深色台面右下方，孔位透出背景。' },
  download: { id: 'download', label: '选择「图片 + 标签」', src: downloadImage, width: 300, height: 215, alt: '结果页的批量下载菜单：全部图片、全部标签 TXT、图片 + 标签。' }
}
const entryOptions = [
  { id: 'full', title: 'GEN / 边缘图', hint: '从提取轮廓开始', materials: 'GEN 或边缘图、纹理图、背景图', flowTitle: '完整生成流程' },
  { id: 'mask', title: '已有 Mask', hint: '跳过轮廓提取', materials: '已有 Mask、纹理图、背景图', shortcut: '省去提取 Mask', flowTitle: '从已有 Mask 开始' },
  { id: 'parts', title: '项目中已有零件', hint: '直接进入合成', materials: '项目内已生成的透明零件、背景图', shortcut: '省去前两步生成', flowTitle: '从已有透明零件开始' }
]
function validEntry(value) { return entryOptions.some(option => option.id === value) ? value : 'full' }
function instructionParts(text) { return text.split(/(「[^」]*」)/g).filter(Boolean) }
const entry = ref(validEntry(route.query.start))
const entryIndex = computed(() => entryOptions.findIndex(option => option.id === entry.value))
const currentEntry = computed(() => entryOptions[entryIndex.value])
const preparation = computed(() => ({
  id: 'prepare', title: entry.value === 'parts' ? '进入项目，准备背景' : '建好项目，上传素材', location: '项目总览 → 素材管理',
  visuals: entry.value === 'parts' ? [pictures.part, pictures.background] : [entry.value === 'mask' ? pictures.mask : pictures.edge, pictures.texture, pictures.background],
  visualLabel: '本流程需要的素材图片',
  lines: entry.value === 'parts'
    ? ['选择已有透明零件的项目，点击「进入工作台」。', '在「素材管理」确认已有零件与背景；缺少背景时点击「上传素材」，类型选「背景图」。']
    : ['在「项目总览」新建或选择项目，点击「进入工作台」。', `点击「上传素材」，按素材类型分别添加${entry.value === 'mask' ? '「已有 Mask」' : '「输入文件 · GEN / 边缘图」'}、纹理图和背景图。`]
}))
const processSteps = [
  { id: 'mask', title: '提取 Mask', location: '01 提取 Mask', lines: ['选择输入文件与提取方式，点击「提交 Mask 提取」。', '任务完成后，在「Mask 验收」勾选轮廓完整、孔洞正确的结果，点击「进入第二步」。'], visuals: [pictures.edge, pictures.mask], visualLabel: '从边缘图提取为实体 Mask' },
  { id: 'parts', title: '生成透明零件', location: '02 透明零件', lines: ['勾选 Mask、选择纹理图，点击「生成透明零件」。', '任务完成后，在「透明零件验收」勾选需要的结果，点击「进入第三步」。'], visuals: [pictures.mask, pictures.texture, pictures.part], formula: true, visualLabel: 'Mask 加纹理图，生成透明零件' },
  { id: 'generate', title: '合成数据集', location: '03 合成数据', lines: ['勾选零件，选择背景、标签格式、布局和生成数量。', '确认可放置区域与生成前检查通过，点击「开始生成数据集」，页面会进入任务中心。'], note: '需要下载标签，请选 YOLO；COCO 暂无 JSON 下载入口。', visuals: [pictures.part, pictures.background, pictures.dataset], formula: true, visualLabel: '透明零件加背景图，生成合成结果' },
  { id: 'download', title: '查看并下载结果', location: '任务中心 → 结果阅览', lines: ['任务显示「已完成」后，点击「查看生成结果」。', '确认「数据集批次」，点击「批量下载 → 图片 + 标签」；也可逐张查看图片、标签 TXT 和生成信息 TXT。'], visuals: [pictures.dataset, pictures.download], visualLabel: '合成图片与对应的批量下载菜单' }
]
const visibleSteps = computed(() => [preparation.value, ...processSteps.filter(step => (
  entry.value === 'full' || (entry.value === 'mask' ? step.id !== 'mask' : !['mask', 'parts'].includes(step.id))
))])
function updateEntry() {
  const query = { ...route.query }
  if (entry.value === 'full') delete query.start
  else query.start = entry.value
  router.replace({ query })
}
watch(() => route.query.start, value => { entry.value = validEntry(value) })
</script>

<style scoped>
.guide-page { max-width: 1320px; }
.guide-header { display: flex; align-items: center; justify-content: space-between; gap: 24px; margin-bottom: 32px; }
.guide-header h1 { margin: 0 0 8px; color: var(--studio-text); font-size: 36px; font-weight: 600; line-height: 1.4; }
.guide-header p { margin: 0; color: var(--studio-muted); font-size: 18px; line-height: 1.7; }
.guide-start { display: inline-flex; align-items: center; justify-content: center; gap: 18px; min-height: 48px; flex-shrink: 0; padding: 10px 20px; border: 1px solid var(--studio-primary); border-radius: 4px; color: #fff; background: #8d4716; font-size: 18px; font-weight: 600; line-height: 1.5; text-decoration: none; transition: background-color 140ms ease, transform 100ms ease; }
.guide-start:hover { background: #783b12; }
.guide-start:active { transform: translateY(1px); }
.guide-start span { font-size: 22px; }
.guide-entry { min-width: 0; margin: 0; padding: 0; border: 0; }
.guide-entry legend { margin-bottom: 12px; padding: 0; color: var(--studio-text); font-size: 20px; font-weight: 600; line-height: 1.5; }
.guide-mobile-entry { display: none; }
.guide-options { position: relative; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); isolation: isolate; padding: 4px; border: 1px solid var(--studio-border); border-radius: 5px; background: #eeeadf; }
.guide-option-indicator { position: absolute; inset: 4px auto 4px 4px; z-index: -1; width: calc((100% - 8px) / 3); border: 1px solid #c5a07d; border-radius: 3px; background: var(--studio-surface); transform: translateX(calc(var(--entry-index) * 100%)); transition: transform 180ms cubic-bezier(.22, 1, .36, 1); }
.guide-option { position: relative; display: flex; align-items: center; justify-content: space-between; gap: 12px; min-width: 0; min-height: 82px; padding: 13px 20px; color: var(--studio-muted); cursor: pointer; }
.guide-option input { position: absolute; width: 1px; height: 1px; padding: 0; border: 0; opacity: 0; }
.guide-option-copy { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.guide-option strong { color: #475044; font-size: 18px; font-weight: 600; line-height: 1.5; }
.guide-option-copy > span { font-size: 16px; line-height: 1.5; }
.guide-option-check { flex-shrink: 0; width: 18px; color: #8d4716; font-size: 19px; font-weight: 600; }
.guide-option.selected strong { color: #85461b; }
.guide-option:has(input:focus-visible) { outline: 2px solid var(--studio-primary); outline-offset: -3px; border-radius: 3px; }
.guide-preparation { display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px 16px; margin: 16px 0 30px; color: var(--studio-muted); font-size: 16px; line-height: 1.7; }
.guide-preparation strong { color: #475044; font-weight: 600; }
.guide-shortcut { margin-left: auto; color: #80532f; }
.guide-layout { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 48px; align-items: start; }
.guide-process { min-width: 0; }
.guide-section-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; padding-bottom: 18px; border-bottom: 1px solid var(--studio-border); }
.guide-section-heading h2, .guide-help > h2 { margin: 0; color: var(--studio-text); font-size: 22px; font-weight: 600; line-height: 1.5; }
.guide-section-heading > span { flex-shrink: 0; color: var(--studio-muted); font-size: 16px; }
.guide-flow { margin: 0; padding: 0; list-style: none; }
.guide-step { display: flex; align-items: flex-start; gap: 18px; padding: 23px 0 25px; border-bottom: 1px solid var(--el-border-color-light); }
.guide-step-number { display: grid; flex: 0 0 32px; min-height: 32px; place-items: center; margin-top: 1px; border: 1px solid #c5ab8b; border-radius: 50%; color: #8b4d20; font-size: 17px; font-weight: 600; line-height: 1; }
.guide-step-copy { flex: 1; min-width: 0; }
.guide-step-heading { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 5px 14px; margin-bottom: 9px; }
.guide-step h3 { margin: 0; color: var(--studio-text); font-size: 21px; font-weight: 600; line-height: 1.5; }
.guide-step-location { color: #6c6d60; font-size: 15px; line-height: 1.6; }
.guide-step p { margin: 0; color: #475044; font-size: 17px; line-height: 1.85; overflow-wrap: anywhere; }
.guide-step p + p { margin-top: 4px; }
.guide-control-name { white-space: nowrap; }
.guide-step p.guide-step-note { margin-top: 7px; color: #80532f; font-size: 16px; line-height: 1.7; }
.guide-visuals { display: grid; grid-template-columns: repeat(var(--visual-count), minmax(0, 1fr)); gap: 24px; max-width: 700px; margin-top: 18px; }
.guide-visual { position: relative; min-width: 0; margin: 0; }
.guide-photo { position: relative; display: flex; align-items: center; justify-content: center; width: 100%; height: 148px; padding: 10px; overflow: hidden; border: 1px solid #ded8cb; border-radius: 3px; color: #80532f; background: #fffdf8; cursor: zoom-in; transition: border-color 140ms ease, background-color 140ms ease; }
.guide-photo:hover { border-color: #ad7a4e; background-color: #f8f2e8; }
.guide-photo:focus-visible { outline: 2px solid var(--studio-primary); outline-offset: 3px; }
.guide-photo img { display: block; width: 100%; height: 100%; object-fit: contain; }
.guide-photo.is-transparent, .guide-picture-stage.is-transparent { background-color: #d8d4ca; background-image: conic-gradient(#b7b4ac 25%, transparent 0 50%, #b7b4ac 0 75%, transparent 0); background-size: 20px 20px; }
.guide-photo.is-screen { padding: 0; }
.guide-photo-zoom { position: absolute; right: 5px; bottom: 5px; display: grid; width: 23px; height: 23px; place-items: center; border-radius: 2px; background: #fffdf8ed; font: 18px/1 var(--studio-font); }
.guide-visual figcaption { margin-top: 7px; color: #5f6255; font-size: 16px; line-height: 1.65; text-align: center; }
.guide-visual-connector { position: absolute; z-index: 1; top: 61px; left: -21px; width: 18px; color: #8b4d20; font-size: 22px; line-height: 1; text-align: center; }
.guide-picture-stage { display: flex; align-items: center; justify-content: center; min-height: 180px; padding: 16px; border: 1px solid var(--studio-border); border-radius: 3px; background: #f6f4ed; }
.guide-picture-stage img { display: block; max-width: 100%; max-height: 68vh; object-fit: contain; }
.guide-picture-description { margin: 14px 0 0; color: var(--studio-muted); font-size: 17px; line-height: 1.8; }
.guide-finish { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 10px 20px; margin-top: 22px; color: var(--studio-muted); font-size: 16px; line-height: 1.7; }
.guide-finish a { display: inline-flex; align-items: center; gap: 12px; min-height: 44px; color: #8b4d20; text-decoration: none; font-weight: 600; }
.guide-finish a:hover { text-decoration: underline; text-underline-offset: 5px; }
.guide-help { position: sticky; top: 24px; min-width: 0; padding: 22px; border: 1px solid var(--studio-border); border-radius: 4px; background: var(--studio-surface); }
.guide-help > h2 { margin-bottom: 12px; font-size: 20px; }
.guide-answer { border-bottom: 1px solid var(--el-border-color-light); }
.guide-answer summary { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 58px; padding: 12px 0; list-style: none; color: #475044; font-size: 17px; font-weight: 500; line-height: 1.65; cursor: pointer; }
.guide-answer summary::-webkit-details-marker { display: none; }
.guide-answer summary > span { color: #8b4d20; font-size: 24px; font-weight: 400; line-height: 1; transition: transform 160ms ease; }
.guide-answer[open] summary { color: #8b4d20; }
.guide-answer[open] summary > span { transform: rotate(45deg); }
.guide-answer summary:focus-visible { outline: 2px solid var(--studio-primary); outline-offset: 3px; }
.guide-answer-body { padding: 0 0 17px; color: var(--studio-muted); font-size: 16px; line-height: 1.8; overflow-wrap: anywhere; }
.guide-answer[open] .guide-answer-body { animation: guide-answer-enter 160ms ease-out; }
.guide-answer-body p { margin: 0; }
.guide-answer-body p + p, .guide-answer-body dl + p { margin-top: 12px; }
.guide-answer-body dl { margin: 0; }
.guide-answer-body dl > div + div { margin-top: 8px; }
.guide-answer-body dt { color: #475044; font-weight: 600; }
.guide-answer-body dd { margin: 0; }
.guide-upload-note { margin: 18px 0 0; color: var(--studio-muted); font-size: 16px; line-height: 1.8; }
@keyframes guide-answer-enter { from { opacity: .4; transform: translateY(-3px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 1080px) { .guide-layout { grid-template-columns: minmax(0, 1fr) 285px; gap: 28px; } .guide-option { padding-inline: 15px; } .guide-step-heading { display: block; } .guide-step-location { display: block; margin-top: 4px; } .guide-help { padding: 18px; } }
@media (max-width: 900px) { .guide-layout { grid-template-columns: minmax(0, 1fr); gap: 30px; } .guide-help { position: static; } .guide-step-heading { display: flex; } .guide-step-location { display: inline; margin-top: 0; } }
@media (max-width: 600px) {
  .guide-header { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px 12px; margin-bottom: 25px; }
  .guide-header > div { display: contents; }
  .guide-header h1 { margin: 0; font-size: 28px; }
  .guide-header p { grid-column: 1 / -1; grid-row: 2; font-size: 17px; }
  .guide-start { grid-column: 2; grid-row: 1; gap: 8px; min-height: 44px; padding: 8px 12px; font-size: 16px; }
  .guide-start span { font-size: 18px; }
  .guide-entry legend { font-size: 19px; }
  .guide-options { display: none; }
  .guide-mobile-entry { display: block; width: 100%; min-width: 0; min-height: 52px; padding: 10px 28px 10px 12px; border: 1px solid #bda589; border-radius: 4px; color: #75421f; background: var(--studio-surface); font: 17px/1.6 var(--studio-font); }
  .guide-mobile-entry:focus-visible { outline: 2px solid var(--studio-primary); outline-offset: 3px; }
  .guide-preparation { display: block; margin-bottom: 25px; }
  .guide-preparation strong { display: block; margin-bottom: 4px; }
  .guide-shortcut { display: block; margin: 4px 0 0; }
  .guide-section-heading h2 { font-size: 21px; }
  .guide-step { gap: 12px; padding: 20px 0 22px; }
  .guide-step-number { flex-basis: 28px; min-height: 28px; font-size: 16px; }
  .guide-step-heading { display: block; margin-bottom: 8px; }
  .guide-step h3 { font-size: 20px; }
  .guide-step-location { display: block; margin-top: 4px; }
  .guide-step p { font-size: 17px; line-height: 1.85; }
  .guide-visuals { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 13px 22px; }
  .guide-visuals.is-collection { grid-template-columns: repeat(var(--visual-count), minmax(0, 1fr)); gap: 10px; }
  .guide-visuals.is-collection .guide-photo { height: 108px; }
  .guide-photo { height: 126px; padding: 7px; }
  .guide-visual figcaption { font-size: 16px; }
  .guide-visuals.is-formula { row-gap: 30px; }
  .guide-visual.is-output { grid-column: 1 / -1; justify-self: center; width: calc((100% - 22px) / 2); }
  .guide-visual-connector { top: 52px; }
  .guide-visual.is-output .guide-visual-connector { top: -27px; left: calc(50% - 9px); transform: rotate(90deg); }
  .guide-finish { display: block; }
  .guide-finish a { margin-top: 5px; }
  .guide-help { padding: 18px; }
}
@media (prefers-reduced-motion: reduce) { .guide-start, .guide-option-indicator, .guide-answer summary > span, .guide-photo { transition: none; } .guide-answer-body { animation: none !important; } }
</style>
