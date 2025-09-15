import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import LandingPage from '@/pages/LandingPage';
import ConferencePage from '@/pages/ConferencePage';
import AppLayout from '@/layouts/AppLayout';
import TeamPage from '@/pages/TeamPage';
import RosterTab from '@/pages/RosterTab';
import BattingTab from '@/pages/BattingTab';
import PitchingTab from '@/pages/PitchingTab';
import PlayerPage from '@/pages/PlayerPage';

const basename = import.meta.env.BASE_URL.replace(/\/$/, '');

function App() {
  return (
    <BrowserRouter basename={basename}>
      <Routes>
        <Route index element={<LandingPage />} />
        <Route element={<AppLayout />}>
          <Route path="conferences" element={<ConferencePage />} />
          <Route path="team/:trackmanAbbreviation/player/:playerName" element={<PlayerPage />} >
            <Route index element={<Navigate to="stats" replace />} />
            <Route path="stats" element={<div>a</div>} />
            <Route path="heat-map" element={<div>Heat Map Page</div>} />
            <Route path="percentiles" element={<div>Percentiles Page</div>} />
          </Route>
          <Route path="team/:trackmanAbbreviation" element={<TeamPage />}>
            <Route index element={<Navigate to="roster" replace />} />
            <Route path="roster" element={<RosterTab />} />
            <Route path="batting" element={<BattingTab />} />
            <Route path="pitching" element={<PitchingTab />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;