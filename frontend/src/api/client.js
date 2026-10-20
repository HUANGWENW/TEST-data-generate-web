import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export async function listProjects() {
  const { data } = await api.get('/projects')
  return data
}

export async function createProject(payload) {
  const { data } = await api.post('/projects', payload)
  return data
}


export async function deleteProject(projectId) {
  await api.delete(`/projects/${projectId}`, { timeout: 0 })
}

export async function deleteAssets(projectId, assetIds) {
  const { data } = await api.post(`/projects/${projectId}/assets/delete`, { asset_ids: assetIds }, { timeout: 0 })
  return data.deleted_ids
}

export async function getProject(id) {
  const { data } = await api.get(`/projects/${id}`)
  return data
}

export async function listAssets(projectId, assetType) {
  const { data } = await api.get(`/projects/${projectId}/assets`, { params: assetType ? { asset_type: assetType } : {} })
  return data
}

export async function uploadAsset(projectId, assetType, file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post(`/projects/${projectId}/assets/upload`, form, {
    params: { asset_type: assetType },
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}

export async function createTask(projectId, taskType, params) {
  const { data } = await api.post(`/projects/${projectId}/tasks`, { task_type: taskType, params })
  return data
}

export async function listProjectTasks(projectId) {
  const { data } = await api.get(`/projects/${projectId}/tasks`)
  return data
}

export async function listDatasetFiles(projectId, datasetId) {
  const { data } = await api.get(`/projects/${projectId}/datasets/${datasetId}/files`)
  return data
}

export async function downloadDatasetArchive(projectId, datasetId, content = 'all') {
  return api.get(`/projects/${projectId}/datasets/${datasetId}/download`, {
    params: { content },
    responseType: 'blob',
    timeout: 0
  })
}

export async function listTasks() {
  const { data } = await api.get('/tasks')
  return data
}
