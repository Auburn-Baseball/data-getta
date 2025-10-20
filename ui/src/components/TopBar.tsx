import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import { common } from '@mui/material/colors';

import CacheRefreshButton from '@/components/CacheRefreshButton';
import SeasonDateRangeSelect from '@/components/SeasonDateRangeSelect';
import { Theme } from '@/styles/theme';
import type { DateRange, SeasonDateRange } from '@/types/dateRange';

type TopBarProps = {
  drawerToggle: () => void;
  width: number;
  startDate: string;
  endDate: string;
  seasonRanges: SeasonDateRange[];
  onDateRangeChange: (range: DateRange) => void;
};

export default function TopBar({
  drawerToggle,
  width,
  startDate,
  endDate,
  seasonRanges,
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
          value={{ startDate, endDate }}
          seasonRanges={seasonRanges}
          onDateRangeChange={onDateRangeChange}
        />
        <CacheRefreshButton />
      </Toolbar>
    </AppBar>
  );
}
