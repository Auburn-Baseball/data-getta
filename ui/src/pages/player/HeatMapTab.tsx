import Box from '@mui/material/Box';
import { prisma } from '@/utils/db';
import HeatMap from '@/player/components/HeatMap/HeatMap';

type Params = Promise<{ teamName: string; playerName: string }>;
type SearchParams = Promise<{ year?: string; pitch?: string; batter?: string }>;

export default async function Page(props: {
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}) {
  const params = await props.params;
  const searchParams = await props.searchParams;

  const decodedPlayerName = decodeURIComponent(params.playerName);
  const year = searchParams.year === '2025' ? '2025' : '2024'; // fallback to 2024
  const pitchType = searchParams.pitch || '';
  const batter = searchParams.batter || 'Both'; // default to both

  // Use year-specific table
  const pTableName = `trackman_pitcher_${year}`;
  const bTableName = `trackman_batter_${year}`;

  let query = `
  SELECT 
    tp."PlateLocSide" AS x,
    tp."PlateLocHeight" AS y,
    tb."BatterSide" AS "batterSide",
    COALESCE(tp."TaggedPitchType", tp."AutoPitchType") AS "pitchType",
    tp."AutoPitchType"
  FROM trackman_pitcher tp
  LEFT JOIN trackman_metadata tm
    ON tp."PitchUID" = tm."PitchUID"
  LEFT JOIN  trackman_batter tb
    ON tp."PitchUID" = tb."PitchUID"
  WHERE tp."Pitcher" = $1
    AND tm."UTCDate" IS NOT NULL
    AND tm."UTCDate" BETWEEN '${year}-01-01' AND '${year}-12-31'
    ${pitchType ? `AND COALESCE(tp."TaggedPitchType", tp."AutoPitchType") = $2` : ''}
    ${batter !== 'Both' ? `AND tb."BatterSide" = $${pitchType ? 3 : 2}` : ''}
  `;

  const args = [decodedPlayerName];

  if (pitchType) args.push(pitchType);
  if (batter !== 'Both') args.push(batter);

  const raw = (await prisma.$queryRawUnsafe(query, ...args)) as any[];

  const pitches = raw.map((p) => ({
    x: Number(p.x),
    y: Number(p.y),
    pitchType: p.pitchType, // TaggedPitchType
    batterSide: p.batterSide,
  }));
  console.log('Passing to HeatMap:', pitches.length, 'pitches');

  return (
    <Box
      sx={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        padding: '2rem 0',
        minHeight: '100vh',
      }}
    >
      <HeatMap playerName={decodedPlayerName} batterFilter={batter} pitches={pitches} />
    </Box>
  );
}
