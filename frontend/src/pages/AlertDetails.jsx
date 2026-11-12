 import { Link, useParams } from 'react-router-dom'
  import { getAlert } from '../api/alerts.js'
  import { useFetch } from '../hooks/useFetch.js'
  import { SeverityBadge } from '../components/SeverityBadge.jsx'
  import { DetectionCard } from '../components/DetectionCard.jsx'
  import { TYPE_LABELS } from '../constants.js'
  import { formatIso } from '../utils/format.js'

  export function AlertDet() {
    const { id } = useParams()
    const { data: alert, error, loading } = useFetch(() => getAlert(id), [id])

    return (
      <div>
        <Link to="/AlertFeed" className="back">← Back to Alert Feed</Link>

        {loading && <p>Loading alert…</p>}
        {error?.response?.status === 404 && <p className="error">Alert #{id} was not found.</p>}
        {error && error.response?.status !== 404 && <p className="error">Could not load alert: {error.message}</p>}

        {alert && (
          <>
            <header className="alert-head">
              <h1>
                {TYPE_LABELS[alert.type] ?? alert.type} <SeverityBadge severity={alert.severity} />
              </h1>
              <span className="muted">Alert #{alert.id}</span>
            </header>
            <p className="muted">
              {formatIso(alert.timestamp)} · {alert.sourceIp} → {alert.destinationIp}
              {' '}· {alert.detections.length} detection(s)
            </p>

            {alert.detections.length === 0
              ? <p>No detections linked to this alert.</p>
              : alert.detections.map((d) => <DetectionCard key={d.detectionId} detection={d} />)}
          </>
        )}
      </div>
    )
  }