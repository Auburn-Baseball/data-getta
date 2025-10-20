import dayjs from 'dayjs';

import type { DateRange, SeasonDateRange } from '@/types/dateRange';

export const sortSeasonRangesDesc = (ranges: SeasonDateRange[]): SeasonDateRange[] =>
  [...ranges].sort((a, b) => {
    const aDate = dayjs(a.startDate);
    const bDate = dayjs(b.startDate);

    if (aDate.isSame(bDate, 'day')) {
      return b.year - a.year;
    }

    return bDate.diff(aDate);
  });

export const getYearRange = (range: DateRange): { startYear: number; endYear: number } => {
  const startYear = dayjs(range.startDate).year();
  const endYear = dayjs(range.endDate).year();

  return { startYear, endYear };
};

export const formatYearRange = (range: DateRange): string => {
  const { startYear, endYear } = getYearRange(range);
  return startYear === endYear ? `${startYear}` : `${startYear}-${endYear}`;
};

export const areDateRangesEqual = (a: DateRange, b: DateRange): boolean =>
  a.startDate === b.startDate && a.endDate === b.endDate;
