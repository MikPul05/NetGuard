 import { useState } from 'react'
  import { Link, useNavigate } from 'react-router-dom'
  import { getLatestAlerts } from '../api/alerts.js'
  import { getSummary } from '../api/stats.js'
  import { getCurrentTraffic, getTimeseries, getTopTalkers } from '../api/traffic.js'
  import { SeverityBadge } from '../components/SeverityBadge.jsx'
  import { StatTile } from '../components/StatTile.jsx'
  import { TrafficChart } from '../components/TrafficChart.jsx'
  import { POLL_MS, SEVERITIES, SEVERITY_COLORS, TYPE_LABELS } from '../constants.js'
  import { usePolling } from '../hooks/usePolling.js'
  import { formatBytes, formatIso } from '../utils/format.js'



  const fmtRate = (x) => (x ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 })

  export function LiveMonit() {
    const [bucket, setBucket] = useState('10s')
    const navigate = useNavigate()

    const current = usePolling(getCurrentTraffic, [], POLL_MS)
    const series = usePolling(() => getTimeseries(bucket), [bucket], POLL_MS)
    const talkers = usePolling(() => getTopTalkers(5), [], POLL_MS)
    const alerts = usePolling(getLatestAlerts, [], POLL_MS)
    const summary = usePolling(() => getSummary({}), [], POLL_MS)

    const failed = [current, series, talkers, alerts, summary].find((s) => s.error)
    const c = current.data
    const bySeverity = summary.data?.bySeverity ?? {}

    return (
      <div>
        <h1>Live Monitoring</h1>
        <p className="muted">Refreshes every {POLL_MS / 1000} s</p>
        {failed && <p className="error">Some data could not be refreshed: {failed.error.message}</p>}

        {/* --- Alerts: works now --- */}
        <h2>Alerts by severity <span className="muted">(all time)</span></h2>
        <div className="tiles">
          {SEVERITIES.map((s) => (
            <StatTile key={s} label={s} value={bySeverity[s] ?? 0} color={SEVERITY_COLORS[s]} />
          ))}
        </div>

        <div className="card">
          <div className="card-head">
            <h3>Latest alerts</h3>
            <Link to="/AlertFeed">Open Alert Feed →</Link>
          </div>
          {alerts.data?.length === 0 && <p>No alerts yet.</p>}
          {alerts.data?.length > 0 && (
            <table className="table">
              <thead>
                <tr><th>Time</th><th>Severity</th><th>Type</th><th>Source</th><th>Destination</th></tr>
              </thead>
              <tbody>
                {alerts.data.slice(0, 5).map((a) => (
                  <tr key={a.id} className="clickable" onClick={() => navigate(`/AlertDetails/${a.id}`)}>
                    <td>{formatIso(a.timestamp)}</td>
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



        {c && (
          <div className="tiles">
            <StatTile label="Flows / s" value={fmtRate(c.flowsPerSec)} />
            <StatTile label="Packets / s" value={fmtRate(c.packetsPerSec)} />
            <StatTile label="Bytes / s" value={`${formatBytes(Number(c.bytesPerSec))}/s`} />
          </div>
        )}

        <div className="chart-grid">
          <section className="card">
            <div className="card-head">
              <h3>Traffic over time</h3>
              <select value={bucket} onChange={(e) => setBucket(e.target.value)}>
                <option value="1s">1 s buckets</option>
                <option value="10s">10 s buckets</option>
                <option value="60s">60 s buckets</option>
              </select>
            </div>
            {series.data?.length === 0 && <p>No flows stored yet.</p>}
            {series.data?.length > 0 && <TrafficChart points={series.data} />}
          </section>

          <section className="card">
            <h3>Top talkers (by bytes sent)</h3>
            {talkers.data?.length === 0 && <p>No flows stored yet.</p>}
            {talkers.data?.length > 0 && (
              <table className="table">
                <thead><tr><th>Source IP</th><th>Bytes</th><th>Flows</th></tr></thead>
                <tbody>
                  {talkers.data.map((t) => (
                    <tr key={t.sourceIp}>
                      <td>{t.sourceIp}</td>
                      <td>{formatBytes(Number(t.totalBytes))}</td>
                      <td>{t.flowCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
              
          </div>
        </div>
      )
    }