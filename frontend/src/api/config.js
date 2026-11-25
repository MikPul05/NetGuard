  import api from './api.js'

  export const getDetectionConfig = () => api.get('/config/detection').then((r) => r.data)
  export const saveDetectionConfig = (config) => api.put('/config/detection', config).then((r) => r.data)
  export const getSources = () => api.get('/sources/').then((r) => r.data.sources)