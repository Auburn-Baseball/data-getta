import { Link as RouterLink } from 'react-router';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import LoginIcon from '@mui/icons-material/Login';
import lineAnimation from '@/assets/LineAnimation.gif';

export default function LandingPage() {
  return (
    <Box
      sx={{ position: 'absolute', inset: 0, width: '100vw', height: '100vh', overflow: 'hidden' }}
    >
      <Box
        component="img"
        src={lineAnimation}
        alt="Animation"
        sx={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          zIndex: -1,
        }}
        loading="lazy"
        decoding="async"
      />

      <Box
        sx={{ display: 'flex', px: 4, py: 2, justifyContent: 'space-between', flexWrap: 'wrap' }}
      >
        <Typography variant="h3" sx={{ color: '#e86100', fontWeight: 700, whiteSpace: 'nowrap' }}>
          DATA GETTA
        </Typography>

        <Button
          component={RouterLink}
          to="/conferences"
          prefetch="intent"
          variant="contained"
          size="large"
          endIcon={<LoginIcon />}
          sx={{ backgroundColor: '#e86100', '&:hover': { backgroundColor: '#cc4e0b' } }}
        >
          Login
        </Button>
      </Box>
    </Box>
  );
}
