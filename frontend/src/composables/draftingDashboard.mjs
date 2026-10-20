export function dashboardState() {
  return {
    projects: [], selectedProjectId: '', loading: false, listError: '',
    assets: [], assetLoading: false, assetError: '', previewKind: 'mask', previewAssetId: '',
    creating: false, deletingProjectId: '',
  }
}

export function errorDetail(error, fallback) {
  const detail = error?.response?.data?.detail
  return typeof detail === 'string' && detail ? detail : fallback
}

export function previewAssets(state, kind = state.previewKind) {
  return state.assets.filter(asset => asset.asset_type === kind)
}

export function createDashboardController(api, state = dashboardState()) {
  let projectVersion = 0
  let assetVersion = 0
  let disposed = false

  function selectPreviewKind(kind) {
    state.previewKind = kind === 'part' ? 'part' : 'mask'
    state.previewAssetId = previewAssets(state)[0]?.id || ''
  }

  async function selectProject(id, { force = false } = {}) {
    if (disposed || (id === state.selectedProjectId && !force)) return false
    const version = ++assetVersion
    const changed = id !== state.selectedProjectId
    state.selectedProjectId = id || ''
    state.assetError = ''
    if (changed || !id) {
      state.assets = []
      state.previewAssetId = ''
      state.previewKind = 'mask'
    }
    if (!id) { state.assetLoading = false; return true }
    state.assetLoading = true
    try {
      const assets = await api.listAssets(id)
      if (disposed || version !== assetVersion || state.selectedProjectId !== id) return false
      state.assets = assets
      if (!previewAssets(state).length) state.previewKind = assets.some(asset => asset.asset_type === 'mask') ? 'mask' : 'part'
      const candidates = previewAssets(state)
      if (!candidates.some(asset => asset.id === state.previewAssetId)) state.previewAssetId = candidates[0]?.id || ''
      return true
    } catch (error) {
      if (!disposed && version === assetVersion) state.assetError = errorDetail(error, '素材加载失败，请重试')
      return false
    } finally {
      if (!disposed && version === assetVersion) state.assetLoading = false
    }
  }

  async function loadProjects(preferredId = '') {
    const version = ++projectVersion
    state.loading = true
    state.listError = ''
    try {
      const projects = await api.listProjects()
      if (disposed || version !== projectVersion) return false
      state.projects = projects
      const selected = [state.selectedProjectId, preferredId].find(id => projects.some(project => project.id === id)) || projects[0]?.id || ''
      await selectProject(selected, { force: true })
      return true
    } catch (error) {
      if (!disposed && version === projectVersion) state.listError = errorDetail(error, '项目加载失败，请重试')
      return false
    } finally {
      if (!disposed && version === projectVersion) state.loading = false
    }
  }

  async function createProject(payload) {
    if (disposed || state.creating) return null
    state.creating = true
    try {
      const project = await api.createProject(payload)
      if (disposed) return null
      ++projectVersion
      state.loading = false
      state.projects = [project, ...state.projects.filter(item => item.id !== project.id)]
      await selectProject(project.id)
      return project
    } finally {
      if (!disposed) state.creating = false
    }
  }

  async function removeProject(id) {
    if (disposed || state.deletingProjectId) return false
    state.deletingProjectId = id
    try {
      await api.deleteProject(id)
      if (disposed) return false
      ++projectVersion
      state.loading = false
      state.projects = state.projects.filter(project => project.id !== id)
      const selected = state.projects.some(project => project.id === state.selectedProjectId)
        ? state.selectedProjectId : state.projects[0]?.id || ''
      await selectProject(selected, { force: true })
      return true
    } catch (error) {
      if (!disposed && error?.response?.status === 404) await loadProjects()
      throw error
    } finally {
      if (!disposed) state.deletingProjectId = ''
    }
  }

  return {
    state, loadProjects, selectProject, selectPreviewKind, createProject, removeProject,
    dispose() { disposed = true; ++projectVersion; ++assetVersion },
  }
}
