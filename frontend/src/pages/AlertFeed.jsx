 import { useEffect, useState } from 'react'
  import api from '../api/api.js'


export function AlertFeed(){
    const [health, setHealth] = useState(null)
    const [alerts, setAlerts] = useState([])
    const [error, setError] = useState(null)

    useEffect(() => {
      api.get('/health')
        .then((r) => setHealth(r.data))
        .catch((e) => setHealth(e.response?.data ?? null))   // 503 still has a JSON body

      api.get('/alerts')
        .then((r) => setAlerts(r.data.alerts))
        .catch((e) => setError(e.message))
    }, [])

    return (
      <div style={{ padding: 16, fontFamily: 'sans-serif' }}>
        <h1>NetGuard</h1>

        <h2>Health</h2>
        <pre>{health ? JSON.stringify(health, null, 2) : 'loading...'}</pre>

        <h2>Alerts</h2>
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        <table border="1" cellPadding="4">
          <thead>
            <tr><th>ID</th><th>Time</th><th>Type</th><th>Severity</th><th>Source</th><th>Destination</th></tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id}>
                <td>{a.id}</td><td>{a.timestamp}</td><td>{a.type}</td>
                <td>{a.severity}</td><td>{a.sourceIp}</td><td>{a.destinationIp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
    }