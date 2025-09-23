import { Link as RouterLink } from 'react-router';
import Tabs from './Tabs';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import eyeLogo from '@/assets/TheEyeLogo.svg';

export default function TabGroup() {
  return (
    <Box sx={{ textAlign: 'center' }}>
      <Link
        component={RouterLink}
        to="/conferences"
        prefetch="intent"
        underline="none"
        sx={{ display: 'inline-block' }}
      >
        <Box
          component="img"
          src={eyeLogo}
          sx={{ width: 134, height: 200 }}
          loading="lazy"
          decoding="async"
        />
      </Link>

      <Box sx={{ pb: 2 }} />
      <Tabs />
    </Box>
  );
}
