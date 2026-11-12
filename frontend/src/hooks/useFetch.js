  import { useEffect, useState } from 'react'

  export function useFetch(fetcher, deps) {
    const [state, setState] = useState({ data: null, error: null, loading: true })

    useEffect(() => {
      let cancelled = false
      setState({ data: null, error: null, loading: true })
      fetcher()
        .then((data) => !cancelled && setState({ data, error: null, loading: false }))
        .catch((error) => !cancelled && setState({ data: null, error, loading: false }))
      return () => { cancelled = true }
    }, deps)

    return state
  }
