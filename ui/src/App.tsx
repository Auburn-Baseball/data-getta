import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import LoginPage from '@/pages/LoginPage';
import ConferencePage from '@/pages/ConferencePage';
import AppLayout from '@/layouts/AppLayout';
import TeamPage from '@/pages/TeamPage';
import RosterTab from '@/pages/RosterTab';
import BatterTab from '@/pages/BatterTab';
import PitcherTab from '@/pages/PitcherTab';
import AuthGuard from '@/utils/supabase/guard';
import ResetPasswordPage from '@/pages/ResetPasswordPage';

const basename = import.meta.env.BASE_URL.replace(/\/$/, '');

export default function App() {
  return (
    <BrowserRouter basename={basename}>
      <Routes>
        <Route element={<AuthGuard />}>
          <Route index element={<LoginPage />} />
          <Route path="reset-password" element={<ResetPasswordPage />} />

          <Route element={<AppLayout />}>
            <Route path="conferences" element={<ConferencePage />} />
            <Route path="team/:trackmanAbbreviation" element={<TeamPage />}>
              <Route index element={<Navigate to="roster" replace />} />
              <Route path="roster" element={<RosterTab />} />
              <Route path="batting" element={<BatterTab />} />
              <Route path="pitching" element={<PitcherTab />} />
            </Route>
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
