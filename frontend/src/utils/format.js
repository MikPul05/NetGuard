  import { PROTOCOLS } from '../constants.js'

  export const formatIso = (iso) => (iso ? new Date(iso).toLocaleString() : '–')
  export const formatUs = (us) => (us ? new Date(us / 1000).toLocaleString() : '–')
  export const formatPercent = (x) => `${Math.round((x ?? 0) * 100)} %`
  export const formatProtocol = (n) => PROTOCOLS[n] ?? String(n)

  export function formatBytes(b) {
    if (b == null) return '–'
    if (b < 1024) return `${b} B`
    if (b < 1024 ** 2) return `${(b / 1024).toFixed(1)} KB`
    return `${(b / 1024 ** 2).toFixed(1)} MB`
  }