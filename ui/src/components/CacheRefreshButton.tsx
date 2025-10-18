import { clearQueryCache } from '@/utils/supabase/cache';
import { Cached } from '@mui/icons-material';
import { Theme } from '@/utils/theme';

export function CacheRefreshButton() {
  return (
    <Cached
      onClick={() => {
        clearQueryCache();
        window.location.reload();
      }}
      sx={{
        color: Theme.palette.primary.light,
        cursor: 'pointer',
        fontSize: '32px',
        marginLeft: '16px',
      }}
    />
  );
}
