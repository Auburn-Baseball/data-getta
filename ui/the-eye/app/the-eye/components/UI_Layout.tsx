/*
* Combines all of the home page layout components together.
* Adds functionality for the menu icon on mobile devices.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

'use client'

import { useState } from 'react';
import Box from '@mui/material/Box';

import TopBar from './TopBar';
import MobileSideBar from './MobileSideBar';
import DesktopSideBar from './DesktopSideBar';

export default function UI_Layout({ width }: { width: number }) {
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
            <TopBar drawerToggle={ handleDrawerToggle } width={drawerWidth}/>
        
            <Box
                component='nav'
                sx={{ width: { lg: drawerWidth }}}
            >
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
