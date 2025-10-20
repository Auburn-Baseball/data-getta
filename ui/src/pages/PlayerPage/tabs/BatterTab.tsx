import { Suspense } from 'react';
import CreateStatsDiagrams from '@/components/player/CreateStatsDiagrams';
import StatsTableSkeleton from '@/components/player/StatsTableSkeleton';

export default async function Page(props: {
  params: Promise<{
    teamName: string;
    playerName: string;
  }>;
}) {
  const params = await props.params;
  const decodedTeamName = decodeURIComponent(params.teamName);
  const decodedPlayerName = decodeURIComponent(params.playerName);

  const startDate = '2024-02-16';
  const endDate = new Date().toISOString().split('T')[0];

  return (
    <Suspense fallback={<StatsTableSkeleton />}>
      <CreateStatsDiagrams
        player={decodedPlayerName}
        team={decodedTeamName}
        startDate={startDate}
        endDate={endDate}
      />
    </Suspense>
  );
}
