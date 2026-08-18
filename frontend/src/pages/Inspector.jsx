import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiFetch } from '../api.js'
import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import { LoadingRegion, SkeletonRows } from '../components/Skeleton.jsx'
import Tag from '../components/Tag.jsx'
import { useApi } from '../hooks/useApi.js'
import { HOP_ACTION, SEVERITY_BORDER } from '../severity.js'
import {
  BUTTON,
  BUTTON_PRIMARY,
  CAPTION,
  CARD,
  CELL,
  CELL_MUTED,
  COLUMN_HEAD,
  FIELD,
  LABEL,
  ROW,
} from '../ui.js'

// The field list. Same data as the Officer screen and the same ranking, read
// for a different purpose: an officer triages, an inspector drives. So each
// row leads with where to go and what to look at when they get there.
//
// Routing is score order, not geography — declared as a scoping decision. The
// page says so rather than implying an optimised route it does not compute.

// Column template shared by the header and every row, so the two cannot drift.
// Score is right-aligned with tabular figures: a column of figures is read by
// its last digit, so the last digits have to line up.
const GRID = 'grid grid-cols-[1fr_96px_96px_144px] items-start gap-4'

const DATE = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
const TIME = new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit' })

export default function Inspector() {
  const { data: cases, error, loading } = useApi('/api/cases')
  const [district, setDistrict] = useState('All districts')
  const [openCase, setOpenCase] = useState(null)

  const districts = useMemo(
    () => (cases ? [...new Set(cases.map((c) => c.shop.block))].sort() : []),
    [cases],
  )

  // No client-side re-sort: the API already ranks, and its tie-break reads a
  // field this row does not carry.
  const visible = useMemo(
    () => (cases ?? []).filter((c) => district === 'All districts' || c.shop.block === district),
    [cases, district],
  )

  return (
    // `isolate` keeps the motif's negative z-index inside this page, where it
    // paints under every card rather than sinking behind the document ground.
    <article className="relative isolate flex-1">
      <PageMotif variant="inspector" />

      <PageHeader
        title="Inspector"
        note="Cases in visit order, highest score first. Add a field note against any of them — it lands in the case's audit trail."
      />

      <div className="px-8 py-8">
        {/* Plated: the District label is text on bare ground, so the motif
            would otherwise run behind it. */}
        <div className="mb-6 flex flex-wrap items-end gap-4 bg-bg">
          <label className="block">
            <span className={LABEL}>District</span>
            <select
              value={district}
              onChange={(event) => setDistrict(event.target.value)}
              className={FIELD}
            >
              {['All districts', ...districts].map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>

        {error ? (
          <ErrorState error={error}>
            Start the backend with <code>uvicorn app.main:app --reload --port 8000</code>.
          </ErrorState>
        ) : null}

        {loading ? (
          <LoadingRegion label="Loading the visit list">
            <SkeletonRows rows={6} />
          </LoadingRegion>
        ) : null}

        {cases ? (
          <>
            {/* The list's caption. Says what the reader is looking at, how many
                rows of it there are, and — out loud, not only in the deck —
                that the order is score, not an optimised route. */}
            <p className={`${CAPTION} mt-0 bg-bg`}>
              <span className="num">{visible.length}</span> of{' '}
              <span className="num">{cases.length}</span> cases, in visit order. Sorted by score,
              not by distance. Severity is the coloured edge on each row.
            </p>

            {visible.length > 0 ? (
              // Plated for the same reason as the caption above it.
              <div className={`${GRID} mt-4 border-b border-border-strong bg-bg px-4 pb-2`}>
                <span className={COLUMN_HEAD}>Shop · what to look at</span>
                <span className={`${COLUMN_HEAD} text-right`}>Score</span>
                <span className={COLUMN_HEAD}>Severity</span>
                <span className={`${COLUMN_HEAD} text-right`}>Actions</span>
              </div>
            ) : null}

            <ul>
              {visible.map((item) => (
                <li
                  key={item.case_id}
                  // The left-border IS the severity value, the same as the
                  // Officer list. Because the border already carries the
                  // colour, the Severity cell below is plain ink — the two
                  // severity patterns never appear on one element, and a
                  // coloured word beside a coloured edge would encode the same
                  // fact twice without adding anything.
                  className={`${CARD} ${ROW} mt-2 border-l-4 ${SEVERITY_BORDER[item.severity]}`}
                >
                  <div className={GRID}>
                    <div>
                      <p className="text-body font-medium text-ink">{item.shop.name}</p>
                      <p className={CELL_MUTED}>
                        Shop #<span className="num">{item.shop.id}</span> · {item.shop.block} ·{' '}
                        {item.case_id}
                      </p>
                      {/* The reason an inspector is on this page rather than
                          the Officer one: not the score, but the instruction
                          the score turns into. Body weight, because it is the
                          thing being read, not a caption on it. */}
                      <p className="mt-2 max-w-xl text-body text-ink">
                        {HOP_ACTION[item.gap_hop] ??
                          'No hop localised — the ladder readings for this cycle are incomplete.'}
                      </p>
                    </div>

                    {/* Ink, not navy. Navy is reserved for headings and the
                        48px score-display on Case Detail. Weight, serif and
                        alignment carry the emphasis instead of colour. */}
                    <p className="num text-right font-display text-section-heading text-ink">
                      {item.score}
                    </p>

                    <p className={CELL}>{item.severity}</p>

                    <div className="flex flex-col items-end gap-2">
                      <Link to={`/cases/${item.case_id}`} className={BUTTON}>
                        Open case
                      </Link>
                      <button
                        type="button"
                        className={BUTTON}
                        aria-expanded={openCase === item.case_id}
                        onClick={() => setOpenCase(openCase === item.case_id ? null : item.case_id)}
                      >
                        {openCase === item.case_id ? 'Close notes' : 'Field note'}
                      </button>
                    </div>
                  </div>

                  {openCase === item.case_id ? <Notes caseId={item.case_id} /> : null}
                </li>
              ))}
            </ul>

            {visible.length === 0 ? (
              <div className="mt-4">
                <EmptyState title={`No cases in ${district}`}>
                  Every case in this district has been closed, or no shop there has been scored for
                  cycle 2026-08. Choose another district to keep working.
                </EmptyState>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </article>
  )
}

// Notes are read back from the audit trail rather than kept in local state.
// The point of the feature is that a note becomes part of the case's permanent
// record, so the page shows what the server actually stored — an optimistic
// list would look identical whether the POST landed or not.
function Notes({ caseId }) {
  const { data: trail, loading, reload } = useApi(`/api/audit/${caseId}`)
  const [text, setText] = useState('')
  const [status, setStatus] = useState(null)
  const [saving, setSaving] = useState(false)

  const notes = (trail ?? []).filter((row) => row.event_type === 'NOTE_ADDED')

  async function submit(event) {
    event.preventDefault()
    const body = text.trim()
    if (!body || saving) return

    setSaving(true)
    setStatus(null)
    try {
      const saved = await apiFetch(`/api/cases/${caseId}/notes`, {
        method: 'POST',
        body: JSON.stringify({ text: body, actor_role: 'inspector' }),
      })
      setText('')
      setStatus({ ok: true, detail: `Event #${saved.id} in this case's audit trail.` })
      reload()
    } catch (err) {
      setStatus({ ok: false, detail: err.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mt-4 border-t border-border pt-4">
      <form onSubmit={submit}>
        <label className="block">
          <span className={LABEL}>Field note</span>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={3}
            placeholder="What you saw, and what you checked it against."
            className={`${FIELD} w-full resize-y`}
          />
        </label>

        <div className="mt-2 flex flex-wrap items-center gap-4">
          <button type="submit" className={BUTTON_PRIMARY} disabled={!text.trim() || saving}>
            {saving ? 'Recording…' : 'Record note'}
          </button>

          {/* The outcome as a tag plus a sentence, not a coloured sentence:
              green-vs-coral text alone leaves a colour-blind reader with two
              identical-looking messages. aria-live so it is announced as well
              as shown. */}
          <p aria-live="polite" className="flex items-center gap-2">
            {status ? (
              <>
                <Tag tone={status.ok ? 'closed' : 'high'}>
                  {status.ok ? 'Recorded' : 'Not recorded'}
                </Tag>
                <span className="text-body-secondary text-ink-secondary">{status.detail}</span>
              </>
            ) : null}
          </p>
        </div>
      </form>

      <div className="mt-4">
        {/* Every note in this list is a NOTE_ADDED event by construction, and a
            note has no open/closed state to show — so there is no status here
            for a tag to carry. Adding one would spend the pattern on a label
            that is the same on every row. */}
        <p className={LABEL}>
          Notes on this case (<span className="num">{notes.length}</span>)
        </p>

        {loading ? (
          <p className="text-body-secondary text-ink-secondary">Reading the audit trail…</p>
        ) : notes.length === 0 ? (
          <p className="text-body-secondary text-ink-secondary">
            No notes yet. The first one written here becomes part of this case permanently — the
            trail is append-only, so a note cannot be edited or withdrawn afterwards.
          </p>
        ) : (
          <ul className="space-y-2">
            {notes.map((note) => (
              <li key={note.id} className="rounded border border-border bg-surface-sunk px-4 py-2">
                <p className="text-body text-ink">{note.payload?.text}</p>
                <p className="mt-1 text-body-secondary text-ink-secondary">
                  {note.actor_role} ·{' '}
                  <time className="num">
                    {DATE.format(new Date(note.created_at))} {TIME.format(new Date(note.created_at))}
                  </time>{' '}
                  · event #<span className="num">{note.id}</span>
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
