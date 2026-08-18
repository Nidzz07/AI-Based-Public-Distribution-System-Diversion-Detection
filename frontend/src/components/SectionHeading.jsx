import { CAPTION } from '../ui.js'

// A section's heading and its one-line caption, on an opaque plate.
//
// The plate is the whole reason this is a component rather than two tags. Every
// page carries a full-bleed motif layer behind it, and a heading sitting on
// bare page ground has that texture running between its letterforms — which is
// exactly what the motif is not allowed to do. bg-bg paints the page ground at
// the value it already had, so nothing changes colour; the texture simply stops
// at the edge of the text block.
//
// Heading and caption are plated TOGETHER, in one element, rather than each
// carrying its own background. The caption's 4px top margin would otherwise be
// a transparent sliver between them, wide enough for a ruled motif to show one
// line through — a gap that reads as a line struck through the heading block.
//
// Navy on the h2 is correct and stays: per CLAUDE.md navy is for headings, and
// this is one. The caption underneath is ink-secondary, as all captions are.
export default function SectionHeading({ title, children }) {
  return (
    <div className="bg-bg">
      <h2 className="font-display text-section-heading text-navy">{title}</h2>
      {children ? <p className={CAPTION}>{children}</p> : null}
    </div>
  )
}
