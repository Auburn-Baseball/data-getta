import { useEffect, useState } from 'react';
import { useParams } from 'react-router';

import RosterTable from '@/components/team/RosterTable';
import TableSkeleton from '@/components/team/TableSkeleton';
import { fetchTeamRoster } from '@/services/teamService';
import type { PlayersTable } from '@/types/db';

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
        const { data, error } = await fetchTeamRoster(year, decodedTrackmanAbbreviation);

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
