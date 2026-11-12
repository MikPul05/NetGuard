import api from './api.js'

  const enc = encodeURIComponent

  export const getEvidence = (id) => api.get(`/detections/${enc(id)}/evidence`).then((r) => r.data)
  export const getTrace = (id) => api.get(`/detections/${enc(id)}/trace`).then((r) => r.data)