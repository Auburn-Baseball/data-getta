import { Cached } from '@mui/icons-material';

import { clearQueryCache } from '@/services/cacheService';
import { Theme } from '@/styles/theme';

export default function CacheRefreshButton() {
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
