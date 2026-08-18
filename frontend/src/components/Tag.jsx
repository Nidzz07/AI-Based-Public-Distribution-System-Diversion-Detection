// The tag component, after GOV.UK's.
//
// A small RECTANGLE at the app's single 4px radius — not a pill. Tinted
// background at 15% of the signal colour, solid full-strength colour for the
// text, and ALWAYS a text label inside it. Colour is never the only signal:
// the label is what a colour-blind reader, a greyscale print of the case
// sheet, and a magistrate's photocopy all still have.
//
// Sentence case ("High", not "HIGH") — the tag is a label, not an alarm.
//
// This is the pattern for COMPACT INLINE status: a rule's severity in a config
// table, a complaint's open/closed state, an audit event's type. It is NOT for
// full data rows — those keep the coloured left-border (Officer list, trace
// table), and the two patterns never appear on the same element.

const TONES = {
  high: 'bg-coral/15 text-coral',
  medium: 'bg-gold/15 text-gold',
  low: 'bg-green/15 text-green',
  open: 'bg-gold/15 text-gold',
  closed: 'bg-green/15 text-green',
  // For labels that classify without ranking — audit event types, for
  // instance. Reaching for a severity colour there would spend signal on
  // something that carries none.
  neutral: 'bg-surface-sunk text-ink-secondary',
}

// Sentence case, applied here rather than trusted to the caller so a raw
// "HIGH" from the API cannot leak onto the page shouting.
function sentenceCase(text) {
  const words = String(text).replace(/_/g, ' ').toLowerCase()
  return words.charAt(0).toUpperCase() + words.slice(1)
}

export default function Tag({ tone = 'neutral', children, className = '' }) {
  return (
    <span
      // transition-colors so a tag that swaps tone — the Inspector note
      // outcome going from Recorded to Not recorded, say — crossfades rather
      // than snapping. Same 150ms as every other state change in the app.
      className={`inline-block rounded px-2 py-1 text-meta-label transition-colors duration-150 ease-out ${
        TONES[tone] ?? TONES.neutral
      } ${className}`}
    >
      {typeof children === 'string' ? sentenceCase(children) : children}
    </span>
  )
}

// Severity arrives as "HIGH" from a case and "high" from a rule; both map to
// the same tone without the caller having to know which it is holding.
export function SeverityTag({ severity, className = '' }) {
  return (
    <Tag tone={String(severity).toLowerCase()} className={className}>
      {severity}
    </Tag>
  )
}

export function StatusTag({ status, className = '' }) {
  return (
    <Tag tone={String(status).toLowerCase()} className={className}>
      {status}
    </Tag>
  )
}
