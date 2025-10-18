import Drawer from '@mui/material/Drawer';
import { Theme } from '@/styles/theme';
import { common } from '@mui/material/colors';
import TabGroup from '@/components/TabGroup';

export default function MobileSideBar({
  open,
  onTransitionEnd,
  onClose,
  width,
}: {
  open: boolean;
  onTransitionEnd: any;
  onClose: any;
  width: number;
}) {
  return (
    <Drawer
      variant="temporary"
      open={open}
      onTransitionEnd={onTransitionEnd}
      onClose={onClose}
      ModalProps={{ keepMounted: true }}
      sx={{
        display: { xs: 'block', lg: 'none' },
        '& .MuiDrawer-paper': {
          boxSizing: 'border-box',
          width: width,
          backgroundColor: Theme.palette.primary.main,
          color: common.white,
          paddingTop: 8,
        },
      }}
    >
      <TabGroup />
    </Drawer>
  );
}
