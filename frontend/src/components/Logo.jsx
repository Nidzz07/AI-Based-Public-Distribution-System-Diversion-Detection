// The mark. Drawn in code so the app ships no image asset and no icon
// dependency, and so the stroke can inherit whatever ground it lands on —
// navy on the cream pages, white on the navy sidebar.
//
// WHAT IT IS, and why it is this and not something else. The product is a
// four-hop ladder of readings that steps down where grain left the chain, and
// a rule underneath it that the reading has to be defensible against. So the
// device is exactly that: a stepped line descending twice, a solid baseline
// beneath it, both held inside a square frame.
//
// The frame is the point of the whole thing. A bounded device containing one
// simple figure is what a registry stamp, a passport-office crest or a tax
// form's letterhead looks like, and it is the opposite of the soft blob with a
// gradient in it that every tool ships with now. Everything here is
// therefore deliberately flat: no gradient, no second colour, no bevel, no
// rounded corners at all — a 4px radius on a 32px mark would read as a
// software icon, and this is meant to read as an emblem.
//
// Geometry is on a 32-unit grid so it survives being scaled: the 2.5-unit
// stroke is 2.2px at the 28px sidebar size and 5px at the 64px sign-in size,
// which is heavy enough to hold at both without a second, "small" drawing.

export function LogoMark({ size = 32, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      // Decorative in every placement: the word LEAKPROOF is always beside it
      // or under it, so a screen reader announcing the mark as well would just
      // say the name twice.
      aria-hidden="true"
      focusable="false"
    >
      <rect x="1.25" y="1.25" width="29.5" height="29.5" stroke="currentColor" strokeWidth="2.5" />
      {/* One path rather than three strokes, so the corners mitre cleanly
          instead of leaving notches where the segments butt together. */}
      <path
        d="M6.5 9H15V16.5H25.5"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="miter"
      />
      <rect x="6.5" y="21.5" width="19" height="2.5" fill="currentColor" />
    </svg>
  )
}

// Mark plus wordmark, locked together at the one size the sidebar uses. Kept
// here rather than assembled in Sidebar.jsx so the sign-in screen and the
// sidebar cannot drift into two different lockups.
export function Logo({ className = '' }) {
  return (
    <span className={`flex items-center gap-2 ${className}`}>
      <LogoMark size={28} />
      {/* section-heading carries its own 600 weight, so font-semibold is not
          repeated here — the named size token IS the whole style. */}
      <span className="font-display text-section-heading tracking-wide">LEAKPROOF</span>
    </span>
  )
}
