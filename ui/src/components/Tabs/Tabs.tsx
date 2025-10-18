import { Link as RouterLink, useNavigate } from 'react-router';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Box from '@mui/material/Box';
import GroupsIcon from '@mui/icons-material/Groups';
import LeaderboardIcon from '@mui/icons-material/Leaderboard';
import LogoutIcon from '@mui/icons-material/Logout';
import { common } from '@mui/material/colors';

import auLogo from '@/assets/AuLogo.svg';
import { logout } from '@/services/authService';
import { Theme } from '@/styles/theme';

export default function Tabs() {
  const navigate = useNavigate();

  const handleSignOut = async () => {
    try {
      await logout();
      navigate('/', { replace: true });
    } catch (e) {
      console.error('Sign out failed', e);
    }
  };

  return (
    <List sx={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column' }}>
      <ListItem disablePadding sx={{ pb: 2 }}>
        <ListItemButton
          component={RouterLink}
          to="/team/AUB_TIG/roster"
          sx={{
            gap: 2,
            justifyContent: 'center',
            ':hover': { bgcolor: Theme.palette.primary.light },
          }}
        >
          <ListItemIcon sx={{ minWidth: 'auto' }}>
            <Box
              component="img"
              src={auLogo}
              alt="Auburn logo"
              sx={{ width: 24, height: 24, display: 'block' }}
            />
          </ListItemIcon>
          <ListItemText sx={{ '& .MuiTypography-root': { fontWeight: 'bold' }, flexGrow: 0 }}>
            Auburn
          </ListItemText>
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding sx={{ pb: 2 }}>
        <ListItemButton
          component={RouterLink}
          to="/conferences"
          sx={{
            gap: 2,
            justifyContent: 'center',
            ':hover': { bgcolor: Theme.palette.primary.light },
          }}
        >
          <ListItemIcon sx={{ minWidth: 'auto' }}>
            <GroupsIcon sx={{ color: common.white }} />
          </ListItemIcon>
          <ListItemText sx={{ '& .MuiTypography-root': { fontWeight: 'bold' }, flexGrow: 0 }}>
            Teams
          </ListItemText>
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding sx={{ pb: 2 }}>
        <ListItemButton
          component={RouterLink}
          to="/teamperformance"
          sx={{
            gap: 2,
            justifyContent: 'center',
            ':hover': { bgcolor: Theme.palette.primary.light },
          }}
        >
          <ListItemIcon sx={{ minWidth: 'auto' }}>
            <LeaderboardIcon sx={{ color: common.white }} />
          </ListItemIcon>
          <ListItemText sx={{ '& .MuiTypography-root': { fontWeight: 'bold' }, flexGrow: 0 }}>
            Team Performance
          </ListItemText>
        </ListItemButton>
      </ListItem>

      <ListItem disablePadding sx={{ pb: 2, mt: 'auto' }}>
        <ListItemButton
          onClick={handleSignOut}
          sx={{
            gap: 2,
            justifyContent: 'center',
            ':hover': { bgcolor: Theme.palette.primary.light },
          }}
        >
          <ListItemIcon sx={{ minWidth: 'auto' }}>
            <LogoutIcon sx={{ color: common.white }} />
          </ListItemIcon>
          <ListItemText sx={{ '& .MuiTypography-root': { fontWeight: 'bold' }, flexGrow: 0 }}>
            Sign out
          </ListItemText>
        </ListItemButton>
      </ListItem>
    </List>
  );
}
