 import { useEffect, useState } from 'react'

  export function usePolling(fetcher, deps, intervalMs) {
    const [state, setState] = useState({ data: null, error: null })

    useEffect(() => {
      let cancelled = false

      async function load() {
        try {
          const data = await fetcher()
          if (!cancelled) setState({ data, error: null })
        } catch (error) {
          if (!cancelled) setState((s) => ({ ...s, error }))   // keep last good data
        }
      }

      setState({ data: null, error: null })
      load()
      const timer = setInterval(load, intervalMs)
      return () => { cancelled = true; clearInterval(timer) }    // stop when leaving the page
    }, deps)

    return state
  }