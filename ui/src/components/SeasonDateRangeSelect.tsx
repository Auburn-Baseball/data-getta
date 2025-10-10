import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import MenuItem from '@mui/material/MenuItem';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs, { Dayjs } from 'dayjs';

type SeasonDateRange = {
  year: string;
  startDate: string;
  endDate: string;
};

export type DateRangeSelection = {
  startDate: string; // YYYY-MM-DD
  endDate: string; // YYYY-MM-DD
};

async function fetchSeasonDateRanges(): Promise<SeasonDateRange[]> {
  return [
    { year: '2021', startDate: '2021-03-01', endDate: '2021-10-05' },
    { year: '2022', startDate: '2022-03-02', endDate: '2022-10-06' },
    { year: '2023', startDate: '2023-03-01', endDate: '2023-10-04' },
    { year: '2024', startDate: '2024-03-04', endDate: '2024-10-02' },
    { year: '2025', startDate: '2025-03-03', endDate: '2025-10-01' },
  ];
}

type SeasonDateRangeSelectProps = {
  startDate: string | null;
  endDate: string | null;
  onDateRangeChange: (range: DateRangeSelection) => void;
};

export default function SeasonDateRangeSelect({
  startDate,
  endDate,
  onDateRangeChange,
}: SeasonDateRangeSelectProps) {
  const [seasonOptions, setSeasonOptions] = useState<SeasonDateRange[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<string>('');
  const [appliedSelection, setAppliedSelection] = useState<string>('');
  const [activeRange, setActiveRange] = useState<{ start: Dayjs; end: Dayjs } | null>(null);
  const [customRange, setCustomRange] = useState<{ start: Dayjs | null; end: Dayjs | null }>({
    start: null,
    end: null,
  });
  const [isCustomDialogOpen, setCustomDialogOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadSeasonRanges = async () => {
      const ranges = await fetchSeasonDateRanges();
      if (!isMounted) return;
      const sortedRanges = [...ranges].sort((a, b) => Number(b.year) - Number(a.year));
      setSeasonOptions(sortedRanges);
      if (sortedRanges.length > 0) {
        const initial = sortedRanges[0];
        const initialStart = dayjs(initial.startDate);
        const initialEnd = dayjs(initial.endDate);
        setSelectedSeason(initial.year);
        setAppliedSelection(initial.year);
        setActiveRange({ start: initialStart, end: initialEnd });
        setCustomRange({ start: initialStart, end: initialEnd });
        onDateRangeChange({
          startDate: initialStart.format('YYYY-MM-DD'),
          endDate: initialEnd.format('YYYY-MM-DD'),
        });
      }
    };

    loadSeasonRanges();

    return () => {
      isMounted = false;
    };
  }, [onDateRangeChange]);

  useEffect(() => {
    if (!startDate || !endDate) {
      return;
    }

    const nextStart = dayjs(startDate);
    const nextEnd = dayjs(endDate);

    setActiveRange((prev) => {
      if (prev && prev.start.isSame(nextStart, 'day') && prev.end.isSame(nextEnd, 'day')) {
        return prev;
      }
      return { start: nextStart, end: nextEnd };
    });

    setCustomRange((prev) => {
      if (prev?.start?.isSame(nextStart, 'day') && prev?.end?.isSame(nextEnd, 'day')) {
        return prev;
      }
      return { start: nextStart, end: nextEnd };
    });
  }, [startDate, endDate]);

  const handleOptionChange = (event: SelectChangeEvent) => {
    const value = event.target.value as string;

    if (value === 'custom') {
      setSelectedSeason(value);
      if (activeRange) {
        setCustomRange({ start: activeRange.start, end: activeRange.end });
      }
      setCustomDialogOpen(true);
      return;
    }

    setSelectedSeason(value);
    setAppliedSelection(value);

    const nextRange = seasonOptions.find((option) => option.year === value);
    if (nextRange) {
      const start = dayjs(nextRange.startDate);
      const end = dayjs(nextRange.endDate);
      setActiveRange({ start, end });
      setCustomRange({ start, end });
      onDateRangeChange({
        startDate: start.format('YYYY-MM-DD'),
        endDate: end.format('YYYY-MM-DD'),
      });
    }
  };

  const handleCustomCancel = () => {
    setCustomDialogOpen(false);
    if (activeRange) {
      setCustomRange({ start: activeRange.start, end: activeRange.end });
    }
    setSelectedSeason(appliedSelection);
  };

  const handleCustomApply = () => {
    if (!customRange.start || !customRange.end) return;

    let start = customRange.start;
    let end = customRange.end;

    if (start.isAfter(end)) {
      [start, end] = [end, start];
    }

    setCustomRange({ start, end });
    setActiveRange({ start, end });
    setAppliedSelection('custom');
    setSelectedSeason('custom');
    setCustomDialogOpen(false);
    onDateRangeChange({
      startDate: start.format('YYYY-MM-DD'),
      endDate: end.format('YYYY-MM-DD'),
    });
  };

  const renderSelectedValue = (selected: unknown) => {
    const value = selected as string;

    if (!value) {
      return 'Select date range';
    }

    if (value === 'custom') {
      if (activeRange) {
        return `Custom: ${activeRange.start.format('MM/DD/YYYY')} - ${activeRange.end.format(
          'MM/DD/YYYY',
        )}`;
      }
      return 'Custom Range';
    }

    const season = seasonOptions.find((option) => option.year === value);
    if (season) {
      const start = dayjs(season.startDate).format('MM/DD/YYYY');
      const end = dayjs(season.endDate).format('MM/DD/YYYY');
      return `${season.year} Season: ${start} - ${end}`;
    }

    return value;
  };

  const isApplyDisabled = !customRange.start || !customRange.end;

  return (
    <>
      <FormControl size="small" sx={{ ml: 'auto' }} disabled={seasonOptions.length === 0}>
        <Select
          value={selectedSeason}
          onChange={handleOptionChange}
          displayEmpty
          renderValue={renderSelectedValue}
          inputProps={{ 'aria-label': 'Select date range' }}
        >
          {seasonOptions.length === 0 ? (
            <MenuItem value="" disabled>
              Loading date ranges...
            </MenuItem>
          ) : (
            seasonOptions.map((option) => (
              <MenuItem key={option.year} value={option.year}>
                {option.year} Season
              </MenuItem>
            ))
          )}
          <MenuItem value="custom">Custom Range</MenuItem>
        </Select>
      </FormControl>
      <Dialog open={isCustomDialogOpen} onClose={handleCustomCancel} fullWidth maxWidth="sm">
        <DialogTitle>Select Custom Date Range</DialogTitle>
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <DialogContent sx={{ pt: 2 }}>
            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                gap: 2,
                mt: 2,
              }}
            >
              <DatePicker
                label="Start Date"
                value={customRange.start}
                onChange={(newDate) =>
                  setCustomRange((prev) => ({
                    ...prev,
                    start: newDate,
                  }))
                }
                maxDate={customRange.end ?? undefined}
              />
              <DatePicker
                label="End Date"
                value={customRange.end}
                onChange={(newDate) =>
                  setCustomRange((prev) => ({
                    ...prev,
                    end: newDate,
                  }))
                }
                minDate={customRange.start ?? undefined}
              />
            </Box>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button onClick={handleCustomCancel}>Cancel</Button>
            <Button onClick={handleCustomApply} variant="contained" disabled={isApplyDisabled}>
              Apply
            </Button>
          </DialogActions>
        </LocalizationProvider>
      </Dialog>
    </>
  );
}
