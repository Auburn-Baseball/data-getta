import { useCallback, useEffect, useMemo, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import MenuItem from '@mui/material/MenuItem';
import Select, { type SelectChangeEvent } from '@mui/material/Select';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs, { type Dayjs } from 'dayjs';

import type { DateRange, SeasonDateRange } from '@/types/dateRange';

type SeasonDateRangeSelectProps = {
  value: DateRange;
  seasonRanges: SeasonDateRange[];
  onDateRangeChange: (range: DateRange) => void;
  disabled?: boolean;
};

const DEFAULT_LABEL = 'Select date range';

export default function SeasonDateRangeSelect({
  value,
  seasonRanges,
  onDateRangeChange,
  disabled = false,
}: SeasonDateRangeSelectProps) {
  const [selectedSeason, setSelectedSeason] = useState<string>('');
  const [isCustomDialogOpen, setCustomDialogOpen] = useState(false);
  const [customRange, setCustomRange] = useState<{ start: Dayjs | null; end: Dayjs | null }>({
    start: null,
    end: null,
  });

  const matchingSeason = useMemo(
    () =>
      seasonRanges.find(
        (season) => season.startDate === value.startDate && season.endDate === value.endDate,
      ) ?? null,
    [seasonRanges, value.endDate, value.startDate],
  );

  useEffect(() => {
    setSelectedSeason(matchingSeason ? String(matchingSeason.year) : 'custom');
  }, [matchingSeason]);

  useEffect(() => {
    setCustomRange({
      start: dayjs(value.startDate),
      end: dayjs(value.endDate),
    });
  }, [value.endDate, value.startDate]);

  const handleOptionChange = useCallback(
    (event: SelectChangeEvent) => {
      const nextValue = event.target.value as string;
      if (nextValue === 'custom') {
        setSelectedSeason('custom');
        setCustomDialogOpen(true);
        return;
      }

      const nextSeason = seasonRanges.find((season) => String(season.year) === nextValue);
      if (!nextSeason) {
        return;
      }

      onDateRangeChange({
        startDate: nextSeason.startDate,
        endDate: nextSeason.endDate,
      });
    },
    [onDateRangeChange, seasonRanges],
  );

  const openCustomDialog = useCallback(() => {
    setCustomDialogOpen(true);
  }, []);

  const handleCustomCancel = useCallback(() => {
    setCustomDialogOpen(false);
    setSelectedSeason(matchingSeason ? String(matchingSeason.year) : 'custom');
  }, [matchingSeason]);

  const handleCustomApply = useCallback(() => {
    if (!customRange.start || !customRange.end) {
      return;
    }

    let start = customRange.start;
    let end = customRange.end;

    if (start.isAfter(end)) {
      [start, end] = [end, start];
    }

    const formattedRange: DateRange = {
      startDate: start.format('YYYY-MM-DD'),
      endDate: end.format('YYYY-MM-DD'),
    };

    setCustomDialogOpen(false);
    onDateRangeChange(formattedRange);
  }, [customRange.end, customRange.start, onDateRangeChange]);

  const renderSelectedValue = useCallback(
    (selected: unknown) => {
      const current = selected as string;

      if (!current) {
        return DEFAULT_LABEL;
      }

      if (current === 'custom') {
        return `Custom: ${dayjs(value.startDate).format('MM/DD/YYYY')} - ${dayjs(
          value.endDate,
        ).format('MM/DD/YYYY')}`;
      }

      const season = seasonRanges.find((option) => String(option.year) === current);
      if (!season) {
        return DEFAULT_LABEL;
      }

      const start = dayjs(season.startDate).format('MM/DD/YYYY');
      const end = dayjs(season.endDate).format('MM/DD/YYYY');
      return `${season.year} Season: ${start} - ${end}`;
    },
    [seasonRanges, value.endDate, value.startDate],
  );

  const isApplyDisabled = !customRange.start || !customRange.end;
  const hasSeasons = seasonRanges.length > 0;

  return (
    <>
      <FormControl
        size="small"
        sx={{ ml: 'auto' }}
        disabled={disabled || !hasSeasons}
        error={!hasSeasons}
      >
        <Select
          value={hasSeasons ? selectedSeason : ''}
          onChange={handleOptionChange}
          displayEmpty
          renderValue={renderSelectedValue}
          inputProps={{ 'aria-label': 'Select date range' }}
        >
          {!hasSeasons && (
            <MenuItem value="" disabled>
              No seasons available
            </MenuItem>
          )}

          {hasSeasons &&
            seasonRanges.map((option) => (
              <MenuItem key={option.year} value={String(option.year)}>
                {option.year} Season
              </MenuItem>
            ))}
          <MenuItem
            value="custom"
            onClick={openCustomDialog} // Add direct click handler to always open dialog
          >
            Custom Range
          </MenuItem>
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
