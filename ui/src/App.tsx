import { useCallback, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import LoginPage from '@/pages/LoginPage';
import ConferencePage from '@/pages/ConferencePage';
import AppLayout from '@/layouts/AppLayout';
import TeamPage from '@/pages/TeamPage';
import RosterTab from '@/pages/RosterTab';
import BattingTab from '@/pages/BattingTab';
import PitchingTab from '@/pages/PitchingTab';
import PlayerPage from '@/pages/PlayerPage';
import PercentilesTab from '@/pages/player/PercentilesTab';
import StatsTab from '@/pages/player/StatsTab';
import HeatMapTab from '@/pages/player/HeatMapTab';
import RequireAuth from '@/utils/supabase/requireauth';
import PublicOnly from '@/utils/supabase/publiconly';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import TeamPerformancePage from '@/pages/TeamPerformancePage';
import { DateRangeSelection } from '@/components/SeasonDateRangeSelect';

const basename = import.meta.env.BASE_URL.replace(/\/$/, '');

type DateRangeState = {
  startDate: string; // YYYY-MM-DD
  endDate: string; // YYYY-MM-DD
};

export default function App() {
  const [dateRange, setDateRange] = useState<DateRangeState>({
    startDate: '',
    endDate: '',
  });

  const year = dateRange.startDate
    ? new Date(dateRange.startDate).getFullYear()
    : new Date().getFullYear();

  const handleDateRangeChange = useCallback((range: DateRangeSelection) => {
    setDateRange({ startDate: range.startDate, endDate: range.endDate });
  }, []);

  return (
    <BrowserRouter basename={basename}>
      <Routes>
        {/* Public-only group: if signed in, redirect to /conferences */}
        <Route element={<PublicOnly />}>
          <Route index element={<LoginPage />} />
          <Route path="reset-password" element={<ResetPasswordPage />} />
        </Route>

        {/* Auth-only group */}
        <Route element={<RequireAuth />}>
          <Route
            element={<AppLayout dateRange={dateRange} onDateRangeChange={handleDateRangeChange} />}
          >
            <Route path="conferences" element={<ConferencePage year={year} />} />
            <Route
              path="team/:trackmanAbbreviation/player/:playerName"
              element={<PlayerPage startDate={dateRange.startDate} endDate={dateRange.endDate} />}
            >
              <Route
                path="stats/:year"
                element={<StatsTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
              />
              <Route
                path="heat-map/:year"
                element={<HeatMapTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
              />
              <Route path="percentiles/:year" element={<div>Percentiles Page</div>} />
            </Route>
            <Route path="team/:trackmanAbbreviation" element={<TeamPage year={year} />}>
              <Route index element={<Navigate to="roster" replace />} />
              <Route path="roster" element={<RosterTab year={year} />} />
              <Route
                path="batting"
                element={<BattingTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
              />
              <Route
                path="pitching"
                element={
                  <PitchingTab startDate={dateRange.startDate} endDate={dateRange.endDate} />
                }
              />
            </Route>
            <Route
              path="teamperformance"
              element={
                <TeamPerformancePage startDate={dateRange.startDate} endDate={dateRange.endDate} />
              }
            />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
