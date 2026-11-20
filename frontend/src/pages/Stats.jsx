 import { useState } from 'react'
  import { getMethods, getSummary } from '../api/stats.js'
  import { CountBarChart } from '../components/CountBarChart.jsx'
  import { QualityPanel } from '../components/QualityPanel.jsx'
  import { METHOD_LABELS, SEVERITIES, SEVERITY_COLORS, TYPE_LABELS } from '../constants.js'
  import { useFetch } from '../hooks/useFetch.js'

  // { PORT_SCAN: 3 } -> [{ key, name, count }], known keys first (with 0s), then any unknown ones
  function toRows(counts, keys, labels = {}) {
    const all = [...new Set([...keys, ...Object.keys(counts)])]
    return all.map((key) => ({ key, name: labels[key] ?? key, count: counts[key] ?? 0 }))
  }

  function StateText({ state, what }) {
    if (state.error) return <p className="error">Could not load {what}: {state.error.message}</p>
    if (state.loading) return <p>Loading…</p>
    return null
  }

  const EMPTY_RANGE = { from: '', to: '' }

  export function Stats() {
    const [draft, setDraft] = useState(EMPTY_RANGE)
    const [range, setRange] = useState(EMPTY_RANGE)      // applied range

    // backend filters only when BOTH dates are given
    const summary = useFetch(
      () => getSummary(range.from && range.to
        ? { from: new Date(range.from).toISOString(), to: new Date(range.to).toISOString() }
        : {}),
      [range.from, range.to],
    )
    const methods = useFetch(getMethods, [])

    const incomplete = !draft.from !== !draft.to         // exactly one date filled in
    const total = summary.data ? Object.values(summary.data.bySeverity).reduce((a, b) => a + b, 0) : 0

    function apply(e) {
      e.preventDefault()
      setRange(draft)
    }

    function showAllTime() {
      setDraft(EMPTY_RANGE)
      setRange(EMPTY_RANGE)
    }

    return (
      <div>
        <h1>Statistics</h1>

        <form className="filters" onSubmit={apply}>
          <label>From
            <input type="datetime-local" value={draft.from} onChange={(e) => setDraft({ ...draft, from: e.target.value })} />
          </label>
          <label>To
            <input type="datetime-local" value={draft.to} onChange={(e) => setDraft({ ...draft, to: e.target.value })} />
          </label>
          <div className="filter-buttons">
            <button type="submit" disabled={incomplete}>Apply</button>
            <button type="button" onClick={showAllTime}>All time</button>
          </div>
        </form>
        {incomplete && <p className="muted">Set both dates to filter by time.</p>}

        <h2>Alerts {range.from ? 'in selected period' : '(all time)'}</h2>
        <StateText state={summary} what="alert statistics" />
        {summary.data && (
          <>
            <p className="muted">{total} alerts in total</p>
            <div className="chart-grid">
              <section className="card">
                <h3>By type</h3>
                <CountBarChart data={toRows(summary.data.byType, Object.keys(TYPE_LABELS), TYPE_LABELS)} />
              </section>
              <section className="card">
                <h3>By severity</h3>
                <CountBarChart data={toRows(summary.data.bySeverity, SEVERITIES)} colors={SEVERITY_COLORS} height={200} />
              </section>
            </div>
          </>
        )}

        <h2>Detections by method <span className="muted">(all time)</span></h2>
        <StateText state={methods} what="method statistics" />
        {methods.data && (
          <section className="card">
            <CountBarChart data={toRows(methods.data, Object.keys(METHOD_LABELS), METHOD_LABELS)} height={160} />
          </section>
        )}

        <h2>Detection quality</h2>
        <QualityPanel />
      </div>
    )
}