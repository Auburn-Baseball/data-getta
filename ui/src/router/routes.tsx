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
import type { DateRange, SeasonDateRange } from '@/types/dateRange';

type AppRoutesProps = {
  dateRange: DateRange;
  seasonRanges: SeasonDateRange[];
  onDateRangeChange: (range: DateRange) => void;
};

export default function AppRoutes({ dateRange, seasonRanges, onDateRangeChange }: AppRoutesProps) {
  return (
    <Routes>
      <Route element={<PublicOnly />}>
        <Route element={<AuthLayout />}>
          <Route index element={<LoginPage />} />
          <Route path="reset-password" element={<ResetPasswordPage />} />
        </Route>
      </Route>

      <Route element={<RequireAuth />}>
        <Route
          element={
            <MainLayout
              dateRange={dateRange}
              seasonRanges={seasonRanges}
              onDateRangeChange={onDateRangeChange}
            />
          }
        >
          <Route path="conferences" element={<ConferencePage dateRange={dateRange} />} />

          <Route
            path="team/:trackmanAbbreviation/player/:playerName"
            element={<PlayerPage dateRange={dateRange} />}
          >
            <Route
              path="stats/:year"
              element={<StatsTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
            />
            <Route
              path="heat-map/:year"
              element={<HeatMapTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
            />
            <Route path="percentiles/:year" element={<PercentilesTab dateRange={dateRange} />} />
          </Route>

          <Route path="team/:trackmanAbbreviation" element={<TeamPage dateRange={dateRange} />}>
            <Route index element={<Navigate to="roster" replace />} />
            <Route path="roster" element={<RosterTab dateRange={dateRange} />} />
            <Route
              path="batting"
              element={<BattingTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
            />
            <Route
              path="pitching"
              element={<PitchingTab startDate={dateRange.startDate} endDate={dateRange.endDate} />}
            />
          </Route>

          <Route path="teamperformance" element={<TeamPerformancePage dateRange={dateRange} />} />
        </Route>
      </Route>
    </Routes>
  );
}
