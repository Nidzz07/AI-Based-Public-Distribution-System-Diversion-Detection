import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { redirectFor } from '../roles.js'
import Sidebar from './Sidebar.jsx'
import TopBar from './TopBar.jsx'

// Role is owned by App now — the sign-in screen sets it before this shell ever
// renders, and the top bar's dropdown changes it afterwards. Both write the
// same state and both read the same map in roles.js, so switching to Inspector
// at the door and switching to Inspector in the top bar are the same action
// arriving from two places.
export default function Layout({ role, onRoleChange }) {
  const location = useLocation()

  // Two redirects, both of them wayfinding. Neither is a permission check:
  // they hold no secret and protect no data — they keep a person on a screen
  // that makes sense for the view they picked.
  //
  // First: no role chosen means no view has been picked, so there is nothing
  // to show and the door is where you go. Every app route is nested under this
  // component, including the catch-all, so any address typed straight into the
  // bar lands here before it renders anything.
  if (!role) return <Navigate to="/sign-in" replace />

  // Second: a role standing on another role's workspace screen goes to its
  // own. Reading it from the location on render rather than from an effect
  // means the wrong screen never paints for a frame first.
  const elsewhere = redirectFor(role, location.pathname)
  if (elsewhere) return <Navigate to={elsewhere} replace />

  return (
    <div className="flex min-h-screen">
      <Sidebar role={role} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar role={role} onRoleChange={onRoleChange} />

        {/* No padding here: the page's own header band needs to run edge to
            edge so its divider reads as a full-width rule. Each page pads its
            own header and content region instead.

            A column flex container so the page inside can take `flex-1` and
            fill the region even when its content is short. Without that, a
            page's motif layer — which is sized to the page element — would
            stop dead partway down the screen and leave a visible edge where
            the texture ends. */}
        <main className="flex flex-1 flex-col">
          <Outlet context={{ role }} />
        </main>
      </div>
    </div>
  )
}
