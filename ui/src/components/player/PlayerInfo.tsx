import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

export default function PlayerInfo({ name, team }: { name: string; team: string }) {
  console.log(name);
  const playerName = name.split(", ");

  return (
    <Box>
      <Typography variant="h4" fontWeight={700}>
        {playerName[1] + ' ' + playerName[0]}
      </Typography>
      <Typography variant="h6" fontWeight={600}>
        {team}
      </Typography>
    </Box>
  );
}
