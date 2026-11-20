 import { getHealth } from '../api/health.js'
  import { usePolling } from '../hooks/usePolling.js'

  const okOrDown = (s) => (s === 'healthy' ? 'OK' : 'down')

  export function HealthIndicator() {
    const { data, error } = usePolling(getHealth, [], 10000)

    let color = '#9ca3af'
    let text = 'Checking…'
    if (error) {
      color = '#dc2626'
      text = 'API offline'
    } else if (data?.status === 'healthy') {
      color = '#16a34a'
      text = 'All systems OK'
    } else if (data) {
      color = '#ca8a04'
      text = `Degraded – DB ${okOrDown(data.database)}, Kafka ${okOrDown(data.kafka)}`
    }

    return (
      <span className="health" title={data ? `Database: ${data.database}\nKafka: ${data.kafka}` : ''}>
        <span className="dot" style={{ background: color }} />
        {text}
      </span>
    )
  }