 import { FEATURE_LABELS, STAT_META_KEYS } from '../constants.js'

  const label = (key) => FEATURE_LABELS[key] ?? key

  export function EvidenceTable({ evidence, thresholds }) {
    const rows = Object.entries(evidence ?? {}).filter(([k]) => !STAT_META_KEYS.includes(k))
    if (rows.length === 0) return <p className="muted">No evidence recorded.</p>

    return (
      <table className="table evidence">
        <thead><tr><th>Feature</th><th>Value</th><th>Threshold</th><th></th></tr></thead>
        <tbody>
          {rows.map(([key, value]) => {
            const limit = thresholds?.[key]
            const exceeded = limit != null && value >= limit
            return (
              <tr key={key} className={exceeded ? 'exceeded' : ''}>
                <td>{label(key)}</td>
                <td>{value}</td>
                <td>{limit ?? '–'}</td>
                <td>{exceeded && '▲ exceeded'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    )
  }

  export function StatisticalSummary({ stats, threshold }) {
    if (!stats?.zScore) return null
    return (
      <p className="stat-summary">
        Statistical: z-score <b>{stats.zScore}</b> on <b>{label(stats.zScoreFeature)}</b>
        {' '}(baseline {stats.baselineMean} ± {stats.baselineStd}
        {threshold != null && `, threshold ${threshold}`})
      </p>
    )
  }