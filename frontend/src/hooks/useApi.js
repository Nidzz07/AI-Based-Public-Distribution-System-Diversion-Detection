import { useCallback, useEffect, useState } from 'react'

import { apiFetch } from '../api.js'

// One fetch hook for every page. Before this existed each page carried its own
// useEffect with its own loading and error handling, and they had already
// started to disagree about what "loading" meant.
//
// `path` of null means "nothing to fetch yet" — an unselected case is not a
// failed request, and the caller gets idle:true rather than a spurious error.
//
// WHY THIS SHAPE, and not three useStates. An earlier version stored data,
// error and loading as three independent pieces of state and flipped them by
// hand. Nothing kept them consistent, and the combination that broke the UI was
// `loading: true` alongside a data value left over from the PREVIOUS request:
// every page renders its skeleton on `loading` and its content on `data` as two
// separate tests, so both appeared at once — grey placeholder bars stacked on
// top of a fully drawn table. It showed up wherever a second request followed a
// first: the Auditor's case dropdown changing the path, or reload() after a
// note was posted.
//
// So the three are no longer independent. One piece of state holds the settled
// response TOGETHER WITH the request it belongs to, and `loading` is derived by
// comparing that against the request currently being asked for. This makes the
// invariant structural rather than something each page has to remember:
//
//     loading === true  implies  data === null && error === null
//
// There is therefore no ordering of effects, no double-invoked StrictMode mount
// and no mid-flight path change that can produce a frame showing a skeleton and
// real content together — not because the flags are set in the right order, but
// because the state that would have to exist to render both cannot be spelled.
//
// It also fixes a correctness bug that mattered more than the cosmetics: while
// a new case's audit trail was in flight, the PREVIOUS case's events stayed on
// screen under the new case's heading. An append-only trail that shows the
// wrong case's rows, however briefly, is worse than one that shows nothing.
export function useApi(path) {
  // The request identity. nonce is part of it so reload() re-fetches the same
  // path and is correctly treated as a new request rather than as one already
  // answered. nonce is a number and every path begins with "/", so the space
  // joining them cannot be ambiguous.
  const [nonce, setNonce] = useState(0)
  const key = path ? `${nonce} ${path}` : null

  // The settled response and the key it answers. Never read directly — read
  // through the derivations below, which discard it unless it matches.
  const [settled, setSettled] = useState({ key: null, data: null, error: null })

  const answered = settled.key === key
  const data = answered ? settled.data : null
  const error = answered ? settled.error : null
  // Derived, not stored: there is a request and it has not been answered yet.
  // Because it is derived during render, a path change already reads as
  // "loading" on the very first render after the change — before any effect has
  // run — which is the frame the old version rendered stale content in.
  const loading = key !== null && !answered

  useEffect(() => {
    if (!key) return undefined

    let live = true

    apiFetch(path)
      .then((result) => {
        if (live) setSettled({ key, data: result, error: null })
      })
      .catch((err) => {
        // data goes to null on failure. A page shows either an error or a
        // result, never an error above the stale rows it replaced.
        if (live) setSettled({ key, data: null, error: err.message })
      })

    // A page can be navigated away from mid-request; without this the response
    // lands on an unmounted component and React warns.
    return () => {
      live = false
    }
  }, [key, path])

  const reload = useCallback(() => setNonce((n) => n + 1), [])

  return { data, error, loading, idle: !path, reload }
}
