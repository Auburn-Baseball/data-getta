import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import LandingPage from '@/pages/LandingPage';
import ConferencePage from '@/pages/ConferencePage';
import AppLayout from '@/layouts/AppLayout';
import TeamPage from '@/pages/TeamPage';
import RosterTab from '@/pages/RosterTab';
import BattingTab from '@/pages/BattingTab';
import PitchingTab from '@/pages/PitchingTab';
import PlayerPage from '@/pages/PlayerPage';
import StatsTab from '@/pages/player/StatsTab';
import HeatMapTab from '@/pages/player/HeatMapTab';

const basename = import.meta.env.BASE_URL.replace(/\/$/, '');

function App() {
  return (
    <BrowserRouter basename={basename}>
      <Routes>
        <Route index element={<LandingPage />} />
        <Route element={<AppLayout />}>
          <Route path="conferences" element={<ConferencePage />} />
          <Route path="team/:trackmanAbbreviation/player/:playerName" element={<PlayerPage />}>
            <Route path="stats/:year" element={<StatsTab />} />
            <Route path="heat-map/:year" element={<HeatMapTab />} />
            <Route path="percentiles/:year" element={<div>Percentiles Page</div>} />
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
