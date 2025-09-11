import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import LandingPage from '@/pages/LandingPage';
import ConferencePage from '@/pages/ConferencePage';
import AppLayout from '@/layouts/AppLayout';
import TeamPage from '@/pages/TeamPage';
import RosterTab from '@/pages/RosterTab';
import BatterTab from '@/pages/BatterTab';
import PitcherTab from '@/pages/PitcherTab';

const basename = import.meta.env.BASE_URL.replace(/\/$/, '');

function App() {
  return (
    <BrowserRouter basename={basename}>
      <Routes>
        <Route index element={<LandingPage />} />
        <Route element={<AppLayout />}>
          <Route path="conferences" element={<ConferencePage />} />
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
