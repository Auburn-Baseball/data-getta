import { useState, useEffect } from 'react';
import { useParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import BatterTable from '@/components/team/BatterTable';
import { BatterStatsTable } from '@/types/schemas';
import TableSkeleton from '@/components/team/TableSkeleton';

export default function BattingTab() {
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const [batters, setBatters] = useState<BatterStatsTable[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchBatters() {
      if (!trackmanAbbreviation) return;

      try {
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);

        const { data, error } = await supabase
          .from('BatterStats')
          .select('*')
          .eq('BatterTeam', decodedTrackmanAbbreviation)
          .overrideTypes<BatterStatsTable[], { merge: false }>();

        if (error) throw error;
        setBatters(data || []);
      } catch (error) {
        console.error('Error fetching batters:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchBatters();
  }, [trackmanAbbreviation]);

  if (loading) return <TableSkeleton />;
  return <BatterTable players={batters} />;
}
