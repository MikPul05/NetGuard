 import { useEffect, useRef, useState } from 'react'
  import { useNavigate } from 'react-router-dom'
  import { getLatestAlerts } from '../api/alerts.js'
  import { SeverityBadge } from '../components/SeverityBadge.jsx'
  import { POLL_MS, TYPE_LABELS } from '../constants.js'

  export function AlertFeed() {
    const [alerts, setAlerts] = useState(null)      // null = not loaded yet
    const [error, setError] = useState(null)
    const [newIds, setNewIds] = useState(new Set())
    const [updatedAt, setUpdatedAt] = useState(null)
    const knownIds = useRef(null)                   // IDs seen so far
    const navigate = useNavigate()

    useEffect(() => {
      let cancelled = false

      async function load() {
        try {
          const data = await getLatestAlerts()
          if (cancelled) return
          // after the first load, mark alerts we haven't seen before as new
          if (knownIds.current) {
            const fresh = data.filter((a) => !knownIds.current.has(a.id)).map((a) => a.id)
            if (fresh.length) {
              setNewIds(new Set(fresh))
              setTimeout(() => !cancelled && setNewIds(new Set()), 5000)
            }
          }
          knownIds.current = new Set(data.map((a) => a.id))
          setAlerts(data)
          setError(null)
          setUpdatedAt(new Date())
        } catch (e) {
          if (!cancelled) setError(e.message)       // keep showing the last list
        }
      }

      load()
      const timer = setInterval(load, POLL_MS)
      return () => { cancelled = true; clearInterval(timer) }   // stop when leaving the page
    }, [])

    return (
      <div>
        <h1>Alert Feed</h1>
        <p className="muted">
          Refreshes every {POLL_MS / 1000} s
          {updatedAt && ` · last update ${updatedAt.toLocaleTimeString()}`}
        </p>

        {error && <p className="error">Could not refresh alerts: {error}</p>}

        {alerts === null && !error && <p>Loading…</p>}
        {alerts?.length === 0 && <p>No alerts yet.</p>}

        {alerts?.length > 0 && (
          <table className="table">
            <thead>
              <tr><th>Time</th><th>Severity</th><th>Type</th><th>Source</th><th>Destination</th></tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr
                  key={a.id}
                  className={`clickable ${newIds.has(a.id) ? 'new-row' : ''}`}
                  onClick={() => navigate(`/AlertDetails/${a.id}`)}
                >
                  <td>{new Date(a.timestamp).toLocaleString()}</td>
                  <td><SeverityBadge severity={a.severity} /></td>
                  <td>{TYPE_LABELS[a.type] ?? a.type}</td>
                  <td>{a.sourceIp}</td>
                  <td>{a.destinationIp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    )
  }