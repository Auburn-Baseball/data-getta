import { createTheme, responsiveFontSizes } from '@mui/material/styles';

export const Theme = responsiveFontSizes(
  createTheme({
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
      fontFamily:
        '"Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", sans-serif',
    },
  }),
);
