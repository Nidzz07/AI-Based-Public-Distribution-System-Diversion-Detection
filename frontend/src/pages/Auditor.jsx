import { useState } from 'react'

import { apiFetch } from '../api.js'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonRows } from '../components/Skeleton.jsx'
import Tag from '../components/Tag.jsx'
import { useApi } from '../hooks/useApi.js'
import { BUTTON_PRIMARY, CARD, CELL, COLUMN_HEAD, FIELD, LABEL, ROW } from '../ui.js'

// F6 on screen: the append-only trail, and the claim that the score can be
// re-derived from stored inputs at any later date.
//
// COLOUR BUDGET FOR THIS PAGE. The recompute outcome is the one signal here,
// and green/coral are spent on it and on nothing else — see REDESIGN-SPEC.md,
// "Per-page application → Auditor". That is why the event-type tags below are
// neutral even where the event sounds like good news (SCORE_RECOMPUTED) or bad
// (RULE_FIRED): an event type classifies, it does not rank, and colouring it
// would put a second green/red conversation on the page competing with the
// only one that matters.

const DEFAULT_CASE = 'C-0041'

// Column template shared by the header and every row, so the two cannot drift.
const GRID = 'grid grid-cols-[176px_112px_160px_1fr] items-baseline gap-4'

// The stored-vs-recomputed comparison grid inside the result band.
const GRID_COMPARE = 'grid grid-cols-[160px_1fr_1fr] items-baseline gap-2'

// Timestamp and actor are meta-label style: this is the scaffolding of the
// narrative, not the narrative. The timestamp is NOT uppercased — "17 Aug
// 2026" stays readable as a date, where "17 AUG 2026" starts shouting a value
// nobody is scanning for.
const META = 'text-meta-label text-ink-secondary'

const STAMP = new Intl.DateTimeFormat('en-IN', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

// Each event type says its own sentence. A raw JSON payload on screen is a
// developer reading their own log; this page is read by someone checking work.
function describe(row) {
  const p = row.payload ?? {}
  switch (row.event_type) {
    case 'CASE_OPENED':
      return `Shop #${p.shop_id}, cycle ${p.period}. Scored ${p.score} (${p.severity}), coverage ${p.coverage_pct}%, gap at ${p.gap_hop ?? 'none located'}.`
    case 'RULE_FIRED':
      return `${p.rule_id}: read ${p.raw_value} against ${p.threshold}. Added ${p.contribution}.`
    case 'COMPLAINT_LINKED':
      return `${p.count} complaint${p.count === 1 ? '' : 's'} inside the ${p.window_days}-day window. Bonus ${p.contribution ? `+${p.contribution}` : 'not applied'}.`
    case 'NOTE_ADDED':
      return p.text ?? ''
    case 'SCORE_RECOMPUTED':
      return p.identical
        ? `Re-derived from stored inputs: ${p.recomputed?.score}. Identical to the stored score.`
        : `Re-derived from stored inputs: ${p.recomputed?.score}, against a stored ${p.stored?.score}. Divergence.`
    default:
      return JSON.stringify(p)
  }
}

export default function Auditor() {
  const [caseId, setCaseId] = useState(DEFAULT_CASE)
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [failure, setFailure] = useState(null)

  const { data: cases } = useApi('/api/cases')
  const { data: trail, error, loading, reload } = useApi(caseId ? `/api/audit/${caseId}` : null)

  async function recompute() {
    setRunning(true)
    setFailure(null)
    try {
      const outcome = await apiFetch(`/api/cases/${caseId}/recompute`, { method: 'POST' })
      setResult(outcome)
      // The SCORE_RECOMPUTED row the POST just wrote should appear below
      // without a page reload — that is the point being demonstrated.
      reload()
    } catch (err) {
      setFailure(err.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    // `isolate` keeps the motif's negative z-index inside this page, where it
    // paints under every card rather than sinking behind the document ground.
    <article className="relative isolate flex-1">
      <PageMotif variant="auditor" />

      <PageHeader
        title="Auditor"
        note="Every event ever written against a case, oldest first. Nothing here can be edited or removed — a recompute adds a row, it never rewrites one."
      />

      <div className="space-y-8 px-8 py-8">
        {/* Plated: the Case label is text on bare ground, so the motif would
            otherwise run behind it. */}
        <div className="flex flex-wrap items-end gap-4 bg-bg">
          <label className="block">
            <span className={LABEL}>Case</span>
            <select
              value={caseId}
              onChange={(event) => {
                setCaseId(event.target.value)
                setResult(null)
                setFailure(null)
              }}
              className={FIELD}
            >
              {(
                cases ?? [{ case_id: DEFAULT_CASE, shop: { id: '4521', name: 'FPS Sitapur-12' } }]
              ).map((item) => (
                <option key={item.case_id} value={item.case_id}>
                  {item.case_id} — {item.shop.name}
                </option>
              ))}
            </select>
          </label>

          <button type="button" onClick={recompute} disabled={running} className={BUTTON_PRIMARY}>
            {running ? 'Re-deriving…' : 'Recompute from stored inputs'}
          </button>
        </div>

        {failure ? <ErrorState error={failure} /> : null}

        {result ? <RecomputeResult result={result} /> : null}

        <section>
          <SectionHeading
            title={
              <>
                Event trail — <span className="num">{caseId}</span>
              </>
            }
          >
            {trail && trail.length > 0 ? (
              <>
                <span className="num">{trail.length}</span> events on this case, oldest first — the
                order the server stored them in, not a client sort. Append-only: there is no code
                path anywhere in this build that can edit or remove one.
              </>
            ) : null}
          </SectionHeading>

          {error ? (
            <div className="mt-4">
              <ErrorState error={error}>
                Start the backend with <code>uvicorn app.main:app --reload --port 8000</code>.
              </ErrorState>
            </div>
          ) : null}

          {loading ? (
            <div className="mt-4">
              <LoadingRegion label="Loading the audit trail">
                <SkeletonRows rows={5} />
              </LoadingRegion>
            </div>
          ) : null}

          {trail && trail.length === 0 ? (
            <div className="mt-4">
              <EmptyState title="Nothing has happened to this case yet">
                The case exists but carries no events. That is a real answer, not a missing one —
                events appear here as the case is opened, scored, noted and re-derived.
              </EmptyState>
            </div>
          ) : null}

          {trail && trail.length > 0 ? (
            <>
              {/* Plated for the same reason as the section heading: column
                  labels on bare ground, and the timeline motif behind them
                  reads as a rule struck through the top of the table. */}
              <div className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}>
                <span className={COLUMN_HEAD}>When</span>
                <span className={COLUMN_HEAD}>Actor</span>
                <span className={COLUMN_HEAD}>Event</span>
                <span className={COLUMN_HEAD}>Detail</span>
              </div>

              <ol>
                {trail.map((row) => (
                  <li key={row.id} className={`${CARD} ${ROW} ${GRID} mt-2`}>
                    <time className={`num ${META}`}>{STAMP.format(new Date(row.created_at))}</time>

                    <span className={`${META} uppercase`}>{row.actor_role}</span>

                    {/* Neutral tone, always — see the colour budget note at the
                        top of this file. */}
                    <span>
                      <Tag tone="neutral">{row.event_type}</Tag>
                    </span>

                    <span className={CELL}>{describe(row)}</span>
                  </li>
                ))}
              </ol>
            </>
          ) : null}
        </section>
      </div>
    </article>
  )
}

// The contrast that has to survive being seen for two seconds from the back of
// a room: a full-width band in green or coral, the two numbers side by side,
// and a word. Colour is doing the fast work and the word is doing the reliable
// work — neither is alone.
//
// This is the ONLY place on the page that spends green or coral.
function RecomputeResult({ result }) {
  const same = result.identical

  return (
    <section
      className={`${CARD} border-l-4 ${same ? 'border-l-green' : 'border-l-coral'} p-6`}
      aria-live="polite"
    >
      <div className="flex flex-wrap items-center gap-8">
        {/* Ink, not navy, and not the 48px score-display either: that exact
            combination belongs to the 87 on Case Detail and nothing else in
            the app competes with it. 28px serif is large enough to read across
            a room once the coloured band beside it has already done the
            pointing. */}
        <div>
          <p className={COLUMN_HEAD}>Stored on the day</p>
          <p className="num font-display text-page-title text-ink">{result.stored.score}</p>
        </div>

        <span className="font-display text-page-title text-ink-muted" aria-hidden="true">
          →
        </span>

        <div>
          <p className={COLUMN_HEAD}>Re-derived just now</p>
          <p className="num font-display text-page-title text-ink">{result.recomputed.score}</p>
        </div>

        {/* Sentence case, not ALL CAPS. The band, the colour and 28px serif
            already make this unmissable; shouting the word as well is the
            badge-soup reflex the redesign is correcting. */}
        <div
          className={`ml-auto rounded px-6 py-4 ${same ? 'bg-green' : 'bg-coral'} text-white`}
        >
          <p className="font-display text-page-title">
            {/* U+2713, a typographic check mark, not an emoji. */}
            {same ? 'Identical ✓' : 'Mismatch'}
          </p>
        </div>
      </div>

      <p className="mt-4 border-t border-border pt-4 text-body text-ink">
        {same
          ? 'The same stored inputs and the same rulebook produced the same score. Severity, coverage and the located gap all match.'
          : 'The re-derivation disagrees with what was stored. The stored case has NOT been overwritten — the disagreement is the finding, and it has been written to the trail below.'}
      </p>

      <dl className={`${GRID_COMPARE} mt-4`}>
        <dt className={COLUMN_HEAD} />
        <dd className={COLUMN_HEAD}>Stored</dd>
        <dd className={COLUMN_HEAD}>Recomputed</dd>
        {['severity', 'coverage_pct', 'gap_hop', 'rulebook_version'].map((field) => (
          <CompareRow key={field} field={field} result={result} />
        ))}
      </dl>
    </section>
  )
}

// Field names are left exactly as the contract spells them. An auditor
// re-deriving this months later is matching them against case_detail.json, and
// a prettier label would be one more thing to translate back.
function CompareRow({ field, result }) {
  const stored = String(result.stored[field])
  const fresh = String(result.recomputed[field])
  const differs = stored !== fresh

  return (
    <>
      <dt className="text-body-secondary text-ink-secondary">{field}</dt>
      <dd className={`num ${CELL}`}>{stored}</dd>
      {/* Coral here is the same signal as the band above — a field that moved
          is part of the mismatch finding, not a separate alarm. */}
      <dd className={`num ${differs ? 'text-table-cell font-medium text-coral' : CELL}`}>
        {fresh}
      </dd>
    </>
  )
}
