import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import { Outlet } from 'react-router';

import SideBar from '@/components/SideBar';
import type { DateRange, SeasonDateRange } from '@/types/dateRange';

type MainLayoutProps = {
  dateRange: DateRange;
  seasonRanges: SeasonDateRange[];
  onDateRangeChange: (range: DateRange) => void;
};

export default function MainLayout({
  dateRange,
  seasonRanges,
  onDateRangeChange,
}: MainLayoutProps) {
  const sidebarWidth = 240;

  return (
    <Box sx={{ display: 'block' }}>
      <SideBar
        width={sidebarWidth}
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        seasonRanges={seasonRanges}
        onDateRangeChange={onDateRangeChange}
      />

      <Box
        component="main"
        sx={{
          width: { lg: `calc(100% - ${sidebarWidth}px)` },
          ml: { lg: `${sidebarWidth}px` },
        }}
      >
        <Toolbar />
        <Outlet context={dateRange} />
      </Box>
    </Box>
  );
}
