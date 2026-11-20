import api from './api.js'

  export const getSummary = (params) => api.get('/stats/summary', { params }).then((r) => r.data)
  export const getMethods = () => api.get('/stats/methods').then((r) => r.data)
  export const getQuality = (runId) =>
    api.get('/stats/quality', { params: runId ? { runId } : {} }).then((r) => r.data)
  export const getRuns = () => api.get('/runs').then((r) => r.data.runs)