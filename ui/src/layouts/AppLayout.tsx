import Box from '@mui/material/Box';
import SideBar from '@/components/SideBar';
import Toolbar from '@mui/material/Toolbar';
import { Outlet } from 'react-router';
import { DateRangeSelection } from '@/components/SeasonDateRangeSelect';

type DateRangeState = {
  startDate: string | null;
  endDate: string | null;
};

type AppLayoutProps = {
  dateRange: DateRangeState;
  onDateRangeChange: (range: DateRangeSelection) => void;
};

export default function AppLayout({ dateRange, onDateRangeChange }: AppLayoutProps) {
  const sidebarWidth = 240;

  return (
    <Box sx={{ display: 'block' }}>
      <SideBar
        width={sidebarWidth}
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
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
