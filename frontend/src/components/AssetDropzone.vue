<template>
  <div
    class="asset-dropzone"
    :class="{ 'is-dragover': dragActive, 'is-loading': loading }"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <el-icon class="dropzone-icon"><UploadFilled /></el-icon>
    <strong>{{ loading ? '正在上传素材…' : '拖动文件或文件夹到这里' }}</strong>
    <span>支持单个文件、多个文件和整个文件夹</span>
    <div class="dropzone-actions">
      <el-button type="primary" :icon="Upload" :loading="loading" @click="openFilePicker">选择文件</el-button>
      <el-button :icon="FolderOpened" :disabled="loading" @click="openFolderPicker">选择文件夹</el-button>
    </div>
    <input ref="fileInput" class="hidden-input" type="file" multiple :accept="accept" @change="onFileSelected" />
    <input ref="folderInput" class="hidden-input" type="file" multiple webkitdirectory :accept="accept" @change="onFolderSelected" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { FolderOpened, Upload, UploadFilled } from '@element-plus/icons-vue'

const props = defineProps({
  accept: { type: String, default: '' },
  extensions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})
const emit = defineEmits(['files'])
const fileInput = ref(null)
const folderInput = ref(null)
const dragActive = ref(false)
let dragDepth = 0

function openFilePicker() { if (!props.loading) fileInput.value?.click() }
function openFolderPicker() { if (!props.loading) folderInput.value?.click() }
function onDragEnter() { dragDepth += 1; dragActive.value = true }
function onDragLeave() { dragDepth = Math.max(0, dragDepth - 1); if (!dragDepth) dragActive.value = false }
function isAccepted(file) {
  if (!props.extensions.length) return true
  const suffix = file.name.includes('.') ? `.${file.name.split('.').pop().toLowerCase()}` : ''
  return props.extensions.includes(suffix)
}
function submitFiles(files) {
  const availableFiles = files.filter(file => file instanceof File)
  const acceptedFiles = availableFiles.filter(isAccepted)
  emit('files', acceptedFiles, availableFiles.length - acceptedFiles.length)
}
function onFileSelected(event) { submitFiles(Array.from(event.target.files || [])); event.target.value = '' }
function onFolderSelected(event) { submitFiles(Array.from(event.target.files || [])); event.target.value = '' }
function readFileEntry(entry) {
  return new Promise((resolve, reject) => entry.file(resolve, reject))
}
function readDirectoryEntries(entry) {
  const reader = entry.createReader()
  return new Promise((resolve, reject) => {
    const entries = []
    const readBatch = () => reader.readEntries(batch => {
      if (!batch.length) resolve(entries)
      else { entries.push(...batch); readBatch() }
    }, reject)
    readBatch()
  })
}
async function filesFromEntry(entry) {
  if (entry.isFile) return [await readFileEntry(entry)]
  if (!entry.isDirectory) return []
  const children = await readDirectoryEntries(entry)
  return (await Promise.all(children.map(filesFromEntry))).flat()
}
async function onDrop(event) {
  dragDepth = 0
  dragActive.value = false
  if (props.loading) return
  const items = Array.from(event.dataTransfer?.items || [])
  const entries = items.map(item => item.webkitGetAsEntry?.()).filter(Boolean)
  try {
    const files = entries.length
      ? (await Promise.all(entries.map(filesFromEntry))).flat()
      : Array.from(event.dataTransfer?.files || [])
    submitFiles(files)
  } catch {
    submitFiles(Array.from(event.dataTransfer?.files || []))
  }
}
</script>

<style scoped>
.asset-dropzone{min-height:178px;padding:22px 16px;border:1.5px dashed #cbd5e1;border-radius:10px;background:#f8fafc;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;transition:border-color .18s,background .18s,box-shadow .18s}.asset-dropzone.is-dragover{border-color:#2563eb;background:#eff6ff;box-shadow:0 0 0 4px rgb(37 99 235 / 10%)}.asset-dropzone.is-loading{opacity:.78}.dropzone-icon{margin-bottom:8px;color:#2563eb;font-size:28px}.asset-dropzone strong{color:#334155;font-size:14px}.asset-dropzone span{margin-top:5px;color:#64748b;font-size:12px}.dropzone-actions{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.dropzone-actions :deep(.el-button){min-height:40px}.hidden-input{display:none}
</style>
