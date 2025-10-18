import { Navigate, Route, Routes } from 'react-router';

import PublicOnly from '@/components/auth/PublicOnly';
import RequireAuth from '@/components/auth/RequireAuth';
import MainLayout from '@/layouts/MainLayout';
import AuthLayout from '@/layouts/AuthLayout';
import LoginPage from '@/pages/LoginPage';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import ConferencePage from '@/pages/ConferencePage';
import TeamPage from '@/pages/TeamPage';
import RosterTab from '@/pages/RosterTab';
import BattingTab from '@/pages/BattingTab';
import PitchingTab from '@/pages/PitchingTab';
import PlayerPage from '@/pages/PlayerPage';
import TeamPerformancePage from '@/pages/TeamPerformancePage';
import { HeatMapTab, PercentilesTab, StatsTab } from '@/pages/PlayerPage/tabs';
import { DateRangeSelection } from '@/components/SeasonDateRangeSelect';

export type DateRangeState = {
  startDate: string;
  endDate: string;
};

type AppRoutesProps = {
  dateRange: DateRangeState;
  onDateRangeChange: (range: DateRangeSelection) => void;
  year: number;
};

export default function AppRoutes({ dateRange, onDateRangeChange, year }: AppRoutesProps) {
  return (
    <Routes>
      <Route element={<PublicOnly />}>
        <Route element={<AuthLayout />}>
          <Route index element={<LoginPage />} />
          <Route path="reset-password" element={<ResetPasswordPage />} />
        </Route>
      </Route>

      <Route element={<RequireAuth />}>
        <Route element={<MainLayout dateRange={dateRange} onDateRangeChange={onDateRangeChange} />}>
          <Route path="conferences" element={<ConferencePage year={year} />} />

          <Route
            path="team/:trackmanAbbreviation/player/:playerName"
            element={<PlayerPage year={year} />}
          >
            <Route
              path="stats/:year"
              element={<StatsTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
            />
            <Route
              path="heat-map/:year"
              element={<HeatMapTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
            />
            <Route path="percentiles/:year" element={<PercentilesTab year={year} />} />
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
              element={<PitchingTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
            />
          </Route>

          <Route path="teamperformance" element={<TeamPerformancePage year={year} />} />
        </Route>
      </Route>
    </Routes>
  );
}
