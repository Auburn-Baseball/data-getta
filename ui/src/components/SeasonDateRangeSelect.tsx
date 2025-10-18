import { useEffect, useState, useCallback } from 'react';
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
import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import { SeasonDatesTable } from '@/types/schemas';

type SeasonDateRange = {
  year: string;
  startDate: string;
  endDate: string;
};

export type DateRangeSelection = {
  startDate: string; // YYYY-MM-DD
  endDate: string; // YYYY-MM-DD
};

async function fetchSeasonDateRanges(): Promise<{
  ranges: SeasonDateRange[];
  errorMessage?: string;
}> {
  const descriptor = {
    select: ['year', 'season_start', 'season_end'],
    order: [{ column: 'year', ascending: false }],
  } as const;

  try {
    const { data, error } = await cachedQuery({
      key: createCacheKey('SeasonDates', descriptor),
      query: () => {
        console.debug('[SeasonDateRangeSelect] fetching SeasonDates from Supabase', {
          descriptor,
        });

        return supabase
          .from('SeasonDates')
          .select('year, season_start, season_end')
          .order('year', { ascending: false })
          .returns<SeasonDatesTable[]>();
      },
    });

    if (error) {
      const message = error.message ?? 'Unknown error loading season dates';
      console.error('Failed to load season date ranges:', error);
      return { ranges: [], errorMessage: message };
    }

    const rows = Array.isArray(data) ? data : [];

    const ranges = rows
      .filter((row) => row.season_start && row.season_end)
      .map((row) => ({
        year: String(row.year),
        startDate: row.season_start as string,
        endDate: row.season_end as string,
      }));

    console.debug('SeasonDates query result', { rowCount: rows.length, ranges });

    if (ranges.length === 0) {
      return { ranges: [], errorMessage: 'No season dates available.' };
    }

    return { ranges };
  } catch (err) {
    console.error('Exception fetching season dates:', err);
    return { ranges: [], errorMessage: 'Failed to load season dates.' };
  }
}

type SeasonDateRangeSelectProps = {
  startDate: string;
  endDate: string;
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
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Load season ranges on component mount
  useEffect(() => {
    let isMounted = true;

    const loadSeasonRanges = async () => {
      setIsLoading(true);
      setLoadError(null);

      const { ranges, errorMessage } = await fetchSeasonDateRanges();
      if (!isMounted) return;

      if (ranges.length === 0) {
        setSeasonOptions([]);
        setSelectedSeason('');
        setAppliedSelection('');
        setActiveRange(null);
        setCustomRange({ start: null, end: null });
        setIsLoading(false);
        if (errorMessage) {
          setLoadError(errorMessage);
        }
        return;
      }

      // Set available season options
      setSeasonOptions(ranges);
      setIsLoading(false);

      // Handle initial date selection
      const hasInitialSelection = Boolean(startDate && endDate);

      if (hasInitialSelection) {
        const nextStart = dayjs(startDate);
        const nextEnd = dayjs(endDate);
        const matchedSeason = ranges.find(
          (option) => option.startDate === startDate && option.endDate === endDate,
        );

        if (matchedSeason) {
          // If the dates match a season, select that season
          setSelectedSeason(matchedSeason.year);
          setAppliedSelection(matchedSeason.year);
        } else {
          // Otherwise it's a custom selection
          setSelectedSeason('custom');
          setAppliedSelection('custom');
        }

        setActiveRange({ start: nextStart, end: nextEnd });
        setCustomRange({ start: nextStart, end: nextEnd });
      } else {
        // No initial selection, use the most recent season
        const initial = ranges[0];
        const initialStart = dayjs(initial.startDate);
        const initialEnd = dayjs(initial.endDate);

        setSelectedSeason(initial.year);
        setAppliedSelection(initial.year);
        setActiveRange({ start: initialStart, end: initialEnd });
        setCustomRange({ start: initialStart, end: initialEnd });

        // Notify parent of the default selection
        onDateRangeChange({
          startDate: initial.startDate,
          endDate: initial.endDate,
        });
      }

      // Set error if there was one during loading
      if (errorMessage) {
        setLoadError(errorMessage);
      }
    };

    loadSeasonRanges();

    return () => {
      isMounted = false;
    };
  }, []); // Dependency array intentionally empty - only run on mount

  // Update component state when props change (e.g., from parent)
  useEffect(() => {
    if (!startDate || !endDate || seasonOptions.length === 0) return;

    const nextStart = dayjs(startDate);
    const nextEnd = dayjs(endDate);

    // Update active range if it changed
    setActiveRange((prev) => {
      if (prev && prev.start.isSame(nextStart, 'day') && prev.end.isSame(nextEnd, 'day')) {
        return prev;
      }
      return { start: nextStart, end: nextEnd };
    });

    // Update custom range state
    setCustomRange((prev) => {
      if (prev?.start?.isSame(nextStart, 'day') && prev?.end?.isSame(nextEnd, 'day')) {
        return prev;
      }
      return { start: nextStart, end: nextEnd };
    });

    // Determine if these dates match a season or are custom
    const matchingSeason = seasonOptions.find(
      (option) => option.startDate === startDate && option.endDate === endDate,
    );

    if (matchingSeason) {
      setSelectedSeason(matchingSeason.year);
      setAppliedSelection(matchingSeason.year);
    } else {
      setSelectedSeason('custom');
      setAppliedSelection('custom');
    }
  }, [startDate, endDate, seasonOptions]);

  // Handle dropdown selection change
  const handleOptionChange = useCallback(
    (event: SelectChangeEvent) => {
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
          startDate: nextRange.startDate,
          endDate: nextRange.endDate,
        });
      }
    },
    [activeRange, onDateRangeChange, seasonOptions],
  );

  // Handle custom dialog cancel
  const handleCustomCancel = useCallback(() => {
    setCustomDialogOpen(false);
    if (activeRange) {
      setCustomRange({ start: activeRange.start, end: activeRange.end });
    }
    setSelectedSeason(appliedSelection);
  }, [activeRange, appliedSelection]);

  // Handle custom dialog apply button
  const handleCustomApply = useCallback(() => {
    if (!customRange.start || !customRange.end) return;

    let start = customRange.start;
    let end = customRange.end;

    // Ensure start is before end
    if (start.isAfter(end)) {
      [start, end] = [end, start];
    }

    const formattedStart = start.format('YYYY-MM-DD');
    const formattedEnd = end.format('YYYY-MM-DD');

    setCustomRange({ start, end });
    setActiveRange({ start, end });
    setAppliedSelection('custom');
    setSelectedSeason('custom');
    setCustomDialogOpen(false);

    onDateRangeChange({
      startDate: formattedStart,
      endDate: formattedEnd,
    });
  }, [customRange.start, customRange.end, onDateRangeChange]);

  // Format the displayed value in the select dropdown
  const renderSelectedValue = useCallback(
    (selected: unknown) => {
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
    },
    [activeRange, seasonOptions],
  );

  const isApplyDisabled = !customRange.start || !customRange.end;

  return (
    <>
      <FormControl
        size="small"
        sx={{ ml: 'auto' }}
        disabled={seasonOptions.length === 0 || isLoading}
        error={Boolean(loadError)}
      >
        <Select
          value={selectedSeason}
          onChange={handleOptionChange}
          displayEmpty
          renderValue={renderSelectedValue}
          inputProps={{ 'aria-label': 'Select date range' }}
        >
          {isLoading && (
            <MenuItem value="" disabled>
              Loading date ranges...
            </MenuItem>
          )}
          {!isLoading &&
            seasonOptions.map((option) => (
              <MenuItem key={option.year} value={option.year}>
                {option.year} Season
              </MenuItem>
            ))}
          <MenuItem value="custom">Custom Range</MenuItem>
        </Select>
      </FormControl>
      {loadError && (
        <Box sx={{ ml: 2, color: 'error.main', fontSize: 12, alignSelf: 'center' }}>
          {loadError}
        </Box>
      )}
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
