import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import lineAnimation from '@/assets/LineAnimation.gif';

export default function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <Box
      sx={{ position: 'absolute', inset: 0, width: '100vw', height: '100vh', overflow: 'hidden' }}
    >
      <Box
        component="img"
        src={lineAnimation}
        alt="Animation"
        sx={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          zIndex: -1,
        }}
        fetchPriority="high"
        decoding="async"
      />

      <Box
        sx={{ display: 'flex', px: 4, py: 2, justifyContent: 'space-between', flexWrap: 'wrap' }}
      >
        <Typography variant="h3" sx={{ color: '#e86100', fontWeight: 700, whiteSpace: 'nowrap' }}>
          DATA GETTA
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80%' }}>
        {children}
      </Box>
    </Box>
  );
}
