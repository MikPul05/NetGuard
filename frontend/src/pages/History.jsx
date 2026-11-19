 import { useEffect, useState } from 'react'
  import { useNavigate, useSearchParams } from 'react-router-dom'
  import { searchAlerts } from '../api/alerts.js'
  import { Pagination } from '../components/Pagination.jsx'
  import { SeverityBadge } from '../components/SeverityBadge.jsx'
  import { SEVERITIES, TYPE_LABELS } from '../constants.js'
  import { useFetch } from '../hooks/useFetch.js'
  import { formatIso } from '../utils/format.js'

  const FILTER_KEYS = ['from', 'to', 'type', 'severity', 'sourceIp', 'destinationIp']
  const PAGE_SIZE = 20

  // Filter values currently in the URL (missing ones become '')
  function readFilters(searchParams) {
    return Object.fromEntries(FILTER_KEYS.map((key) => [key, searchParams.get(key) ?? '']))
  }

  // Query for GET /alerts: skip empty fields, send times as UTC ISO strings
  function toApiParams(searchParams) {
    const params = {
      page: searchParams.get('page') ?? 1,
      size: PAGE_SIZE,
      sort: searchParams.get('sort') ?? '-timestamp',
    }
    for (const key of FILTER_KEYS) {
      const value = searchParams.get(key)
      if (!value) continue
      params[key] = key === 'from' || key === 'to' ? new Date(value).toISOString() : value
    }
    return params
  }

  export function Hist() {
    const [searchParams, setSearchParams] = useSearchParams()
    const [draft, setDraft] = useState(() => readFilters(searchParams))  // form fields before "Search"
    const navigate = useNavigate()

    const query = searchParams.toString()
    const { data, error, loading } = useFetch(() => searchAlerts(toApiParams(searchParams)), [query])

    // Keep the form in sync when the URL changes (e.g. browser Back button)
    useEffect(() => { setDraft(readFilters(searchParams)) }, [query])

    const change = (key) => (e) => setDraft({ ...draft, [key]: e.target.value })

    // Copy the filled-in fields into the URL -> triggers a new request, back to page 1
    function applyFilters(e) {
      e.preventDefault()
      const next = {}
      for (const key of FILTER_KEYS) if (draft[key].trim()) next[key] = draft[key].trim()
      const sort = searchParams.get('sort')
      if (sort) next.sort = sort
      setSearchParams(next)
    }

    function resetFilters() {
      setSearchParams({})
    }

    // Change one URL value (page or sort) and keep the filters
    function setParam(key, value) {
      const next = new URLSearchParams(searchParams)
      next.set(key, value)
      if (key === 'sort') next.delete('page')
      setSearchParams(next)
    }

    return (
      <div>
        <h1>Alert History</h1>

        <form className="filters" onSubmit={applyFilters}>
          <label>From
            <input type="datetime-local" value={draft.from} onChange={change('from')} />
          </label>
          <label>To
            <input type="datetime-local" value={draft.to} onChange={change('to')} />
          </label>
          <label>Type
            <select value={draft.type} onChange={change('type')}>
              <option value="">All</option>
              {Object.entries(TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
          <label>Severity
            <select value={draft.severity} onChange={change('severity')}>
              <option value="">All</option>
              {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label>Source IP
            <input value={draft.sourceIp} onChange={change('sourceIp')} placeholder="e.g. 192.168.1.17" />
          </label>
          <label>Destination IP
            <input value={draft.destinationIp} onChange={change('destinationIp')} placeholder="e.g. 10.0.0.53" />
          </label>
          <div className="filter-buttons">
            <button type="submit">Search</button>
            <button type="button" onClick={resetFilters}>Reset</button>
          </div>
        </form>

        <label className="muted">Sort:{' '}
          <select value={searchParams.get('sort') ?? '-timestamp'} onChange={(e) => setParam('sort', e.target.value)}>
            <option value="-timestamp">Newest first</option>
            <option value="timestamp">Oldest first</option>
            <option value="type">Type (A–Z)</option>
          </select>
        </label>

        {error && <p className="error">Could not load alerts: {error.message}</p>}
        {loading && <p>Loading…</p>}
        {data?.total === 0 && <p>No alerts match these filters.</p>}

        {data?.alerts.length > 0 && (
          <>
            <p className="muted">{data.total} alerts found</p>
            <table className="table">
              <thead>
                <tr><th>Time</th><th>Severity</th><th>Type</th><th>Source</th><th>Destination</th></tr>
              </thead>
              <tbody>
                {data.alerts.map((a) => (
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
            <Pagination page={data.page} size={data.size} total={data.total}
                        onChange={(p) => setParam('page', p)} />
          </>
        )}
      </div>
    )
  }