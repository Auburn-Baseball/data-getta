/*
* Branding theme for the app.
* Created based on Auburn's branding guide.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

'use client'

import { Inter } from 'next/font/google'
import { createTheme, responsiveFontSizes } from "@mui/material/styles";

const inter = Inter({ subsets: ['latin'] });

export const Theme = responsiveFontSizes(createTheme({

    palette: {
        primary: {
            main: '#0b2341',
            light: '#233954',
            contrastText: '#fff',
        },

        secondary: {
            main: '#e86100',
            light: '#ea711a',
            dark: '#cc4e0b',
            contrastText: '#fff',
        },

        text: {
            primary: 'rgba(11, 35, 65, 1)',
            secondary: 'rgba(11, 35, 65, 0.6)',
            disabled: 'rgba(11, 35, 65, 0.38)',
        },
    },

    typography: {
        fontFamily: inter.style.fontFamily,
    },

}));