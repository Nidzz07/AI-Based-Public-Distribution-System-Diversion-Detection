import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonRows } from '../components/Skeleton.jsx'
import Tag, { SeverityTag } from '../components/Tag.jsx'
import { useApi } from '../hooks/useApi.js'
import { OPERATOR_SYMBOL } from '../severity.js'
import { CARD, CELL, CELL_MUTED, COLUMN_HEAD, ROW } from '../ui.js'

// This is the page that makes the rulebook an officer's document rather than a
// developer's config file. It renders app/rules.yaml as served, so an edit to
// the YAML shows up on a refresh with no code change — which is the whole
// point of F2 and worth being able to demonstrate live.
//
// Rendered as a legible rulebook, not a JSON dump: each rule reads across its
// row as a sentence ("Weighing shortfall · variance_dispatch_to_receipt ·
// < -5.0%") with its weight in a column an officer can add up.
//
// Severity here is the rectangular Tag, NOT the coloured left-border the
// Officer list and the trace table use. These rows are config entries, not
// cases: nothing on this page is a thing that happened to a shop, so a row of
// alarm-coloured edges would be spending signal on a settings screen. See
// docs/design/REDESIGN-SPEC.md, "Per-page application → Rulebook".

// Column template shared by the header and every row, so the two cannot drift.
// The two numeric columns — threshold and weight — are right-aligned: a column
// of figures is read by its last digit, so the last digits have to line up.
const GRID = 'grid grid-cols-[1fr_240px_120px_96px_80px] items-baseline gap-4'

function threshold(rule) {
  // The unit rides with the number the way the trace prints it: -5.0% closed
  // up, 48 hrs spaced.
  if (!rule.unit) return `${rule.threshold}`
  return rule.unit === '%' ? `${rule.threshold}${rule.unit}` : `${rule.threshold} ${rule.unit}`
}

export default function Rulebook() {
  const { data: book, error, loading } = useApi('/api/rulebook')

  const ruleTotal = book ? book.rules.reduce((total, rule) => total + rule.weight, 0) : 0

  return (
    // `isolate` keeps the motif's negative z-index inside this page, where it
    // paints under every card rather than sinking behind the document ground.
    <article className="relative isolate flex-1">
      <PageMotif variant="rulebook" />

      <PageHeader
        title="Rulebook"
        note="The thresholds this district scores against. Held in rules.yaml, read at request time — editing the file changes the next score, with no code change."
      />

      <div className="space-y-8 px-8 py-8">
        {error ? (
          <ErrorState error={error}>
            Start the backend with <code>uvicorn app.main:app --reload --port 8000</code>.
          </ErrorState>
        ) : null}

        {loading ? (
          <LoadingRegion label="Loading the rulebook">
            <SkeletonRows rows={6} />
          </LoadingRegion>
        ) : null}

        {book ? (
          <>
            {/* Provenance of the file itself. The values are ink, not navy:
                they are data about the rulebook, not headings. */}
            <section className={`${CARD} p-6`}>
              <div className="flex flex-wrap gap-8">
                <div>
                  <p className={COLUMN_HEAD}>Version</p>
                  <p className="num font-display text-section-heading text-ink">{book.version}</p>
                </div>
                <div>
                  <p className={COLUMN_HEAD}>Maintained by</p>
                  <p className="font-display text-section-heading text-ink">{book.updated_by}</p>
                </div>
                <div>
                  <p className={COLUMN_HEAD}>Severity bands</p>
                  {/* The bands are the one place on this page where a colour
                      legend earns its keep: it tells the reader what the tags
                      further down mean in points. Each band carries its label
                      inside the tag, so the colour is never the only signal. */}
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <SeverityTag severity="high" />
                    <span className={`num ${CELL}`}>≥ {book.severity_bands.high}</span>
                    <span className="text-ink-muted" aria-hidden="true">
                      ·
                    </span>
                    <SeverityTag severity="medium" />
                    <span className={`num ${CELL}`}>≥ {book.severity_bands.medium}</span>
                    <span className="text-ink-muted" aria-hidden="true">
                      ·
                    </span>
                    <SeverityTag severity="low" />
                    <span className={CELL}>below that</span>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <SectionHeading title="Scoring rules">
                Rulebook v<span className="num">{book.version}</span> ·{' '}
                <span className="num">{book.rules.length}</span> rules ·{' '}
                <span className="num">{ruleTotal}</span> points possible before the corroboration
                bonus. Each rule reads one field, compares it to one threshold, and adds its weight
                if the comparison holds.
              </SectionHeading>

              {/* Plated for the same reason as the heading: these labels sit on
                  bare ground, and the ledger motif behind them would read as a
                  rule struck through the top of the table. */}
              <div className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}>
                <span className={COLUMN_HEAD}>Rule</span>
                <span className={COLUMN_HEAD}>Field read</span>
                <span className={`${COLUMN_HEAD} text-right`}>Fires when</span>
                <span className={COLUMN_HEAD}>Severity</span>
                <span className={`${COLUMN_HEAD} text-right`}>Weight</span>
              </div>

              <ul>
                {book.rules.map((rule) => (
                  <li key={rule.id} className={`${GRID} ${CARD} ${ROW} mt-2`}>
                    <span>
                      <span className="block text-body font-medium text-ink">{rule.label}</span>
                      <span className={`block ${CELL_MUTED}`}>{rule.id}</span>
                    </span>

                    <span className={`num ${CELL_MUTED}`}>{rule.field}</span>

                    <span className="num text-right text-table-cell text-ink">
                      {OPERATOR_SYMBOL[rule.operator] ?? rule.operator} {threshold(rule)}
                    </span>

                    <span>
                      <SeverityTag severity={rule.severity} />
                    </span>

                    <span className="num text-right font-display text-section-heading text-ink">
                      {rule.weight}
                    </span>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <SectionHeading title="Corroboration">
                The one entry that is not a rule.{' '}
                <span className="num">{book.corroboration.complaint_bonus.weight}</span> points,
                available once. Public complaints are not evidence of diversion on their own: they
                add a bounded bonus to a case the ladder already built — they never create one.
              </SectionHeading>

              <div className={`${GRID} ${CARD} ${ROW} mt-4`}>
                <span>
                  <span className="block text-body font-medium text-ink">
                    Complaints corroborate the case
                  </span>
                  <span className={`block ${CELL_MUTED}`}>complaint_bonus</span>
                </span>

                <span className={`num ${CELL_MUTED}`}>complaints in window</span>

                <span className="num text-right text-table-cell text-ink">
                  ≥ {book.corroboration.complaint_bonus.min_complaints} in{' '}
                  {book.corroboration.complaint_bonus.window_days} days
                </span>

                {/* Neutral, not gold. "Bonus" classifies this row against the
                    rules above it; it does not rank it, and a severity colour
                    here would read as an alarm level it does not have. */}
                <span>
                  <Tag tone="neutral">Bonus</Tag>
                </span>

                <span className="num text-right font-display text-section-heading text-ink">
                  +{book.corroboration.complaint_bonus.weight}
                </span>
              </div>
            </section>

            {/* Invariant 3 said out loud on the screen it applies to. A judge
                who adds the column up gets 120 and should not have to wonder
                why a case can score 100. */}
            <section className={`${CARD} p-6`}>
              <p className="text-body text-ink">
                <span className="num">{book.rules.length}</span> rules totalling{' '}
                <span className="num">{ruleTotal}</span> points, plus a{' '}
                <span className="num">{book.corroboration.complaint_bonus.weight}</span>-point
                corroboration bonus — <span className="num">130</span> arithmetically possible.
              </p>
              <p className="mt-1 text-body-secondary text-ink-secondary">
                The displayed score is capped at 100. The weights are not renormalised to hide the
                cap: a case that reached 130 and a case that reached 101 are both shown as 100, and
                the raw total is kept on the case record.
              </p>
              <p className="mt-4 border-t border-border pt-4 text-body-secondary text-ink-secondary">
                Weights are back-solved for the demo case, not learned from outcomes. Declared as a
                scoping decision.
              </p>
            </section>
          </>
        ) : null}

        {!loading && !error && !book ? (
          <EmptyState title="The rulebook came back empty">
            /api/rulebook answered, but rules.yaml parsed to nothing.
          </EmptyState>
        ) : null}
      </div>
    </article>
  )
}
