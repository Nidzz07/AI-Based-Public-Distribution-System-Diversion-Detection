import { CARD } from '../ui.js'

// An empty state is a sentence, not a shrug. Each one says what is not here,
// why, and what to do next — "No results" tells a judge nothing and looks like
// a bug.
//
// Deliberately a plain hairline card with no coloured left-border: per
// CLAUDE.md that accent encodes a severity value, and an empty state has no
// severity. Spending the idiom here would blunt it on the rows that carry one.
export default function EmptyState({ title, children }) {
  return (
    <div className={`${CARD} p-6`}>
      <p className="text-body font-medium text-ink">{title}</p>
      {children ? <p className="mt-1 text-body-secondary text-ink-secondary">{children}</p> : null}
    </div>
  )
}

// The same shape for a failed fetch. Kept next to EmptyState because the two
// are read in the same slot and should not drift apart visually.
//
// Coral on the heading, not on a left-border: the border accent belongs to
// severity values on data rows, and a failed request has no severity.
export function ErrorState({ error, children }) {
  return (
    <div className={`${CARD} p-6`}>
      <p className="font-medium text-coral">Could not load this from the API</p>
      <p className="mt-1 text-body-secondary text-ink-secondary">{error}</p>
      {children ? <p className="mt-2 text-body-secondary text-ink-secondary">{children}</p> : null}
    </div>
  )
}
