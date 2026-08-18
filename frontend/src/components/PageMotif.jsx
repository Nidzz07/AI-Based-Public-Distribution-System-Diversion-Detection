import { LogoMark } from './Logo.jsx'

// Page texture, not page imagery.
//
// The reference is security paper: the faint ruled ground under a land record,
// the watermark in a certificate, the ticked margin of an inspection register.
// Something you only notice when you go looking for it, whose whole job is to
// make the sheet feel like an official sheet rather than a blank one. If a
// motif on this page ever draws the eye, it is wrong, and the fix is to remove
// a line or drop the opacity — never to make it prettier.
//
// CONTRAST DISCIPLINE, enforced here so no page has to remember it:
//
//   1. Opacity is capped in this file, at a value picked by sweeping the
//      candidates against real text rather than by eye. Navy at 10% over the
//      #FAF8F4 ground lands at #E3E3E3. Against that, body ink (#14171A)
//      reads 14.02:1 and ink-secondary (#5B6169) — the lightest type that
//      ever sits on bare ground — reads 4.87:1, clear of the 4.5:1 AA floor
//      with room to spare. AA survives as far as 14% (4.51:1), which is
//      exactly why the cap is not there: a floor reached with no margin is a
//      floor one future tweak breaks. ink-muted (#94989E) would not clear it
//      at any opacity including zero, but ink-muted only ever appears inside
//      a card, and cards are opaque (see 3).
//   2. The layer is masked to fade in over the first 200px, which softens the
//      texture under the page header band but does NOT clear it: the band runs
//      to roughly 112px, where the mask is still better than half open. The
//      fade is a gradient, not a cutoff, so it cannot be what protects text.
//      Occlusion does that — see 3.
//   3. The layer sits at z-index -10 inside the page's own `isolate` stacking
//      context. Negative z paints BEFORE descendant backgrounds, so anything
//      with an opaque background covers the motif completely. That is why
//      every container holding text carries one: bg-surface on cards and rows,
//      bg-bg on the header band, the section headings (SectionHeading.jsx),
//      the table header rows, the filter bars and the ladder's connector
//      strip. Text NEVER sits on the bare layer — a watermark between the
//      letterforms of a heading is the failure this rule exists to prevent.
//      What is left for the texture is the true empty space: the gutters
//      between cards, the gaps between sections, and the tail below the last
//      row. That is the only place it is allowed to be.
//
// One component with a `variant` prop rather than five hand-rolled
// backgrounds, so those three rules have exactly one place to be broken.

// Uniform across the five tiling motifs. A variant is allowed to differ in
// what it draws, not in how loud it is — that is what stops one page's texture
// creeping up on the others.
//
// Every motif draws at a 1-unit line weight and lands between 2% and 4% ink
// coverage per tile, so no page's texture is meaningfully heavier than
// another's.
const OPACITY = 0.1

// The sign-in watermark is the mark itself at 720px, where the frame stroke is
// 56px of solid navy rather than a 1px rule. Equal alpha on those two does not
// read as equal presence — at 10% the watermark stops being a watermark and
// starts being a shape on the page — so it takes a lighter value to land at
// the same weight the ruled motifs do.
const OPACITY_MARK = 0.08

// The header band on every page is about 100-120px tall. Fading in over 200px
// clears it with room to spare, and gives the texture a top edge that reads as
// a watermark rather than as a background image starting at y=0.
const FADE = 'linear-gradient(to bottom, transparent 0px, #000 200px)'

// A tiling pattern, sized in user units. currentColor throughout so the whole
// layer takes its ink from the wrapper's text-navy and there is no second
// place a colour could be introduced.
function Tiled({ id, width, height, children }) {
  return (
    <svg className="h-full w-full" aria-hidden="true">
      <defs>
        <pattern id={id} width={width} height={height} patternUnits="userSpaceOnUse">
          {children}
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
    </svg>
  )
}

const VARIANTS = {
  // Officer — a ruled register. Horizontal rules at a fixed line pitch with a
  // column rule at wide intervals: the ground of a bound ledger the ranked
  // list is written onto.
  officer: (
    // 32px line pitch, not 24. At 3.5% the tighter ruling was invisible either
    // way; at 10% it read as hatching rather than as a ruled register, and it
    // was the densest of the five. Opening it up settles both.
    <Tiled id="motif-officer" width={160} height={32}>
      <path d="M0 31.5H160" stroke="currentColor" strokeWidth="1" />
      <path d="M0.5 0V32" stroke="currentColor" strokeWidth="1" />
    </Tiled>
  ),

  // Case Detail — the ladder itself, abstracted: runs of four nodes joined in
  // a chain, the links stopping at the end of each run rather than continuing,
  // so it reads as repeated four-hop chains and not as a lattice.
  case: (
    <Tiled id="motif-case" width={200} height={64}>
      <path d="M18.5 32H69.5M74.5 32H125.5M130.5 32H181.5" stroke="currentColor" strokeWidth="1" />
      <rect x="13.5" y="29.5" width="5" height="5" fill="currentColor" />
      <rect x="69.5" y="29.5" width="5" height="5" fill="currentColor" />
      <rect x="125.5" y="29.5" width="5" height="5" fill="currentColor" />
      <rect x="181.5" y="29.5" width="5" height="5" fill="currentColor" />
    </Tiled>
  ),

  // Rulebook — stacked rules of uneven length, all flush left. The shape a
  // block of clauses makes on a page when you are too far away to read it.
  rulebook: (
    <Tiled id="motif-rulebook" width={240} height={72}>
      <rect x="0" y="8" width="208" height="1" fill="currentColor" />
      <rect x="0" y="24" width="160" height="1" fill="currentColor" />
      <rect x="0" y="40" width="224" height="1" fill="currentColor" />
      <rect x="0" y="56" width="112" height="1" fill="currentColor" />
    </Tiled>
  ),

  // Inspector — a dotted route with waypoints. The path returns to its
  // starting height at the tile edge so it joins across tiles instead of
  // breaking into visible seams.
  inspector: (
    <Tiled id="motif-inspector" width={96} height={48}>
      <path
        d="M0 38H24V14H72V38H96"
        stroke="currentColor"
        strokeWidth="1"
        strokeDasharray="3 3"
      />
      <rect x="22.5" y="12.5" width="3" height="3" fill="currentColor" />
      <rect x="70.5" y="12.5" width="3" height="3" fill="currentColor" />
    </Tiled>
  ),

  // Auditor — a timeline scale: vertical rules at a wide pitch with ticks
  // stepped along them. The one motif that runs vertically, because the trail
  // it sits behind is read as a sequence in time rather than as a table.
  auditor: (
    <Tiled id="motif-auditor" width={56} height={48}>
      <path d="M12.5 0V48" stroke="currentColor" strokeWidth="1" />
      <path d="M12.5 12H20.5M12.5 36H20.5" stroke="currentColor" strokeWidth="1" />
    </Tiled>
  ),

  // Sign-in — the mark itself as a watermark. Large enough that its frame
  // falls outside the reading column, so what sits behind the text is the
  // empty middle of the mark rather than a stroke crossing a line of type.
  signin: (
    <div className="flex h-full w-full items-center justify-center">
      <LogoMark size={720} />
    </div>
  ),
}

export default function PageMotif({ variant }) {
  const motif = VARIANTS[variant]
  if (!motif) return null

  // The sign-in watermark is one drawing rather than a repeating tile, and it
  // differs from the five tiling motifs in both respects that matter here: it
  // takes the lighter opacity (see OPACITY_MARK), and it is not masked,
  // because fading its top 200px would cut the top edge off the frame and
  // leave a mark that looks broken rather than faint.
  const tiling = variant !== 'signin'

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 -z-10 overflow-hidden text-navy"
      style={{
        opacity: tiling ? OPACITY : OPACITY_MARK,
        // Both spellings: the unprefixed property is what Chrome and Firefox
        // read, the -webkit- one is what Safari still needs, and the demo may
        // be shown on any of the three.
        maskImage: tiling ? FADE : undefined,
        WebkitMaskImage: tiling ? FADE : undefined,
      }}
    >
      {motif}
    </div>
  )
}
