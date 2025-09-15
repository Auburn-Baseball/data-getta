import Box from '@mui/material/Box';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router';

export default function DateSelector({ start, end }: { start: string; end: string }) {
  const navigate = useNavigate();
  const location = useLocation();
  const currentURL = location.pathname;

  const [startDate, setStartDate] = useState<Dayjs | null>(dayjs(start));
  const [endDate, setEndDate] = useState<Dayjs | null>(dayjs(end));

  const handleStartDate = (date: Dayjs | null) => {
    if (startDate !== null && date !== null) {
      const newURL = currentURL.replace(
        'stats/' + startDate.format('YYYY-MM-DD'),
        'stats/' + date.format('YYYY-MM-DD'),
      );
      setStartDate(date);
      navigate(newURL, { replace: true });
    }
  };

  const handleEndDate = (date: Dayjs | null) => {
    if (endDate !== null && date !== null) {
      const oldURL = currentURL.substring(0, currentURL.length - 10);
      const newURL = oldURL.concat(date.format('YYYY-MM-DD'));
      setEndDate(date);
      navigate(newURL, { replace: true });
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Box sx={{ display: 'inline-block', paddingRight: 2, paddingY: 1 }}>
          <DatePicker
            label="Start Date"
            value={startDate}
            onChange={(newStartDate) => handleStartDate(newStartDate)}
          />
        </Box>

        <Box sx={{ display: 'inline-block', paddingY: 1 }}>
          <DatePicker
            label="End Date"
            value={endDate}
            onChange={(newEndDate) => handleEndDate(newEndDate)}
          />
        </Box>
      </Box>
    </LocalizationProvider>
  );
}
