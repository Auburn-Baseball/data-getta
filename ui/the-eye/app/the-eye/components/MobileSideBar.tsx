/*
* Menu nav that is displayed on mobile only.
* Created based on MUI examples.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import Drawer from '@mui/material/Drawer';
import { Theme } from '@/app/utils/theme';
import { common } from '@mui/material/colors';
import TabGroup from './TabGroup';

export default function MobileSideBar({ open, onTransitionEnd, onClose, width}: 
    {open: boolean, onTransitionEnd: any, onClose: any, width: number}) {
    
    return (
        <Drawer
            variant="temporary"
            open={open}
            onTransitionEnd={ onTransitionEnd }
            onClose={ onClose }
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