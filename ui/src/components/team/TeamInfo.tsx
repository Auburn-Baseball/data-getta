import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

export default function TeamInfo({
  name,
  conference,
  seasonLabel,
}: {
  name: string;
  conference: string;
  seasonLabel: string;
}) {
  return (
    <Box sx={{ paddingBottom: 2 }}>
      <Typography variant="h4" fontWeight={700}>
        {name} ({seasonLabel})
      </Typography>
      <Typography variant="h6" fontWeight={600}>
        {conference}
      </Typography>
    </Box>
  );
}
