import { type TransitionEventHandler } from 'react';

import Drawer, { type DrawerProps } from '@mui/material/Drawer';
import { Theme } from '@/styles/theme';
import { common } from '@mui/material/colors';
import TabGroup from '@/components/TabGroup';

type MobileSideBarProps = {
  open: boolean;
  onTransitionEnd?: TransitionEventHandler<HTMLDivElement>;
  onClose?: DrawerProps['onClose'];
  width: number;
};

export default function MobileSideBar({
  open,
  onTransitionEnd,
  onClose,
  width,
}: MobileSideBarProps) {
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
