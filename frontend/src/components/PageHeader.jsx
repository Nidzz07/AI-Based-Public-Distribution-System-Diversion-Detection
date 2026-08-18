// Every screen opens the same way: title, one line of context, then a hairline
// that separates "what this page is" from "what this page holds". The rule runs
// the full width of the column while the text stays inside the reading measure,
// so the divider reads as page structure rather than as a box around the title.
//
// bg-bg is an opaque plate, not a colour change: it paints the page ground at
// the value it already had. It is here because the page motif is a full-bleed
// layer behind the whole article, and a transparent header band would let the
// texture run between the letterforms of the title and its note. The motif's
// top fade attenuates that but does not remove it — at the note's baseline the
// fade is still better than half open — so occlusion, not opacity, is what
// keeps this band clean. See PageMotif.jsx, contrast discipline.
export default function PageHeader({ title, note }) {
  return (
    <header className="border-b border-border bg-bg px-8 py-6">
      <div className="max-w-4xl">
        <h1 className="font-display text-page-title text-navy">{title}</h1>
        {note ? <p className="mt-2 max-w-3xl text-body text-ink-secondary">{note}</p> : null}
      </div>
    </header>
  )
}
