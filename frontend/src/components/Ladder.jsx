import { formatKg, formatPct } from '../severity.js'
import { CARD, COLUMN_HEAD } from '../ui.js'
import SectionHeading from './SectionHeading.jsx'

// The four-hop reconciliation ladder — the core insight on one line:
// allocated -> dispatched -> weighed -> dispensed, with what was lost between
// each pair, and the located gap called out.
//
// Deliberately not a table. A table invites reading four independent numbers;
// the point is that these are four readings of the SAME grain, and the story
// is the drop between them. Nodes and connectors say that; rows do not.
//
// The kg figures are ink, not navy: they are data, and navy is reserved for
// headings and the score-display. The only colour on the ladder is coral on
// the one connector where the grain actually went — colour as signal, spent
// once.

const STAGES = [
  { key: 'allocated_kg', label: 'Allocated', source: 'Government allocation order' },
  { key: 'dispatched_kg', label: 'Dispatched', source: 'FCI depot weighbridge' },
  { key: 'weighed_kg', label: 'Received', source: 'Shop weighing scale' },
  { key: 'dispensed_kg', label: 'Dispensed', source: 'ePoS counter total' },
]

// Each connector sits between two stages and carries the hop id the backend
// uses, so "which hop is highlighted" is decided by the API's gap_hop and not
// by anything this component infers.
const HOPS = [
  { id: 'allocation_to_dispatch', from: 'allocated_kg', to: 'dispatched_kg', variance: null },
  {
    id: 'dispatch_to_receipt',
    from: 'dispatched_kg',
    to: 'weighed_kg',
    variance: 'variance_dispatch_to_receipt',
  },
  {
    id: 'receipt_to_counter',
    from: 'weighed_kg',
    to: 'dispensed_kg',
    variance: 'variance_receipt_to_counter',
  },
]

function Node({ stage, value }) {
  const missing = value === null || value === undefined

  return (
    <div className={`${CARD} min-w-[128px] flex-1 p-4`}>
      <p className={COLUMN_HEAD}>{stage.label}</p>
      {missing ? (
        // F5 on the ladder itself: a rung we have no reading for shows as
        // unreported, never as zero.
        <p className="mt-1 font-display text-section-heading italic text-ink-muted">
          not reported
        </p>
      ) : (
        <p className="num mt-1 font-display text-section-heading text-ink">
          {formatKg(value)} <span className="text-body-secondary text-ink-secondary">kg</span>
        </p>
      )}
      {/* The instrument each reading came from. Sits at meta size but in
          sentence case, not tracked caps — it is a source note, not a column
          label. */}
      <p className="mt-2 text-body-secondary text-ink-secondary">{stage.source}</p>
    </div>
  )
}

function Connector({ hop, cycle, located }) {
  const from = cycle[hop.from]
  const to = cycle[hop.to]
  const measurable = from !== null && from !== undefined && to !== null && to !== undefined

  // kg is exact subtraction of two stored readings. The percentage is the
  // BACKEND's variance wherever the backend has one — recomputing it here
  // would give the trace table and the ladder two roundings of one number.
  const deltaKg = measurable ? to - from : null
  const pct = hop.variance ? cycle[hop.variance] : measurable ? ((to - from) / from) * 100 : null

  const tone = located ? 'text-coral' : 'text-ink-secondary'
  const rule = located ? 'bg-coral' : 'bg-border-strong'

  return (
    <div className="flex min-w-[112px] shrink-0 flex-col items-center justify-center px-2">
      <p className={`num text-body-secondary font-medium ${tone}`}>
        {measurable ? `${deltaKg > 0 ? '+' : ''}${formatKg(deltaKg)} kg` : '—'}
      </p>
      <div className={`my-1 h-px w-full ${rule}`} />
      <p className={`num text-body-secondary ${tone}`}>
        {pct === null || pct === undefined ? 'not measurable' : formatPct(pct)}
      </p>
      {located ? (
        <p className="mt-1 text-center text-meta-label uppercase text-coral">gap located</p>
      ) : null}
    </div>
  )
}

export default function Ladder({ cycle, gapHop }) {
  return (
    <section>
      <SectionHeading title="Reconciliation ladder">
        Four readings of the same consignment, from allocation order to counter. The gap is where
        they stop agreeing.
      </SectionHeading>

      {/* Scrolls rather than wraps: a ladder that wraps stops reading as a
          single chain, which is the one thing it has to do.

          bg-bg is not a visual change — it is the page ground, painted at the
          same value it already had. It is here so the connector labels below,
          which are the only text in the app that sits on bare ground rather
          than on a card, have an opaque backing and the page motif cannot
          reach them. The coral on a located gap is the lowest-contrast type
          in the build; nothing is allowed to sit behind it. */}
      <div className="mt-4 flex items-stretch overflow-x-auto bg-bg pb-2">
        {STAGES.map((stage, index) => (
          <div key={stage.key} className="flex items-stretch">
            <Node stage={stage} value={cycle[stage.key]} />
            {index < HOPS.length ? (
              <Connector hop={HOPS[index]} cycle={cycle} located={HOPS[index].id === gapHop} />
            ) : null}
          </div>
        ))}
      </div>
    </section>
  )
}
