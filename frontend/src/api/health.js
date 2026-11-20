 import api from './api.js'

  // /health answers 503 when the database or Kafka is down - that is still a valid answer
  export const getHealth = () =>
    api.get('/health', { validateStatus: (s) => s === 200 || s === 503 }).then((r) => r.data)