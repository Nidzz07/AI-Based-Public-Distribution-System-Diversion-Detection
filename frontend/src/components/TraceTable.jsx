import { TRACE_ROW } from '../severity.js'
import { COLUMN_HEAD } from '../ui.js'
import SectionHeading from './SectionHeading.jsx'

// The reasoning trace. Every rule the rulebook holds gets a row, including the
// ones that passed and the ones we could not evaluate — the trace is a record
// of what was examined, not a list of accusations.
//
// Three visually distinct states, because conflating two of them is how an
// audit system loses credibility:
//   fired   coral edge, full-strength ink, its weight in the score
//   passed  green edge, full-strength ink, a dash where the weight would be
//   skipped grey edge, SUNK GROUND, MUTED AND ITALIC — we could not check
//           this, and it must never read as "we checked and it was fine"
//
// Reading, Threshold and Weight are right-aligned with tabular figures: they
// are three columns of measurements, and a reader compares them down the
// column, not across the row.

const GRID = 'grid grid-cols-[1fr_120px_120px_88px_96px] items-center gap-4'

export default function TraceTable({ hits }) {
  return (
    <section>
      <SectionHeading title="Reasoning trace">
        Every rule in the rulebook, what it read, and what it did about it — including the rules
        that passed and the ones there was no reading for.
      </SectionHeading>

      {/* bg-bg on the header row for the same reason the heading is plated: the
          column labels sit on bare ground, and a ruled motif behind them reads
          as a line struck through the table's top edge. */}
      <div className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}>
        <span className={COLUMN_HEAD}>Rule</span>
        <span className={`${COLUMN_HEAD} text-right`}>Reading</span>
        <span className={`${COLUMN_HEAD} text-right`}>Threshold</span>
        <span className={`${COLUMN_HEAD} text-right`}>Weight</span>
        <span className={COLUMN_HEAD}>Status</span>
      </div>

      <ul>
        {hits.map((hit) => {
          const state = TRACE_ROW[hit.status] ?? TRACE_ROW.passed
          return (
            <li
              key={hit.rule_id}
              // Not the shared CARD class: CARD sets bg-surface, and the
              // skipped row needs bg-surface-sunk. Two background utilities of
              // equal specificity are resolved by stylesheet order, not by the
              // order written here, so the greyed row would win or lose at
              // random. Same radius and shadow tokens, background left to the
              // state.
              className={`${GRID} ${state.row} mt-2 rounded border-y border-r border-border border-l-4 ${state.border} px-4 py-4 shadow-card`}
            >
              <span>
                <span className="block text-table-cell">{hit.label}</span>
                <span className="block text-meta-label text-ink-muted">{hit.rule_id}</span>
              </span>

              <span className="num text-right text-table-cell">
                {/* A null reading is the whole point of a skipped row: there
                    was nothing to quote. */}
                {hit.raw_value ?? 'no reading'}
              </span>

              <span className="num text-right text-table-cell">{hit.threshold}</span>

              <span className="num text-right text-table-cell">
                {hit.status === 'fired' ? `+${hit.contribution}` : '—'}
              </span>

              <span className={`text-table-cell ${state.labelClass}`}>{state.label}</span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
