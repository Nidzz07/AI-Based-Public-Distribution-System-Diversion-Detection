import { NavLink } from 'react-router-dom'

// Case Detail points at the demo case. Once the officer list is real it will
// be reached by clicking a row; it stays in the nav for now so the shell can
// be walked end to end.
const NAV_ITEMS = [
  { to: '/', label: 'Officer', end: true },
  { to: '/cases/C-0041', label: 'Case Detail', end: false },
  { to: '/rulebook', label: 'Rulebook', end: false },
  { to: '/inspector', label: 'Inspector', end: false },
  { to: '/auditor', label: 'Auditor', end: false },
]

function navClasses({ isActive }) {
  // Green edge bar plus a green-tinted ground. This is a navigation
  // active-state indicator, which is a different job from the severity
  // left-border on a data row: that one encodes a value, this one encodes
  // "you are here". Nothing else in the shell carries a left accent, so the
  // two never appear on the same screen competing for the same reading.
  const base = 'block border-l-4 py-2 pl-4 pr-4 text-body-secondary transition-colors'
  return isActive
    ? `${base} border-green bg-green/15 font-medium text-white`
    : `${base} border-transparent text-white/60 hover:border-white/20 hover:text-white`
}

export default function Sidebar() {
  return (
    <aside className="flex w-sidebar shrink-0 flex-col bg-navy">
      <div className="flex h-topbar items-center px-6">
        {/* section-heading carries its own 600 weight, so font-semibold is not
            repeated here — the named size token IS the whole style. */}
        <span className="font-display text-section-heading tracking-wide text-white">
          LEAKPROOF
        </span>
      </div>

      <nav className="flex flex-col gap-1 py-4">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={navClasses}>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* meta-label bakes its own 1.4 line-height, so leading-relaxed is gone
          rather than overriding half the token. */}
      <div className="mt-auto px-6 py-6 text-meta-label text-white/40">
        Synthetic data, seed 4521.
        <br />
        Demo build — not a system of record.
      </div>
    </aside>
  )
}
