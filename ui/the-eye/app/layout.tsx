/*
* Root Layout for the entire app.
* Created from Next.js default and MUI integration docs
* https://mui.com/material-ui/integrations/nextjs/
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import CssBaseline from '@mui/material/CssBaseline';
import { AppRouterCacheProvider } from '@mui/material-nextjs/v14-appRouter';
import type { Metadata } from "next";
import ThemeProvider from '@mui/material/styles/ThemeProvider';
import { Theme } from './utils/theme';

export const metadata: Metadata = {
    title: "Data Getta",
};

export default function RootLayout({ children, }: Readonly<{ children: React.ReactNode; }>) {
    return (
        <html lang="en">
            <body>

                <AppRouterCacheProvider>
                    <ThemeProvider theme = {Theme}>
                        <CssBaseline />
                        {children}
                    </ThemeProvider>
                </AppRouterCacheProvider>

            </body>
        </html>
    );
}
