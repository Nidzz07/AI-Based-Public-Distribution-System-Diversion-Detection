import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import { LoadingRegion, SkeletonRows } from '../components/Skeleton.jsx'
import { useApi } from '../hooks/useApi.js'
import { HOP_LABEL, SEVERITY_BORDER } from '../severity.js'
import {
  CAPTION,
  CARD_INTERACTIVE,
  CELL,
  CELL_MUTED,
  COLUMN_HEAD,
  FIELD,
  LABEL,
  ROW,
  SORT_HEAD,
} from '../ui.js'

// Column template shared by the header and every row, so the two cannot drift.
// Track widths are multiples of 8. The two numeric columns are the narrow ones
// on the right, and both are right-aligned — a column of figures is read by
// its last digit, so the last digits have to line up.
const GRID = 'grid grid-cols-[1fr_176px_120px_112px_96px] items-center gap-4'

// `score` is null on purpose: the API already returns cases in triage order,
// and its tie-break reads complaint_count, which this row does not carry.
// Re-sorting here by score alone would silently drop that tie-break and
// reorder equal scores at random. The backend ranks; the client only reorders
// when the officer asks for a different axis.
const SORTS = {
  score: null,
  shop: (a, b) => a.shop.name.localeCompare(b.shop.name),
  coverage: (a, b) => a.coverage_pct - b.coverage_pct || b.score - a.score,
}

function SortHeader({ label, field, sort, onSort, align = 'left' }) {
  const active = sort === field
  return (
    <button
      type="button"
      onClick={() => onSort(field)}
      aria-pressed={active}
      // SORT_HEAD carries the table-header type and the tertiary tier's hover
      // underline, but deliberately no colour: exactly one colour class may
      // reach this element. `text-ink` and `text-ink-secondary` have equal
      // specificity, and Tailwind emits text-ink first, so a header carrying
      // both would silently render muted however it was written — which is
      // what the active state used to do.
      className={`${SORT_HEAD} ${align === 'right' ? 'text-right' : 'text-left'} ${
        active ? 'text-ink' : 'text-ink-secondary hover:text-ink'
      }`}
    >
      {label}
      {/* One mark, always in the same slot, so the header does not reflow when
          the sort changes. */}
      <span className="ml-1" aria-hidden="true">
        {active ? '▾' : ''}
      </span>
    </button>
  )
}

export default function Officer() {
  const { data: cases, error, loading } = useApi('/api/cases')
  const [district, setDistrict] = useState('All districts')
  const [severity, setSeverity] = useState('All severities')
  const [sort, setSort] = useState('score')

  // Districts come from the data rather than a hardcoded list: the filter can
  // only ever offer districts that actually have cases behind them.
  const districts = useMemo(
    () => (cases ? [...new Set(cases.map((c) => c.shop.block))].sort() : []),
    [cases],
  )

  const visible = useMemo(() => {
    if (!cases) return []
    const filtered = cases
      .filter((c) => district === 'All districts' || c.shop.block === district)
      .filter((c) => severity === 'All severities' || c.severity === severity)
    return SORTS[sort] ? filtered.slice().sort(SORTS[sort]) : filtered
  }, [cases, district, severity, sort])

  return (
    // `isolate` is what keeps the motif's negative z-index inside this page.
    // Without it the layer would sink behind the document background and stop
    // being visible at all; with it, it paints under every card on the page.
    <article className="relative isolate flex-1">
      <PageMotif variant="officer" />

      <PageHeader
        title="Officer"
        note="Every open case, ranked by score. The list is the triage order — the top of it is where an inspector goes first."
      />

      <div className="px-8 py-8">
        {/* Plated: the filter labels are text on bare ground, so the motif
            would otherwise run behind them. */}
        <div className="mb-6 flex flex-wrap items-end gap-4 bg-bg">
          <Filter
            label="District"
            value={district}
            onChange={setDistrict}
            options={['All districts', ...districts]}
          />
          <Filter
            label="Severity"
            value={severity}
            onChange={setSeverity}
            options={['All severities', 'HIGH', 'MEDIUM', 'LOW']}
          />
        </div>

        {error ? (
          <ErrorState error={error}>
            Start the backend with <code>uvicorn app.main:app --reload --port 8000</code>.
          </ErrorState>
        ) : null}

        {loading ? (
          <LoadingRegion label="Loading the ranked case list">
            <SkeletonRows rows={6} />
          </LoadingRegion>
        ) : null}

        {cases ? (
          <>
            {/* The table's caption. States in plain language what the reader is
                looking at and how many rows of it there are. */}
            <p className={`${CAPTION} mt-0 bg-bg`}>
              <span className="num">{visible.length}</span> of{' '}
              <span className="num">{cases.length}</span> shops, ranked by evidence. Severity is
              the coloured edge on each row.
            </p>

            {/* Plated for the same reason as the caption above it: column
                labels on bare ground, and a ruled motif behind them reads as a
                line struck through the top of the table. */}
            <div className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}>
              <SortHeader label="Shop" field="shop" sort={sort} onSort={setSort} />
              <span className={COLUMN_HEAD}>Gap located at</span>
              <SortHeader
                label="Coverage"
                field="coverage"
                sort={sort}
                onSort={setSort}
                align="right"
              />
              <SortHeader label="Score" field="score" sort={sort} onSort={setSort} align="right" />
              <span className={COLUMN_HEAD}>Severity</span>
            </div>

            <ul>
              {visible.map((item) => (
                <li key={item.case_id}>
                  <Link
                    to={`/cases/${item.case_id}`}
                    // The left-border IS the severity value. Every row carries
                    // one, so the eye reads the column of colour down the page
                    // before it reads a single number. Because the border
                    // already carries the colour, the Severity cell below is
                    // plain ink — encoding the same fact twice would spend the
                    // signal without adding anything.
                    // CARD_INTERACTIVE rather than CARD: this row goes
                    // somewhere, so it lifts under the cursor. It changes no
                    // border colour on hover, which is what keeps the severity
                    // edge from being wiped out by the hover state.
                    className={`${GRID} ${CARD_INTERACTIVE} ${ROW} mt-2 border-l-4 ${
                      SEVERITY_BORDER[item.severity]
                    }`}
                  >
                    <span>
                      <span className="block text-body font-medium text-ink">
                        {item.shop.name}
                      </span>
                      <span className={`block ${CELL_MUTED}`}>
                        Shop #<span className="num">{item.shop.id}</span> · {item.shop.block} ·{' '}
                        {item.case_id}
                      </span>
                    </span>

                    <span className={CELL_MUTED}>
                      {HOP_LABEL[item.gap_hop] ?? 'Not localised'}
                    </span>

                    <span className="num text-right text-table-cell text-ink">
                      {item.coverage_pct}%
                      {item.coverage_pct < 100 ? (
                        <span className="block text-meta-label text-ink-muted">
                          partial signal
                        </span>
                      ) : null}
                    </span>

                    {/* Ink, not navy. Navy is reserved for headings and the
                        48px score-display on Case Detail, with no exceptions —
                        a list of sixty scores is table data, however much it
                        is the point of the row. Weight, serif and alignment
                        carry the emphasis instead of colour. */}
                    <span className="num text-right font-display text-section-heading text-ink">
                      {item.score}
                    </span>

                    <span className={CELL}>{item.severity}</span>
                  </Link>
                </li>
              ))}
            </ul>

            {visible.length === 0 ? (
              <div className="mt-2">
                <EmptyState title="No case matches this filter">
                  {district !== 'All districts' && severity !== 'All severities'
                    ? `No ${severity} case in ${district}. Widen either filter to see the rest.`
                    : 'Widen the filter to see the rest of the ranked list.'}
                </EmptyState>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </article>
  )
}

function Filter({ label, value, onChange, options }) {
  return (
    <label className="block">
      <span className={LABEL}>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className={FIELD}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}
