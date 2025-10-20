import { useState } from 'react';
import Box from '@mui/material/Box';

import TopBar from '@/components/TopBar';
import MobileSideBar from '@/components/MobileSideBar';
import DesktopSideBar from '@/components/DesktopSideBar';
import type { DateRange, SeasonDateRange } from '@/types/dateRange';

type SideBarProps = {
  width: number;
  startDate: string;
  endDate: string;
  seasonRanges: SeasonDateRange[];
  onDateRangeChange: (range: DateRange) => void;
};

export default function SideBar({
  width,
  startDate,
  endDate,
  seasonRanges,
  onDateRangeChange,
}: SideBarProps) {
  const drawerWidth = width;
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const handleDrawerClose = () => {
    setIsClosing(true);
    setMobileOpen(false);
  };

  const handleDrawerTransitionEnd = () => {
    setIsClosing(false);
  };

  const handleDrawerToggle = () => {
    if (!isClosing) {
      setMobileOpen((prev) => !prev);
    }
  };

  return (
    <>
      <TopBar
        drawerToggle={handleDrawerToggle}
        width={drawerWidth}
        startDate={startDate}
        endDate={endDate}
        seasonRanges={seasonRanges}
        onDateRangeChange={onDateRangeChange}
      />

      <Box component="nav" sx={{ width: { lg: drawerWidth } }}>
        <MobileSideBar
          open={mobileOpen}
          onTransitionEnd={handleDrawerTransitionEnd}
          onClose={handleDrawerClose}
          width={drawerWidth}
        />

        <DesktopSideBar width={drawerWidth} />
      </Box>
    </>
  );
}
