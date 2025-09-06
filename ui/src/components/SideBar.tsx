import { useState } from 'react';
import Box from '@mui/material/Box';

import TopBar from '@/components/TopBar';
import MobileSideBar from '@/components/MobileSideBar';
import DesktopSideBar from '@/components/DesktopSideBar';

export default function SideBar({ width }: { width: number }) {
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
      setMobileOpen(!mobileOpen);
    }
  };

  return (
    <>
      <TopBar drawerToggle={handleDrawerToggle} width={drawerWidth} />

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
