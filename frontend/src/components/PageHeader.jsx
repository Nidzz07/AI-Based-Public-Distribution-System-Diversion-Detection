// Every screen opens the same way: title, one line of context, then a hairline
// that separates "what this page is" from "what this page holds". The rule runs
// the full width of the column while the text stays inside the reading measure,
// so the divider reads as page structure rather than as a box around the title.
export default function PageHeader({ title, note }) {
  return (
    <header className="border-b border-border px-8 py-6">
      <div className="max-w-4xl">
        <h1 className="font-display text-page-title text-navy">{title}</h1>
        {note ? <p className="mt-2 max-w-3xl text-body text-ink-secondary">{note}</p> : null}
      </div>
    </header>
  )
}
