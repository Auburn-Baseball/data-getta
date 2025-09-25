// src/pages/TeamPerformancePage.tsx
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import Box from '@mui/material/Box';
import TeamPercent, { Row } from '@/components/team/TeamPercent';

export default function TeamPerformancePage() {
  const [params] = useSearchParams();
  const year = useMemo(() => {
    const y = params.get('year');
    return y === '2024' || y === '2025' ? y : '2025'; // default+validate
  }, [params]);

  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setLoading(true);
      setErr(null);

      const { data, error } = await supabase
        .from('team_performance')
        .select('*')
        .eq('year', 2025)
        .order('label', { ascending: true })
        .order('percentile', { ascending: false });
        // .returns<Row[]>() // (optional if you have typed client)

      if (cancelled) return;

      if (error) {
        setErr(error.message);
      } else {
        // Coerce NUMERIC -> number if Supabase returns strings
        const casted = (data ?? []).map((r: any) => ({
          team: r.team,
          label: r.label,
          raw_value: typeof r.raw_value === 'string' ? Number(r.raw_value) : r.raw_value,
          percentile: typeof r.percentile === 'string' ? Number(r.percentile) : r.percentile,
        })) as Row[];
        setRows(casted);
      }
      setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [year]);

  return (
    <Box sx={{ bgcolor: '#0b2341', color: 'white', minHeight: '100vh', px: 4, py: 4 }}>
      {loading && <p>Loading team performance…</p>}
      {err && <p style={{ color: 'salmon' }}>{err}</p>}
      {!loading && !err && <TeamPercent year={year} rows={rows} />}
    </Box>
  );
}
