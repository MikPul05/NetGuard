  import { FEATURE_OPTIONS, WINDOW_OPTIONS } from '../configFields.js'

  export function ConfigField({ field, value, error, onChange }) {
    let input

    if (field.type === 'bool') {
      input = <input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} />
    } else if (field.type === 'window') {
      // keep an unusual value from the file selectable instead of silently changing it
      const options = WINDOW_OPTIONS.includes(Number(value)) ? WINDOW_OPTIONS : [...WINDOW_OPTIONS, Number(value)]
      input = (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          {options.map((s) => <option key={s} value={s}>{s} s</option>)}
        </select>
      )
    } else if (field.type === 'features') {
      input = (
        <div className="checks">
          {Object.entries(FEATURE_OPTIONS).map(([key, label]) => (
            <label key={key}>
              <input
                type="checkbox"
                checked={value.includes(key)}
                onChange={(e) => onChange(e.target.checked ? [...value, key] : value.filter((f) => f !== key))}
              />{' '}{label}
            </label>
          ))}
        </div>
      )
    } else {
      input = <input value={value} onChange={(e) => onChange(e.target.value)} />
    }

    return (
      <div className="config-field">
        <span className="config-label">{field.label}</span>
        <div>
          {input}
          {field.help && <div className="muted">{field.help}</div>}
          {error && <div className="error">{error}</div>}
        </div>
      </div>
    )
  }