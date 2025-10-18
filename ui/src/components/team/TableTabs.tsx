import Box from '@mui/material/Box';
import Link from '@/components/ui/Link';
import { useLocation } from 'react-router';
import { useState, useEffect } from 'react';

export default function TableTabs({ trackmanAbbreviation }: { trackmanAbbreviation: string }) {
  const currentURL = '/team/';

  const location = useLocation();

  const [rosterUnderline, setRosterUnderline] = useState<'none' | 'hover' | 'always' | undefined>(
    'hover',
  );
  const [batterUnderline, setBatterUnderline] = useState<'none' | 'hover' | 'always' | undefined>(
    'hover',
  );
  const [pitcherUnderline, setPitcherUnderline] = useState<'none' | 'hover' | 'always' | undefined>(
    'hover',
  );

  useEffect(() => {
    setRosterUnderline('hover');
    setBatterUnderline('hover');
    setPitcherUnderline('hover');

    if (location.pathname.includes('/roster')) {
      setRosterUnderline('always');
    } else if (location.pathname.includes('/batting')) {
      setBatterUnderline('always');
    } else if (location.pathname.includes('/pitching')) {
      setPitcherUnderline('always');
    }
  }, [location.pathname]);

  return (
    <Box
      sx={{
        display: 'flex',
        columnGap: 8,
        rowGap: 2,
        flexWrap: 'wrap',
      }}
    >
      <Link
        href={currentURL.concat(trackmanAbbreviation).concat('/roster')}
        name="Roster"
        fontWeight={600}
        underline={rosterUnderline}
      />
      <Link
        href={currentURL.concat(trackmanAbbreviation).concat('/batting')}
        name="Batting"
        fontWeight={600}
        underline={batterUnderline}
      />
      <Link
        href={currentURL.concat(trackmanAbbreviation).concat('/pitching')}
        name="Pitching"
        fontWeight={600}
        underline={pitcherUnderline}
      />
    </Box>
  );
}
