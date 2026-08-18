// Shared control and surface classes.
//
// One radius token and one shadow depth, per CLAUDE.md's UI conventions: every
// surface in the app is `rounded` (4px) and `shadow-card`, and there is no
// second option to reach for. Keeping the strings here rather than in each
// page is what stops a fifth button from inventing a sixth style.
//
// Colour discipline (docs/design/REDESIGN-SPEC.md): nothing in this file sets
// navy except the primary tier, whose whole job is to be the one navy control
// on a screen. Everything else carries ink text on surface, bordered with the
// warm `border` tokens. Navy stays reserved for headings, the score-display
// number, and that single primary action.
//
// Focus rings are NOT here — they live in index.css as a global
// :focus-visible rule so that native controls (select, textarea) get one
// without every page having to remember.

export const CARD = 'rounded border border-border bg-surface shadow-card'

// The one motion setting in the app. 150ms ease-out is fast enough that a
// control feels answered rather than animated — long enough to read as a
// response, short enough that a demo clicking quickly never waits on it.
// `transition` (not transition-all) covers colour, background, border, shadow
// and transform, which is exactly the set the states below move.
//
// Exported because CARD_OPTION inverts on hover: the card changes ground and
// its contents change colour with it, and a child that does not carry the same
// timing would snap while the card around it eases.
export const MOTION = 'transition duration-150 ease-out'

// The lift. One pixel of translate plus the app's ONE shadow token appearing
// from nothing — that is how a control gains elevation here without a second
// shadow depth existing to reach for. `disabled:hover:` unwinds it, so a
// disabled button stays flat under the cursor; those stacked variants carry
// two pseudo-classes and therefore outrank the plain hover rules.
const LIFT =
  'hover:-translate-y-px hover:shadow-card active:translate-y-0 active:shadow-none ' +
  'disabled:hover:translate-y-0 disabled:hover:shadow-none'

// ---------------------------------------------------------------------------
// Buttons, in three tiers. Every clickable thing in the app is one of these.
// ---------------------------------------------------------------------------

// TIER 1 — primary. Solid navy, white text. At most one per screen: the action
// the screen exists for. Recompute on Auditor, Record note on Inspector, and
// the role choices on the sign-in screen, which are the only thing that page
// does. Hover darkens the fill and lifts; active drops it back down.
export const BUTTON_PRIMARY =
  'inline-block rounded border border-navy bg-navy px-4 py-2 text-body-secondary font-medium text-white ' +
  `${MOTION} ${LIFT} ` +
  'hover:border-navy/90 hover:bg-navy/90 active:bg-navy ' +
  'disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-navy'

// TIER 2 — secondary. Outlined, ink text, surface fill. The ordinary controls:
// Open case, Field note, back links, and anything else a screen offers
// alongside its primary action. Hover fills faintly with surface-sunk and
// lifts, so the tier is distinguished by weight rather than by another colour.
export const BUTTON =
  'inline-block rounded border border-border-strong bg-surface px-4 py-2 text-body-secondary font-medium text-ink ' +
  `${MOTION} ${LIFT} ` +
  'hover:border-ink-secondary hover:bg-surface-sunk active:bg-surface-sunk ' +
  'disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-border-strong ' +
  'disabled:hover:bg-surface'

// TIER 3 — tertiary. Text only: no border, no fill, ink-secondary, underlined
// on hover. For minor actions that must not compete with the two tiers above.
// The sortable column heads are the only ones in the build, and they are
// styled through SORT_HEAD below because a table header keeps its own type
// size whatever else it is.
const TERTIARY = `${MOTION} underline-offset-2 hover:underline`

// A sortable column head: the tertiary tier at table-header size. The colour
// is left to the caller rather than baked in, because the active state has to
// swap it — and `text-ink` and `text-ink-secondary` on one element are two
// utilities of equal specificity, resolved by stylesheet order rather than by
// the order they are written in. `text-ink` is emitted first, so the muted one
// wins and an active header silently stays muted. Exactly one colour class
// reaches this element, so that cannot happen.
export const SORT_HEAD = `text-table-header uppercase ${TERTIARY}`

// ---------------------------------------------------------------------------

// A card that goes somewhere. Same lift vocabulary as the buttons, and
// deliberately NOT applied to informational panels: a hover response on a card
// that cannot be clicked promises a click that never happens.
//
// No border-colour change here on purpose — the Officer and Inspector rows
// carry their severity as a coloured left-border, and a hover rule setting all
// four border colours would wipe it out under the cursor.
export const CARD_INTERACTIVE =
  `${CARD} ${MOTION} hover:-translate-y-px hover:bg-surface-sunk ` +
  'active:translate-y-0 active:bg-surface-sunk'

// A selection card: one of a small set of choices, each carrying a label and a
// line of description, where the whole surface is the target.
//
// AT REST IT IS NOT NAVY, and that is the point. The primary tier's solid navy
// was written for an inline button that IS the action — one per screen, so the
// fill reads as emphasis. Three of them stacked full-width stop reading as
// three things to choose between and start reading as a filled table, because
// nothing distinguishes one row from the next. So the card rests as a bordered
// surface, the way a set of options should, and the navy arrives on
// interaction — hover and keyboard focus both invert it. The weight lands
// where the reader is actually pointing rather than on all three at once.
//
// `group` is part of the token: the contents invert with the card, and they
// key off this class.
export const CARD_OPTION =
  `group rounded border border-border-strong bg-surface shadow-card ${MOTION} ` +
  'hover:-translate-y-px hover:border-navy hover:bg-navy ' +
  'focus-visible:border-navy focus-visible:bg-navy ' +
  'active:translate-y-0 active:bg-navy'

export const FIELD =
  'rounded border border-border-strong bg-surface px-4 py-2 text-body-secondary text-ink ' +
  // Filters sit in the secondary tier, but a select that lifted off the page
  // when the cursor crossed it would be motion for its own sake. It gets the
  // border response and nothing else.
  `${MOTION} hover:border-ink-secondary`

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
