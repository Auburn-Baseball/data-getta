import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import LoginPage from '@/pages/LoginPage';
import ConferencePage from '@/pages/ConferencePage';
import AppLayout from '@/layouts/AppLayout';
import TeamPage from '@/pages/TeamPage';
import RosterTab from '@/pages/RosterTab';
<<<<<<< HEAD
import BattingTab from '@/pages/BattingTab';
import PitchingTab from '@/pages/PitchingTab';
import PlayerPage from '@/pages/PlayerPage';
=======
import BatterTab from '@/pages/BatterTab';
import PitcherTab from '@/pages/PitcherTab';
import RequireAuth from '@/utils/supabase/requireauth';
import PublicOnly from '@/utils/supabase/publiconly';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
>>>>>>> upstream/main

const basename = import.meta.env.BASE_URL.replace(/\/$/, '');

export default function App() {
  return (
    <BrowserRouter basename={basename}>
      <Routes>
<<<<<<< HEAD
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
=======
        {/* Public-only group: if signed in, redirect to /conferences */}
        <Route element={<PublicOnly />}>
          <Route index element={<LoginPage />} />
          <Route path="reset-password" element={<ResetPasswordPage />} />
        </Route>

        {/* Auth-only group */}
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route path="conferences" element={<ConferencePage />} />
            <Route path="team/:trackmanAbbreviation" element={<TeamPage />}>
              <Route index element={<Navigate to="roster" replace />} />
              <Route path="roster" element={<RosterTab />} />
              <Route path="batting" element={<BatterTab />} />
              <Route path="pitching" element={<PitcherTab />} />
            </Route>
>>>>>>> upstream/main
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
<<<<<<< HEAD

export default App;
=======
>>>>>>> upstream/main
