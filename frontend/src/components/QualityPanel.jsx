 import { useState } from 'react'
  import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
  import { getQuality, getRuns } from '../api/stats.js'
  import { TYPE_LABELS } from '../constants.js'
  import { useFetch } from '../hooks/useFetch.js'

  const fmt = (x) => (x ?? 0).toFixed(3)

  export function QualityPanel() {
    const runs = useFetch(getRuns, [])
    const [runId, setRunId] = useState('')                 // '' = latest run
    const quality = useFetch(() => getQuality(runId), [runId])

    const q = quality.data
    // backend spells this key two ways (detectedAttacks / detected_attacks)
    const attacks = q?.detectedAttacks ?? q?.detected_attacks ?? []

    return (
      <div>
        <label className="muted">Evaluation run:{' '}
          <select value={runId} onChange={(e) => setRunId(e.target.value)}>
            <option value="">Latest</option>
            {runs.data?.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>

        {quality.error && <p className="error">Could not load quality metrics: {quality.error.message}</p>}
        {quality.loading && <p>Loading…</p>}
        {q?.runId === 'none' && <p>No evaluation results stored for this run.</p>}

        {q && q.runId !== 'none' && (
          <div className="chart-grid">
            <section className="card">
              <h3>Run {q.runId}</h3>
              <table className="table">
                <thead><tr><th></th><th>Detected</th><th>Not detected</th></tr></thead>
                <tbody>
                  <tr><th>Attack</th><td>TP {q.TP}</td><td>FN {q.FN}</td></tr>
                  <tr><th>Normal</th><td>FP {q.FP}</td><td>TN {q.TN}</td></tr>
                </tbody>
              </table>
              <table className="table">
                <tbody>
                  <tr><th>Precision</th><td>{fmt(q.precision)}</td></tr>
                  <tr><th>Recall</th><td>{fmt(q.recall)}</td></tr>
                  <tr><th>F1</th><td>{fmt(q.F1)}</td></tr>
                  <tr><th>False-positive rate</th><td>{fmt(q.FPR)}</td></tr>
                  <tr><th>False-negative rate</th><td>{fmt(q.FNR)}</td></tr>
                </tbody>
              </table>
              <p className="muted">
                Detected attack types: {attacks.length ? attacks.map((t) => TYPE_LABELS[t] ?? t).join(', ') : '–'}
              </p>
            </section>

            <section className="card">
              <h3>Precision / Recall / F1</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={[
                  { name: 'Precision', value: q.precision },
                  { name: 'Recall', value: q.recall },
                  { name: 'F1', value: q.F1 },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 1]} />
                  <Tooltip formatter={(v) => fmt(v)} />
                  <Bar dataKey="value" name="Score" fill="#16a34a" />
                </BarChart>
              </ResponsiveContainer>
            </section>
          </div>
        )}
      </div>
    )
  }