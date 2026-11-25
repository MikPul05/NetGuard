 import { useEffect, useState } from 'react'
  import { getDetectionConfig, getSources, saveDetectionConfig } from '../api/config.js'
  import { ConfigField } from '../components/ConfigField.jsx'
  import { CONFIG_SECTIONS, DEFAULT_CONFIG } from '../configFields.js'
  import { useFetch } from '../hooks/useFetch.js'
  import { fieldId, fromForm, toForm } from '../utils/configForm.js'

  export function Config() {
    const [config, setConfig] = useState(null)        // last loaded / saved config
    const [form, setForm] = useState(null)            // what is in the inputs now
    const [loadError, setLoadError] = useState(null)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState(null)      // { ok: true/false, text }
    const sources = useFetch(getSources, [])

    useEffect(() => {
      getDetectionConfig()
        .then((c) => { setConfig(c); setForm(toForm(c)) })
        .catch((e) => setLoadError(e.message))
    }, [])

    if (loadError) return <div><h1>Configuration</h1><p className="error">Could not load configuration: {loadError}</p></div>
    if (!form) return <div><h1>Configuration</h1><p>Loading…</p></div>

    const { config: newConfig, errors } = fromForm(form, config)
    const hasErrors = Object.keys(errors).length > 0
    const dirty = JSON.stringify(form) !== JSON.stringify(toForm(config))

    const update = (id) => (value) => {
      setForm({ ...form, [id]: value })
      setMessage(null)
    }

    function fillForm(source) {
      setForm(toForm(source))
      setMessage(null)
    }

    async function save(e) {
      e.preventDefault()
      setSaving(true)
      try {
        const res = await saveDetectionConfig(newConfig)
        setConfig(res.config)
        setForm(toForm(res.config))
        setMessage(res.warning ? { ok: false, text: res.warning } : { ok: true, text: 'Configuration saved.' })
      } catch (err) {
        setMessage({ ok: false, text: `Save failed: ${err.response?.data?.error ?? err.message}` })
      } finally {
        setSaving(false)
      }
    }

    return (
      <div>
        <h1>Configuration</h1>
        <p className="preview-note">
          Administrative page. Saved values are stored by the backend, but the running detector
          does not reload them yet. Login is out of scope, so this page is not protected.
        </p>

        <form onSubmit={save}>
          {CONFIG_SECTIONS.map((section) => (
            <section key={section.title} className="card">
              <h3>{section.title}</h3>
              {section.fields.map((field) => {
                const id = fieldId(section, field)
                return <ConfigField key={id} field={field} value={form[id]} error={errors[id]} onChange={update(id)} />
              })}
            </section>
          ))}

          <div className="config-actions">
            <button type="submit" disabled={!dirty || hasErrors || saving}>{saving ? 'Saving…' : 'Save changes'}</button>
            <button type="button" disabled={!dirty} onClick={() => fillForm(config)}>Discard changes</button>
            <button type="button" onClick={() => fillForm(DEFAULT_CONFIG)}>Restore defaults</button>
            {hasErrors && <span className="error">Fix the marked fields before saving.</span>}
            {message && <span className={message.ok ? 'ok' : 'error'}>{message.text}</span>}
          </div>
        </form>

        <h2>Data sources</h2>
        <p className="muted">
          Capture and flow files in the platform's data folder. They are imported with the
          command-line tools (see README).
        </p>
        {sources.error && <p className="error">Could not load sources: {sources.error.message}</p>}
        {sources.loading && <p>Loading…</p>}
        {sources.data?.length > 0 && (
          <table className="table">
            <thead><tr><th>File</th><th>Kind</th></tr></thead>
            <tbody>
              {sources.data.map((f) => (
                <tr key={f}>
                  <td>{f}</td>
                  <td>{f.endsWith('.jsonl') ? 'Flow records (JSONL)' : 'Packet capture (PCAP)'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    )
  }