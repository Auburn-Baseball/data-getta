import { Box, MenuItem, Select, Typography } from '@mui/material';
import { useSearchParams } from 'react-router';

const pitchOptions = ['Fastball', 'Curveball', 'Slider', 'Changeup', 'Sinker'];
const yearOptions = ['2024', '2025'];
const viewOptions = ['Individual', 'Density'];

export default function FilterDropdowns({ player }: { player: string }) {
  const [searchParams, setSearchParams] = useSearchParams();

  const pitch = searchParams.get('pitch') || '';
  const year = searchParams.get('year') || '2024';
  const view = searchParams.get('view') || 'Density';
  const batter = searchParams.get('batter') || 'Both';

  const handleChange = (key: string, value: string) => {
    setSearchParams((current) => {
      const params = new URLSearchParams(current);
      params.set('player', player);
      params.set(key, value);
      return params;
    });
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        px: 4,
        mt: 2,
        mb: 2,
        flexWrap: 'wrap',
        justifyContent: 'center',
      }}
    >
      {/* Year Dropdown */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography fontWeight={600}>Year:</Typography>
        <Select
          size="small"
          value={year}
          onChange={(e) => handleChange('year', e.target.value)}
          sx={{ minWidth: 120 }}
        >
          {yearOptions.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </Select>
      </Box>

      {/* Pitch Type Dropdown */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography fontWeight={600}>Pitch Type:</Typography>
        <Select
          size="small"
          value={pitch}
          onChange={(e) => handleChange('pitch', e.target.value)}
          sx={{ minWidth: 140 }}
          displayEmpty
        >
          <MenuItem value="">All</MenuItem>
          {pitchOptions.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </Select>
      </Box>

      {/* 🆕 View Mode Dropdown */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography fontWeight={600}>View Mode:</Typography>
        <Select
          size="small"
          value={view}
          onChange={(e) => handleChange('view', e.target.value)}
          sx={{ minWidth: 140 }}
        >
          {viewOptions.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </Select>
      </Box>
      {/* Batter Handedness Dropdown */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography fontWeight={600}>Batter Type:</Typography>
        <Select
          size="small"
          value={batter}
          onChange={(e) => handleChange('batter', e.target.value)}
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="Both">Both</MenuItem>
          <MenuItem value="Left">Left</MenuItem>
          <MenuItem value="Right">Right</MenuItem>
          {/* Uncomment if you want to add more options */}
          {/* <MenuItem value="Switch">Switch</MenuItem> */}
          {/* Add more batter types as needed */}
          {/* {batterType.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))} */}
        </Select>
      </Box>
    </Box>
  );
}
