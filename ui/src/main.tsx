import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from '@/App';

import { ThemeProvider, CssBaseline } from '@mui/material';
import { Theme } from './utils/theme';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider theme={Theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </StrictMode>,
);
