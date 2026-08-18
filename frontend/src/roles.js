// The role model, in one place so the sign-in screen, the top bar's switcher
// and the sidebar cannot disagree about what a role is offered.
//
// WHAT THIS IS NOT. This is wayfinding. It decides which screens a person is
// shown links to and which screen they land on. It is not access control and
// nothing here protects anything: the API answers the same rows whichever
// role is set, every page remains reachable by typing its address, and the
// role itself is picked from a list with no password. Declared limitation 4
// in PROJECT-BRIEF.md — roles are a switcher, not authentication.

export const ROLES = ['Officer', 'Inspector', 'Auditor']

// Where each role starts, and where it is sent back to if it ends up on
// another role's screen. Sign-in and the top-bar switcher both read this, so
// choosing Inspector at the door and choosing Inspector mid-session land in
// exactly the same place.
export const ROLE_HOME = {
  Officer: '/',
  Inspector: '/inspector',
  Auditor: '/auditor',
}

// The sidebar, per role: one workspace screen, then the two screens everybody
// reads. Case Detail is on all three lists because every role opens cases. So
// is the Rulebook — it is the document the scores are derived from, and an
// officer, an inspector and an auditor all have reason to check what a case
// was measured against. Filtering it out of the nav would leave F2, the
// editable rulebook, reachable only by typing its address.
const SHARED = [
  { to: '/cases/C-0041', label: 'Case Detail', end: false },
  { to: '/rulebook', label: 'Rulebook', end: false },
]

export const ROLE_NAV = {
  Officer: [{ to: '/', label: 'Officer', end: true }, ...SHARED],
  Inspector: [{ to: '/inspector', label: 'Inspector', end: false }, ...SHARED],
  Auditor: [{ to: '/auditor', label: 'Auditor', end: false }, ...SHARED],
}

// The three workspace screens and who owns each. A role standing on another
// role's screen is sent home; everything absent from this map — Case Detail,
// the Rulebook, the 404 — belongs to no role and nobody is moved off it.
const OWNER = {
  '/': 'Officer',
  '/inspector': 'Inspector',
  '/auditor': 'Auditor',
}

// Returns the path to send this role to, or null to leave them where they are.
export function redirectFor(role, pathname) {
  const owner = OWNER[pathname]
  return owner && owner !== role ? ROLE_HOME[role] : null
}
