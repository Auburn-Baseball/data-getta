import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import { common } from '@mui/material/colors';
import { Theme } from '@/utils/theme';
import SeasonDateRangeSelect, { DateRangeSelection } from '@/components/SeasonDateRangeSelect';
import { CacheRefreshButton } from '@/components/CacheRefreshButton';

type TopBarProps = {
  drawerToggle: () => void;
  width: number;
  startDate: string | null;
  endDate: string | null;
  onDateRangeChange: (range: DateRangeSelection) => void;
};

export default function TopBar({
  drawerToggle,
  width,
  startDate,
  endDate,
  onDateRangeChange,
}: TopBarProps) {
  return (
    <AppBar
      component="header"
      position="fixed"
      sx={{
        width: { lg: `calc(100% - ${width}px)` },
        ml: { lg: `${width}px` },
        backgroundColor: common.white,
      }}
    >
      <Toolbar sx={{ display: 'flex' }}>
        <IconButton
          onClick={drawerToggle}
          sx={{
            mr: 2,
            display: { lg: 'none' },
            color: Theme.palette.primary.main,
          }}
        >
          <MenuIcon />
        </IconButton>
        <SeasonDateRangeSelect
          startDate={startDate}
          endDate={endDate}
          onDateRangeChange={onDateRangeChange}
        />
        <CacheRefreshButton />
      </Toolbar>
    </AppBar>
  );
}
