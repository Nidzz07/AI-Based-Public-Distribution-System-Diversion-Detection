import { useCallback, useEffect, useState } from 'react'

import { apiFetch } from '../api.js'

// One fetch hook for every page. Before this existed each page carried its own
// useEffect with its own loading and error handling, and they had already
// started to disagree about what "loading" meant.
//
// `path` of null means "nothing to fetch yet" — an unselected case is not a
// failed request, and the caller gets idle:true rather than a spurious error.
export function useApi(path) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(Boolean(path))
  // Bumping this re-runs the effect. Used by reload() after a POST, so a page
  // shows what the server actually stored rather than what it hoped it stored.
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    if (!path) {
      setData(null)
      setLoading(false)
      return undefined
    }

    let live = true
    setLoading(true)
    setError(null)

    apiFetch(path)
      .then((result) => {
        if (!live) return
        setData(result)
        setLoading(false)
      })
      .catch((err) => {
        if (!live) return
        setError(err.message)
        setLoading(false)
      })

    // A page can be navigated away from mid-request; without this the response
    // lands on an unmounted component and React warns.
    return () => {
      live = false
    }
  }, [path, nonce])

  const reload = useCallback(() => setNonce((n) => n + 1), [])

  return { data, error, loading, idle: !path, reload }
}
