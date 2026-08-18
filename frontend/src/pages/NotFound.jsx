import { Link } from 'react-router-dom'

import PageHeader from '../components/PageHeader.jsx'
import { BUTTON, CARD } from '../ui.js'

// CLAUDE.md bans unstyled 404s. A wrong URL in front of judges should look
// like part of the product, not like a stack trace. It uses the same header
// band and content region as every other screen for exactly that reason.
export default function NotFound() {
  return (
    <article className="flex-1">
      <PageHeader
        title="No such screen"
        note="That route is not part of this build."
      />

      <div className="px-8 py-8">
        {/* Same CARD and BUTTON tokens as every other screen, rather than a
            hand-rolled border and a hand-rolled link. A 404 that styles itself
            is a 404 that drifts. */}
        <div className={`${CARD} min-h-region max-w-4xl p-8`}>
          <p className="text-body-secondary text-ink-secondary">
            Check the address, or start again from the ranked case list.
          </p>
          <Link to="/" className={`${BUTTON} mt-4 inline-block`}>
            Back to the case list
          </Link>
        </div>
      </div>
    </article>
  )
}
