import { Link, useParams } from 'react-router-dom'

import EmptyState, { ErrorState } from '../components/EmptyState.jsx'
import Ladder from '../components/Ladder.jsx'
import PageHeader from '../components/PageHeader.jsx'
import PageMotif from '../components/PageMotif.jsx'
import SectionHeading from '../components/SectionHeading.jsx'
import { LoadingRegion, SkeletonPanel, SkeletonRows } from '../components/Skeleton.jsx'
import Tag, { StatusTag } from '../components/Tag.jsx'
import TraceTable from '../components/TraceTable.jsx'
import { useApi } from '../hooks/useApi.js'
import { HOP_LABEL, SEVERITY_BORDER } from '../severity.js'
import { BUTTON, CARD, COLUMN_HEAD } from '../ui.js'

const DATE = new Intl.DateTimeFormat('en-IN', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

// This page has four exits — error, loading, empty and the real thing — and
// all four are the same sheet with the same texture behind them. Wrapping them
// once is what stops a later edit adding the motif to three of the four.
//
// `isolate` is what keeps the motif's negative z-index inside this page:
// without it the layer sinks behind the document background and disappears;
// with it, it paints under every card here.
function Page({ children }) {
  return (
    <article className="relative isolate flex-1">
      <PageMotif variant="case" />
      {children}
    </article>
  )
}

export default function CaseDetail() {
  const { caseId } = useParams()
  const { data: detail, error, loading } = useApi(`/api/cases/${caseId}`)

  if (error) {
    return (
      <Page>
        <PageHeader title="Case Detail" note={`Case ${caseId}`} />
        <div className="px-8 py-8">
          <ErrorState error={error}>
            {error.includes('404')
              ? `There is no case ${caseId}. It may have been opened under a different id.`
              : 'Start the backend with uvicorn app.main:app --reload --port 8000.'}
          </ErrorState>
        </div>
      </Page>
    )
  }

  if (loading) {
    return (
      <Page>
        <PageHeader title="Case Detail" note={`Case ${caseId}`} />
        <div className="space-y-8 px-8 py-8">
          <LoadingRegion label={`Loading case ${caseId}`}>
            <SkeletonPanel lines={2} />
            <div className="mt-8">
              <SkeletonRows rows={4} />
            </div>
          </LoadingRegion>
        </div>
      </Page>
    )
  }

  if (!detail) {
    return (
      <Page>
        <PageHeader title="Case Detail" note={`Case ${caseId}`} />
        <div className="px-8 py-8">
          <EmptyState title="This case came back empty">
            The API answered for {caseId} but returned no case body.
          </EmptyState>
        </div>
      </Page>
    )
  }

  const { shop, complaint_bonus: bonus } = detail

  return (
    <Page>
      <PageHeader
        title={shop.name}
        note={`Case ${detail.case_id} · Shop #${shop.id} · ${shop.block} · opened ${DATE.format(
          new Date(detail.opened_at),
        )}`}
      />

      <div className="space-y-8 px-8 py-8">
        {/* A back link is a secondary control, not a stray piece of underlined
            prose — it gets the same bordered button every other secondary
            action on the app uses. */}
        <Link to="/" className={BUTTON}>
          ← All cases
        </Link>

        {/* Headline: the score, its band, and — inseparably — how much of the
            rulebook we were actually able to run to get it.

            The severity colour is carried by the card's left-border, so the
            Severity value beside it is plain ink. A coloured border AND a
            coloured word would be the same fact encoded twice, and the two
            severity patterns never mix on one element. */}
        <section className={`${CARD} border-l-4 ${SEVERITY_BORDER[detail.severity]} p-6`}>
          <div className="flex flex-wrap items-end gap-8">
            <div>
              <p className={COLUMN_HEAD}>Score</p>
              {/* THE score-display. The one element in the entire app that gets
                  navy at 48px serif — the number the case is ultimately about.
                  Nothing else on any page competes with it. */}
              <p className="num font-display text-score-display text-navy">
                {detail.score}
                <span className="text-section-heading font-normal text-ink-muted">/100</span>
              </p>
            </div>

            <div>
              <p className={COLUMN_HEAD}>Severity</p>
              <p className="font-display text-section-heading text-ink">{detail.severity}</p>
            </div>

            <div>
              <p className={COLUMN_HEAD}>Gap located at</p>
              <p className="font-display text-section-heading text-ink">
                {HOP_LABEL[detail.gap_hop] ?? 'Not localised'}
              </p>
            </div>

            <CoverageBadge coverage={detail.coverage_pct} score={detail.score} />
          </div>

          {/* The partial-coverage caveat lives on the footer line, not inside
              the coverage block. Inside, its two extra lines made that column
              the tallest thing in an items-end row, which dragged the score
              down the card and left a dead gap above it. */}
          <p className="mt-4 border-t border-border pt-4 text-body-secondary text-ink-secondary">
            Rulebook v{detail.rulebook_version} · status {detail.status.toLowerCase()}
            {detail.coverage_pct < 100
              ? ' · some rules could not be evaluated — they are greyed in the trace and scored nothing'
              : ''}
          </p>
        </section>

        <Ladder cycle={detail.cycle} gapHop={detail.gap_hop} />

        <TraceTable hits={detail.rule_hits} />

        {/* Corroboration is shown as its own block, not folded into the trace:
            it is not a rule, it is the public agreeing with one. */}
        <section>
          <SectionHeading title="Linked complaints">
            Grievances filed against this shop inside the {bonus.window_days}-day window before the
            case opened.{' '}
            {bonus.contribution
              ? `${bonus.count} of them, adding ${bonus.contribution} to the score.`
              : `${bonus.count} filed — below the threshold, so nothing was added to the score.`}
          </SectionHeading>

          {detail.complaints.length === 0 ? (
            <div className="mt-4">
              <EmptyState title="No complaints inside the window">
                Nothing was filed against this shop in the {bonus.window_days} days before the case
                opened. Older complaints, if any, are outside the window and were not counted.
              </EmptyState>
            </div>
          ) : (
            <ul className="mt-4">
              {detail.complaints.map((complaint) => (
                <li key={complaint.id} className={`${CARD} mt-2 px-4 py-4`}>
                  <div className="flex flex-wrap items-center gap-4">
                    <span className="text-table-cell font-medium text-ink">
                      {complaint.category.replace(/_/g, ' ')}
                    </span>
                    <span className="text-body-secondary text-ink-secondary">
                      {complaint.source.replace(/_/g, ' ')}
                    </span>
                    <time className="num text-body-secondary text-ink-secondary">
                      {DATE.format(new Date(complaint.filed_at))}
                    </time>
                    {/* Status as a rectangular tag: colour plus a text label,
                        never colour alone. */}
                    <StatusTag status={complaint.status} className="ml-auto" />
                  </div>
                  <p className="mt-1 text-body text-ink">{complaint.text}</p>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <SectionHeading title="Memo">
            The case in one paragraph, for an officer who will act on it and an auditor who will
            re-derive it months later.
          </SectionHeading>
          <p className={`${CARD} mt-4 p-6 text-body leading-relaxed text-ink`}>{detail.memo}</p>
          {/* Said plainly on the screen an officer reads, not only in the deck:
              this sentence is assembled from the trace above by a template.
              Plated: it is the last thing on the page, so the motif's open
              space begins directly under it. */}
          <p className="mt-2 bg-bg text-body-secondary text-ink-secondary">
            Assembled from the fired rules above by a template. Not generated by a language model.
          </p>
        </section>
      </div>
    </Page>
  )
}

// "87 / 100 · signal coverage 100%". The two numbers travel together on
// purpose: a score means something different when a fifth of the rulebook
// could not be run, and separating them lets a reader forget that.
//
// The figure itself is ink. Partial coverage earns a gold tag — colour spent
// only on the exceptional case, with a word attached so the colour is never
// doing the work alone. Full coverage gets no tag: the absence is the signal,
// and a green "complete" badge on every clean case would be noise.
function CoverageBadge({ coverage, score }) {
  const partial = coverage < 100
  return (
    <div className="ml-auto">
      <p className={COLUMN_HEAD}>Signal coverage</p>
      <p className="num font-display text-section-heading text-ink">
        {coverage}%
        {partial ? (
          <Tag tone="medium" className="ml-2">
            Partial
          </Tag>
        ) : null}
      </p>
      <p className="num mt-1 text-body-secondary text-ink-secondary">
        {score} / 100 · signal coverage {coverage}%
      </p>
    </div>
  )
}
