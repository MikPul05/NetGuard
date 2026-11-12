 import { useState } from 'react'
  import { getEvidence } from '../api/detections.js'
  import { useFetch } from '../hooks/useFetch.js'
  import { formatPercent } from '../utils/format.js'
  import { SeverityBadge } from './SeverityBadge.jsx'
  import { EvidenceTable, StatisticalSummary } from './EvidenceTable.jsx'
  import { TraceSection } from './TraceSection.jsx'

  export function DetectionCard({ detection }) {
    const [showTrace, setShowTrace] = useState(false)
    const ev = useFetch(() => getEvidence(detection.detectionId), [detection.detectionId])

    // statistical-only detections keep z-score data in "evidence"; combined ones in "statisticalEvidence"
    const stats = ev.data?.statisticalEvidence ?? (ev.data?.evidence?.zScore != null ? ev.data.evidence : null)

    return (
      <section className="card">
        <div className="card-head">
          <h3>Detection <code>{detection.detectionId}</code></h3>
          <div className="chips">
            <SeverityBadge severity={detection.severity} />
            {detection.methods.map((m) => <span key={m} className="chip">{m}</span>)}
          </div>
        </div>

        <div className="facts">
          <div>
            Confidence
            <div className="bar"><div style={{ width: formatPercent(detection.confidence) }} /></div>
            {formatPercent(detection.confidence)}
          </div>
          <div>Window<br /><b>{detection.window}</b></div>
        </div>

        <p className="explanation">{detection.explanation}</p>

        <h4>Evidence</h4>
        {ev.loading && <p>Loading evidence…</p>}
        {ev.error && <p className="error">Could not load evidence: {ev.error.message}</p>}
        {ev.data && (
          <>
            <EvidenceTable evidence={ev.data.evidence} thresholds={ev.data.thresholds} />
            <StatisticalSummary stats={stats} threshold={ev.data.thresholds?.zScore} />
          </>
        )}

        <button className="btn" onClick={() => setShowTrace((s) => !s)}>
          {showTrace ? 'Hide contributing flows' : 'Show contributing flows'}
        </button>
        {showTrace && <TraceSection detectionId={detection.detectionId} />}
      </section>
    )
  }