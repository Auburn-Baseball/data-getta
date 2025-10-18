import { useState, useEffect } from 'react';
import { useParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import RosterTable from '@/components/team/RosterTable';
import { PlayersTable } from '@/types/schemas';
import TableSkeleton from '@/components/team/TableSkeleton';

type RosterTabProps = {
  year: number;
};

export default function RosterTab({ year }: RosterTabProps) {
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const [players, setPlayers] = useState<PlayersTable[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRoster() {
      if (!trackmanAbbreviation) return;

      try {
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
        console.log(decodedTrackmanAbbreviation);
        const { data, error } = await cachedQuery({
          key: createCacheKey('Players', {
            select: '*',
            eq: {
              Year: year,
              TeamTrackmanAbbreviation: decodedTrackmanAbbreviation,
            },
            order: [{ column: 'Name', ascending: true }],
          }),
          query: () =>
            supabase
              .from('Players')
              .select('*')
              .eq('Year', year)
              .eq('TeamTrackmanAbbreviation', decodedTrackmanAbbreviation)
              .order('Name', { ascending: true })
              .overrideTypes<PlayersTable[], { merge: false }>(),
        });

        if (error) throw error;
        setPlayers(data || []);
      } catch (error) {
        console.error('Error fetching roster:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchRoster();
  }, [trackmanAbbreviation, year]);

  if (loading) return <TableSkeleton />;
  return <RosterTable players={players} />;
}
