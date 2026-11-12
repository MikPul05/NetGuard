import api from './api.js'
export const getLatestAlerts = () => api.get('/alerts/latest').then((r) => r.data)
export const getAlert = (id) => api.get(`/alerts/${id}`).then((r) => r.data)