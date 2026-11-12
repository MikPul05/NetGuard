import api from './api.js'
export const getLatestAlerts = () => api.get('/alerts/latest').then((r) => r.data)