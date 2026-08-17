import { Route, Routes } from 'react-router-dom'

import Layout from './components/Layout.jsx'
import Auditor from './pages/Auditor.jsx'
import CaseDetail from './pages/CaseDetail.jsx'
import Inspector from './pages/Inspector.jsx'
import NotFound from './pages/NotFound.jsx'
import Officer from './pages/Officer.jsx'
import Rulebook from './pages/Rulebook.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
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
