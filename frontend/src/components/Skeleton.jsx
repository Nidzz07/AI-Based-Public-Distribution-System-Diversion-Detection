import { CARD } from '../ui.js'

// Skeletons, not spinners. CLAUDE.md bans spinner-only loading states, and the
// reason is worth keeping in view: a spinner says "something is happening", a
// skeleton says "a list of rows is coming and here is how tall it will be".
// The page does not jump when the data lands, which on a demo screen being
// projected is the difference between smooth and twitchy.
//
// animate-pulse moves opacity only. No gradient — the palette is five colours
// and a shimmer would introduce a sixth.

function Bar({ width = 'w-full', className = '' }) {
  return <div className={`h-4 rounded bg-border ${width} ${className}`} aria-hidden="true" />
}

// Mirrors the shape of a case row: title over subtitle on the left, short
// values on the right.
export function SkeletonRows({ rows = 5 }) {
  return (
    <ul className="animate-pulse" aria-hidden="true">
      {Array.from({ length: rows }, (_, index) => (
        <li key={index} className={`${CARD} mt-2 flex items-center gap-4 border-l-4 border-l-border px-4 py-4`}>
          <div className="flex-1 space-y-2">
            <Bar width="w-48" />
            <Bar width="w-32" className="h-2" />
          </div>
          <Bar width="w-24" className="h-2" />
          <Bar width="w-12" />
        </li>
      ))}
    </ul>
  )
}

// For a page whose content is prose or a panel rather than a list.
export function SkeletonPanel({ lines = 3 }) {
  return (
    <div className={`${CARD} animate-pulse space-y-2 p-6`} aria-hidden="true">
      <Bar width="w-32" className="h-2" />
      {Array.from({ length: lines }, (_, index) => (
        <Bar key={index} width={index === lines - 1 ? 'w-2/3' : 'w-full'} />
      ))}
    </div>
  )
}

// Screen readers get a sentence; sighted readers get the shape above. Pairing
// them keeps the loading state announced without reading out placeholder bars.
export function LoadingRegion({ label, children }) {
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">{label}</span>
      {children}
    </div>
  )
}
