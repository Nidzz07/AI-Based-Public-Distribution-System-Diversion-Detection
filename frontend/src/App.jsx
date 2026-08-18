import { useState } from 'react'
import { Route, Routes } from 'react-router-dom'

import Layout from './components/Layout.jsx'
import Auditor from './pages/Auditor.jsx'
import CaseDetail from './pages/CaseDetail.jsx'
import Inspector from './pages/Inspector.jsx'
import NotFound from './pages/NotFound.jsx'
import Officer from './pages/Officer.jsx'
import Rulebook from './pages/Rulebook.jsx'
import SignIn from './pages/SignIn.jsx'

export default function App() {
  // Role was local to Layout until the sign-in screen existed. It has to live
  // above the router's outlet now because two things set it — the sign-in
  // screen, which is outside the shell, and the top bar's dropdown, which is
  // inside it — and both have to be moving the same piece of state.
  //
  // null means "nobody has chosen a view yet", and it is the only thing
  // standing between a visitor and the app. That is a front door, not
  // authentication: declared limitation 4 still holds, nothing is verified and
  // nothing is stored, so a refresh drops back to the sign-in screen.
  const [role, setRole] = useState(null)

  return (
    <Routes>
      <Route path="/sign-in" element={<SignIn onSelect={setRole} />} />

      <Route element={<Layout role={role} onRoleChange={setRole} />}>
        <Route index element={<Officer />} />
        <Route path="cases/:caseId" element={<CaseDetail />} />
        <Route path="rulebook" element={<Rulebook />} />
        <Route path="inspector" element={<Inspector />} />
        <Route path="auditor" element={<Auditor />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
