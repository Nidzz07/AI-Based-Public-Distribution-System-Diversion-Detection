// Severity and trace-state styling, in one place so a row on the Officer list
// and a row in the trace table can never disagree about what coral means.
//
// Tailwind classes are written out in full rather than composed at runtime:
// the JIT scans source text, so a class built as `border-${colour}` would be
// absent from the stylesheet and the row would silently lose its border.
//
// TWO severity patterns exist and they never mix on one element:
//   (1) coloured left-border on a full data row — SEVERITY_BORDER below,
//       used by the Officer list, the Inspector list and the case header
//   (2) the rectangular Tag component — components/Tag.jsx, used for compact
//       inline status (Rulebook severities, complaint status, note outcomes)
// Where a row carries the left-border, its severity TEXT is plain ink: the
// border is already the colour signal, and colouring the word as well would
// be encoding the same fact twice. There is deliberately no severity-to-text-
// colour map here any more — a bare coloured word is never the right answer,
// because colour alone is not a label.

export const SEVERITY_BORDER = {
  HIGH: 'border-l-coral',
  MEDIUM: 'border-l-gold',
  LOW: 'border-l-green',
}

// Rulebook comparisons, written the way an officer reads them rather than the
// way YAML stores them.
export const OPERATOR_SYMBOL = {
  lt: '<',
  lte: '≤',
  gt: '>',
  gte: '≥',
  eq: '=',
}

// What a located gap tells an inspector to go and do. Derived from gap_hop,
// which is the one field on a case that names a place rather than a number.
export const HOP_ACTION = {
  allocation_to_dispatch:
    'Short before it left the depot. Check the dispatch order against the weighbridge slip.',
  dispatch_to_receipt:
    'Lost on the transport leg. Check the consignment note, the vehicle log and the route.',
  receipt_to_counter:
    'Lost at the counter. Check the stock register against the ePoS dispensing record.',
}

// The three trace-row states. A skipped rule is greyed and italic — it must
// never be mistaken for a rule that passed, so it is the one state that
// changes the type style and not just the colour.
export const TRACE_ROW = {
  fired: {
    border: 'border-l-coral',
    row: 'bg-surface text-ink',
    label: 'Fired',
    labelClass: 'text-coral font-medium',
  },
  passed: {
    border: 'border-l-green',
    row: 'bg-surface text-ink',
    label: 'Passed',
    labelClass: 'text-green',
  },
  skipped: {
    border: 'border-l-border-strong',
    row: 'bg-surface-sunk text-ink-muted italic',
    label: 'Skipped',
    labelClass: 'text-ink-muted',
  },
}

const KG = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })

export function formatKg(value) {
  return value === null || value === undefined ? null : KG.format(value)
}

export function formatPct(value) {
  // Two decimals, matching the precision the ladder is reconciled at. Nulls
  // stay null: an unmeasured hop is not a 0.00% hop.
  return value === null || value === undefined ? null : `${value.toFixed(2)}%`
}

export const HOP_LABEL = {
  allocation_to_dispatch: 'Allocation to dispatch',
  dispatch_to_receipt: 'Dispatch to receipt',
  receipt_to_counter: 'Receipt to counter',
}
