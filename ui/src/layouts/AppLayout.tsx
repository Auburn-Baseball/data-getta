import Box from '@mui/material/Box';
import SideBar from '@/components/SideBar';
import Toolbar from '@mui/material/Toolbar';
import { Outlet } from 'react-router';

export default function AppLayout() {
  const sidebar_width: number = 240;

  return (
    <Box sx={{ display: 'block' }}>
      <SideBar width={sidebar_width} />

      <Box
        component="main"
        sx={{
          width: { lg: `calc(100% - ${sidebar_width}px)` },
          ml: { lg: `${sidebar_width}px` },
        }}
      >
        <Toolbar></Toolbar>
        <Outlet />
      </Box>
    </Box>
  );
}
