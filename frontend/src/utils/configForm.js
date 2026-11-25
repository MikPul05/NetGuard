  import { CONFIG_SECTIONS } from '../configFields.js'

  const getIn = (obj, path) => path.reduce((o, k) => o?.[k], obj)

  function setIn(obj, path, value) {
    let o = obj
    for (const k of path.slice(0, -1)) o = o[k] ??= {}
    o[path.at(-1)] = value
  }

  export const fieldId = (section, field) => [...section.path, field.key].join('.')

  const allFields = () => CONFIG_SECTIONS.flatMap((s) =>
    s.fields.map((f) => ({ field: f, path: [...s.path, f.key], id: fieldId(s, f) })))

  // config object -> flat form values ({ 'rules.dos.window_seconds': '10', ... })
  // numbers are kept as text so the user can type freely
  export function toForm(config) {
    const form = {}
    for (const { field, path, id } of allFields()) {
      const v = getIn(config, path)
      if (field.type === 'bool') form[id] = Boolean(v)
      else if (field.type === 'features') form[id] = Array.isArray(v) ? v : []
      else if (field.type === 'ports') form[id] = Array.isArray(v) ? v.join(', ') : ''
      else form[id] = v == null ? '' : String(v)
    }
    return form
  }

  // one form value -> [parsed value, error message or null]
  function parse(field, raw) {
    switch (field.type) {
      case 'bool':
        return [raw, null]
      case 'features':
        return [raw, raw.length ? null : 'Select at least one feature']
      case 'window':
        return [Number(raw), null]
      case 'ports': {
        const ports = raw.split(',').map((p) => p.trim()).filter(Boolean).map(Number)
        if (!ports.length) return [ports, 'Enter at least one port']
        if (ports.some((p) => !Number.isInteger(p) || p < 1 || p > 65535)) return [ports, 'Ports must be whole numbers 1–65535']
        return [ports, null]
      }
      case 'int': {
        const n = Number(raw)
        if (raw.trim() === '' || !Number.isInteger(n)) return [n, 'Enter a whole number']
        return [n, n < field.min ? `Must be at least ${field.min}` : null]
      }
      case 'float': {
        const n = Number(raw)
        if (raw.trim() === '' || Number.isNaN(n)) return [n, 'Enter a number']
        return [n, n <= field.min ? `Must be greater than ${field.min}` : null]
      }
      default:
        return [raw, null]
    }
  }

  // form values + loaded config -> { config to send, errors by field id }
  // starts from the loaded config, so values the form doesn't show are kept
  export function fromForm(form, original) {
    const config = structuredClone(original)
    const errors = {}
    for (const { field, path, id } of allFields()) {
      const [value, error] = parse(field, form[id])
      if (error) errors[id] = error
      else setIn(config, path, value)
    }
    return { config, errors }
  }