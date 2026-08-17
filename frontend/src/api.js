// Single fetch wrapper. Every network call in the app goes through apiFetch()
// so that flipping USE_MOCK is the only change needed to move the whole
// frontend from the frozen contract file onto the live backend.

import caseDetail from '@contract/case_detail.json'

// The engine, the routers and the derivation path all exist now, so the app
// reads the real backend. The mock path is kept, not deleted: it is the only
// way to open the UI when the API is down, and docs/contract/case_detail.json
// is still the shape both sides are held to.
export const USE_MOCK = false

const API_BASE = 'http://localhost:8000'

// The only fixture the contract currently freezes is one case detail.
// Anything else has to fail loudly rather than return a plausible-looking
// empty object — a silent {} is how a page ends up rendering fake zeros.
function resolveMock(path) {
  if (/^\/api\/cases\/[^/]+$/.test(path)) return caseDetail
  throw new Error(
    `No mock fixture for ${path}. Add it to docs/contract/ or set USE_MOCK = false.`,
  )
}

export async function apiFetch(path, options = {}) {
  if (USE_MOCK) {
    // Structured-cloned so a page mutating the response cannot corrupt the
    // fixture for every later read in the same session.
    return structuredClone(resolveMock(path))
  }

  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`${options.method ?? 'GET'} ${path} failed: ${response.status}`)
  }

  return response.json()
}
