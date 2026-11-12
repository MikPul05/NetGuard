  import { getTrace } from '../api/detections.js'
  import { useFetch } from '../hooks/useFetch.js'
  import { formatBytes, formatProtocol, formatUs } from '../utils/format.js'

  export function TraceSection({ detectionId }) {
    const { data, error, loading } = useFetch(() => getTrace(detectionId), [detectionId])

    if (loading) return <p>Loading flows…</p>
    if (error) return <p className="error">Could not load trace: {error.message}</p>

    return (
      <div className="trace">
        <p className="muted">
          Source: <b>{data.inputSource?.file ?? 'unknown'}</b> · window start {formatUs(data.windowStartUnixUs)}
          {' '}· {data.contributingFlowCount} flow(s){data.contributingFlowCount >= 100 && ' (first 100 shown)'}
        </p>
        {data.flows.length === 0 ? (
          <p className="muted">No stored flows match this detection.</p>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Start</th><th>Source</th><th>Destination</th><th>Port</th><th>Protocol</th><th>Packets</th><th>Bytes</th></tr>
            </thead>
            <tbody>
              {data.flows.map((f) => (
                <tr key={f.flowId}>
                  <td>{formatUs(f.startTimeUnixUs)}</td>
                  <td>{f.sourceIp}</td>
                  <td>{f.destinationIp}</td>
                  <td>{f.destinationPort ?? '–'}</td>
                  <td>{formatProtocol(f.protocol)}</td>
                  <td>{f.packets}</td>
                  <td>{formatBytes(f.bytes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    )
  }