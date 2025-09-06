import Drawer from '@mui/material/Drawer';
import { Theme } from '@/utils/theme';
import { common } from '@mui/material/colors';
import TabGroup from '@/components/TabGroup';

export default function DesktopSideBar({ width }: { width: number }) {
  return (
    <Drawer
      variant="permanent"
      sx={{
        display: { xs: 'none', lg: 'block' },
        '& .MuiDrawer-paper': {
          boxSizing: 'border-box',
          width: width,
          paddingTop: 6,
          backgroundColor: Theme.palette.primary.main,
          color: common.white,
        },
      }}
      open
    >
      <TabGroup />
    </Drawer>
  );
}
