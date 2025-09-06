import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import LandingPage from '@/pages/LandingPage';
import ConferencePage from '@/pages/ConferencePage';
import AppLayout from '@/layouts/AppLayout';
import TeamPage from '@/pages/TeamPage';
import RosterTab from '@/pages/RosterTab';
import BatterTab from '@/pages/BatterTab';
import PitcherTab from '@/pages/PitcherTab';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* force user to login each time */}
        <Route index element={<LandingPage />} />

        <Route element={<AppLayout />}>
          <Route index path="conferences" element={<ConferencePage />} />
          <Route path="team/:trackmanAbbreviation" element={<TeamPage />}>
            <Route index element={<Navigate to="roster" replace />} />
            <Route path="roster" element={<RosterTab />} />
            <Route path="batting" element={<BatterTab />} />
            <Route path="pitching" element={<PitcherTab />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
