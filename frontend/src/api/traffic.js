import api from './api.js'

  export const getCurrentTraffic = () => api.get('/traffic/current').then((r) => r.data)
  export const getTimeseries = (bucket) =>
    api.get('/traffic/timeseries', { params: { window: bucket } }).then((r) => r.data.points)
  export const getTopTalkers = (limit = 5) =>
    api.get('/traffic/top-talkers', { params: { limit } }).then((r) => r.data)