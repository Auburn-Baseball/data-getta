// src/pages/TeamPerformancePage.tsx
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import Box from '@mui/material/Box';
import TeamPercent, { Row } from '@/components/team/TeamPercent';

const PAGE_SIZE = 1000;

type TeamPerformancePageProps = {
  startDate: string | null;
  endDate: string | null;
};

export default function TeamPerformancePage({ startDate, endDate }: TeamPerformancePageProps) {
  const [params] = useSearchParams();

  const year = useMemo(() => {
    const y = params.get('year');
    return y === '2024' || y === '2025' ? y : '2025';
  }, [params]);

  const mode = useMemo<'overall' | 'wl'>(() => {
    const m = (params.get('mode') || 'overall').toLowerCase();
    return m === 'wl' ? 'wl' : 'overall';
  }, [params]);

  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchAll() {
      setLoading(true);
      setErr(null);

      // We still fetch the base data (so switching back to Overall is instant).
      let all: any[] = [];
      let from = 0;

      const first = await cachedQuery({
        key: createCacheKey('team_performance', {
          select: ['team', 'label', 'raw_value', 'percentile'],
          count: 'exact',
          eq: { year: Number(year) },
          order: [
            { column: 'team', ascending: true },
            { column: 'label', ascending: true },
          ],
          range: [from, from + PAGE_SIZE - 1],
          filterRange: { startDate, endDate },
        }),
        query: () =>
          supabase
            .from('team_performance')
            .select('team,label,raw_value,percentile', { count: 'exact' })
            .eq('year', Number(year))
            .order('team', { ascending: true })
            .order('label', { ascending: true })
            .range(from, from + PAGE_SIZE - 1),
      });

      if (first.error) {
        setErr(first.error.message);
        setLoading(false);
        return;
      }

      all = first.data ?? [];
      const total = first.count ?? all.length;

      from += PAGE_SIZE;
      while (!cancelled && from < total) {
        const { data, error } = await cachedQuery({
          key: createCacheKey('team_performance', {
            select: ['team', 'label', 'raw_value', 'percentile'],
            eq: { year: Number(year) },
            order: [
              { column: 'team', ascending: true },
              { column: 'label', ascending: true },
            ],
            range: [from, from + PAGE_SIZE - 1],
            filterRange: { startDate, endDate },
          }),
          query: () =>
            supabase
              .from('team_performance')
              .select('team,label,raw_value,percentile')
              .eq('year', Number(year))
              .order('team', { ascending: true })
              .order('label', { ascending: true })
              .range(from, from + PAGE_SIZE - 1),
        });

        if (error) {
          setErr(error.message);
          setLoading(false);
          return;
        }
        all = all.concat(data ?? []);
        from += PAGE_SIZE;
      }

      if (cancelled) return;

      const casted = all.map((r: any) => ({
        team: r.team,
        label: r.label,
        raw_value: typeof r.raw_value === 'string' ? Number(r.raw_value) : r.raw_value,
        percentile: typeof r.percentile === 'string' ? Number(r.percentile) : r.percentile,
      })) as Row[];

      setRows(casted);
      setLoading(false);
    }

    fetchAll();
    return () => {
      cancelled = true;
    };
  }, [year, startDate, endDate]);

  // If mode is W/L (no data yet), pass empty rows to show the empty state
  const rowsToShow = mode === 'wl' ? [] : rows;

  return (
    <Box sx={{ bgcolor: 'white', color: 'white', minHeight: '100vh', px: 4, py: 4 }}>
      {loading && <p>Loading team performance…</p>}
      {err && <p style={{ color: 'salmon' }}>{err}</p>}
      {!loading && !err && <TeamPercent year={year} rows={rowsToShow} mode={mode} />}
    </Box>
  );
}
