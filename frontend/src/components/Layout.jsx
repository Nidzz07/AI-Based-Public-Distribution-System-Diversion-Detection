import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import Sidebar from './Sidebar.jsx'
import TopBar from './TopBar.jsx'

export default function Layout() {
  // Role lives here and travels down through the router's outlet context.
  // No state library, and nothing persists it — a refresh returns to Officer.
  const [role, setRole] = useState('Officer')

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar role={role} onRoleChange={setRole} />

        {/* No padding here: the page's own header band needs to run edge to
            edge so its divider reads as a full-width rule. Each page pads its
            own header and content region instead. */}
        <main className="flex-1">
          <Outlet context={{ role }} />
        </main>
      </div>
    </div>
  )
}
