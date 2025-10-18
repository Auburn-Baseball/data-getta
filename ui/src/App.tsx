import { useCallback, useEffect, useState } from 'react';
import { BrowserRouter, useLocation, useNavigate } from 'react-router';

import AppRoutes from '@/router/routes';
import { fetchSeasonDateRanges } from '@/services/seasonService';
import type { DateRange, SeasonDateRange } from '@/types/dateRange';
import { areDateRangesEqual } from '@/utils/dateRange';

const basename = import.meta.env.BASE_URL.replace(/\/$/, '');

export default function App() {
  return (
    <BrowserRouter basename={basename}>
      <AppShell />
    </BrowserRouter>
  );
}

function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();

  const [seasonRanges, setSeasonRanges] = useState<SeasonDateRange[]>([]);
  const [dateRange, setDateRange] = useState<DateRange | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const loadSeasonRanges = async () => {
      try {
        setLoading(true);
        const { ranges, errorMessage } = await fetchSeasonDateRanges();

        if (!isMounted) {
          return;
        }

        if (errorMessage) {
          setError(errorMessage);
        }

        if (!ranges.length) {
          setSeasonRanges([]);
          return;
        }

        setSeasonRanges(ranges);
      } catch (err) {
        if (isMounted) {
          setError('Failed to load season dates.');
          console.error('[App] Failed to fetch season dates', err);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    void loadSeasonRanges();

    return () => {
      isMounted = false;
    };
  }, []);

  const updateSearchParams = useCallback(
    (range: DateRange, replace = false) => {
      const params = new URLSearchParams(location.search);
      params.set('start', range.startDate);
      params.set('end', range.endDate);

      navigate(
        {
          pathname: location.pathname,
          search: `?${params.toString()}`,
        },
        { replace },
      );
    },
    [location.pathname, location.search, navigate],
  );

  useEffect(() => {
    if (!seasonRanges.length) {
      return;
    }

    const params = new URLSearchParams(location.search);
    const startParam = params.get('start');
    const endParam = params.get('end');

    const nextRange: DateRange =
      startParam && endParam
        ? { startDate: startParam, endDate: endParam }
        : {
            startDate: seasonRanges[0].startDate,
            endDate: seasonRanges[0].endDate,
          };

    setDateRange((prev) => {
      if (prev && areDateRangesEqual(prev, nextRange)) {
        return prev;
      }
      return nextRange;
    });

    if (!startParam || !endParam) {
      updateSearchParams(nextRange, true);
    }
  }, [location.search, seasonRanges, updateSearchParams]);

  const handleDateRangeChange = useCallback(
    (range: DateRange) => {
      setDateRange((prev) => {
        if (prev && areDateRangesEqual(prev, range)) {
          return prev;
        }
        return range;
      });

      if (!dateRange || !areDateRangesEqual(dateRange, range)) {
        updateSearchParams(range, false);
      }
    },
    [dateRange, updateSearchParams],
  );

  if (loading) {
    return <div>Loading seasons…</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  if (!dateRange) {
    return <div>No season data available.</div>;
  }

  return (
    <AppRoutes
      dateRange={dateRange}
      onDateRangeChange={handleDateRangeChange}
      seasonRanges={seasonRanges}
    />
  );
}
