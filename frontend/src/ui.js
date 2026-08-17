// Shared control and surface classes.
//
// One radius token and one shadow depth, per CLAUDE.md's UI conventions: every
// surface in the app is `rounded` (4px) and `shadow-card`, and there is no
// second option to reach for. Keeping the strings here rather than in each
// page is what stops a fifth button from inventing a sixth style.
//
// Colour discipline (docs/design/REDESIGN-SPEC.md): nothing in this file sets
// navy. Controls carry ink text on surface, bordered with the warm `border`
// token. Navy is reserved for headings and the score-display number.
//
// Focus rings are NOT here — they live in index.css as a global
// :focus-visible rule so that native controls (select, textarea) get one
// without every page having to remember.

export const CARD = 'rounded border border-border bg-surface shadow-card'

export const BUTTON =
  'rounded border border-border-strong bg-surface px-4 py-2 text-body-secondary font-medium text-ink ' +
  'transition-colors hover:border-ink-secondary disabled:cursor-not-allowed disabled:opacity-50'

// Reserved for the one action on a page that is the point of the page —
// Recompute on the Auditor screen, Record note on the Inspector screen.
export const BUTTON_PRIMARY =
  'rounded border border-navy bg-navy px-4 py-2 text-body-secondary font-medium text-white ' +
  'transition-colors hover:border-navy/80 hover:bg-navy/90 ' +
  'disabled:cursor-not-allowed disabled:opacity-50'

export const FIELD =
  'rounded border border-border-strong bg-surface px-4 py-2 text-body-secondary text-ink'

// The meta-label style: 12px, uppercase, tracked, ink-secondary. Used for
// field labels and for the small caps above a figure.
export const LABEL = 'mb-1 block text-meta-label uppercase text-ink-secondary'

// Table headers share the meta-label style so they read as structure rather
// than as another row of data — smaller, tracked and muted against the cells.
export const COLUMN_HEAD = 'text-table-header uppercase text-ink-secondary'

// Every table and list carries one of these: a plain-language line saying what
// the reader is looking at, sitting under the section heading.
export const CAPTION = 'mt-1 text-body-secondary text-ink-secondary'

// Body copy and the standard table cell. Numeric cells add `num` for
// tabular figures and `text-right` for alignment.
export const BODY = 'text-body text-ink'
export const CELL = 'text-table-cell text-ink'
export const CELL_MUTED = 'text-table-cell text-ink-secondary'
export const CELL_NUM = 'num text-table-cell text-ink text-right'

// Row padding for list/table views: 16px vertical. Dense enough to read as a
// data product, not so dense it reads as a spreadsheet.
export const ROW = 'px-4 py-4'
