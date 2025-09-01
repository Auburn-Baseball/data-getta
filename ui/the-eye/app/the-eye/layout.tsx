/*
* Layout used for each page of the app.
* Contains the desktop sidebar, mobile nav, and the top bar.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import Box from "@mui/material/Box";
import UI_Layout from "./components/UI_Layout";
import Toolbar from '@mui/material/Toolbar';

export default function Layout({ children }: { children: React.ReactNode }) {
    const sidebar_width: number = 240;
    
    return (
        <Box sx = {{ display: 'block' }}>
            <UI_Layout width = { sidebar_width } />

            <Box
                component='main'
                sx={{
                    width: { lg: `calc(100% - ${sidebar_width}px)` },
                    ml: { lg: `${sidebar_width}px` },
                }}
            >
                <Toolbar></Toolbar>
                { children }
            </Box>
        </Box>
    );
}