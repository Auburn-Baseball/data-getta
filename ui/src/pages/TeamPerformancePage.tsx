// src/pages/TeamPerformancePage.tsx
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import Box from '@mui/material/Box';
import TeamPercent, { Row } from '@/components/team/TeamPercent';

const PAGE_SIZE = 1000;

export default function TeamPerformancePage() {
  const [params] = useSearchParams();
  const year = useMemo(() => {
    const y = params.get('year');
    return y === '2024' || y === '2025' ? y : '2025';
  }, [params]);

  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchAll() {
      setLoading(true);
      setErr(null);

      let all: any[] = [];
      let from = 0;

      // get total count first (and first page)
      const first = await supabase
        .from('team_performance')
        .select('team,label,raw_value,percentile', { count: 'exact' })
        .eq('year', Number(year))
        .order('team', { ascending: true })     // <-- order by team first
        .order('label', { ascending: true })    // then label
        .range(from, from + PAGE_SIZE - 1);

      if (first.error) {
        setErr(first.error.message);
        setLoading(false);
        return;
      }

      all = (first.data ?? []);
      const total = first.count ?? all.length;

      // page through remaining rows if needed
      from += PAGE_SIZE;
      while (!cancelled && from < total) {
        const { data, error } = await supabase
          .from('team_performance')
          .select('team,label,raw_value,percentile')
          .eq('year', Number(year))
          .order('team', { ascending: true })
          .order('label', { ascending: true })
          .range(from, from + PAGE_SIZE - 1);

        if (error) {
          setErr(error.message);
          setLoading(false);
          return;
        }
        all = all.concat(data ?? []);
        from += PAGE_SIZE;
      }

      if (cancelled) return;

      // cast numeric strings → numbers
      const casted = all.map((r: any) => ({
        team: r.team,
        label: r.label,
        raw_value: typeof r.raw_value === 'string' ? Number(r.raw_value) : r.raw_value,
        percentile: typeof r.percentile === 'string' ? Number(r.percentile) : r.percentile,
      })) as Row[];

      setRows(casted);
      setLoading(false);

      // Optional sanity logs
      console.log(`Fetched ${casted.length} rows for year ${year}`);
      const byTeam = casted.reduce((m, r) => (m[r.team] = (m[r.team] || 0) + 1, m), {} as Record<string, number>);
      console.log('Rows per team (should be ~9 each):', byTeam);
    }

    fetchAll();
    return () => { cancelled = true; };
  }, [year]);

  return (
    <Box sx={{ bgcolor: '#0b2341', color: 'white', minHeight: '100vh', px: 4, py: 4 }}>
      {loading && <p>Loading team performance…</p>}
      {err && <p style={{ color: 'salmon' }}>{err}</p>}
      {!loading && !err && <TeamPercent year={year} rows={rows} />}
    </Box>
  );
}
