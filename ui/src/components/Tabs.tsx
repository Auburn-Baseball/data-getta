import { Link as RouterLink } from 'react-router';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Box from '@mui/material/Box';
import GroupsIcon from '@mui/icons-material/Groups';
import { common } from '@mui/material/colors';
import { Theme } from '@/utils/theme';
import auLogo from '@/assets/AuLogo.svg';

export default function Tabs() {
  return (
    <List>
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
    </List>
  );
}
