import { useCallback, useState } from 'react';
import { BrowserRouter } from 'react-router';

import { DateRangeSelection } from '@/components/SeasonDateRangeSelect';
import AppRoutes, { type DateRangeState } from '@/router/routes';

const basename = import.meta.env.BASE_URL.replace(/\/$/, '');

export default function App() {
  const [dateRange, setDateRange] = useState<DateRangeState>({
    startDate: '',
    endDate: '',
  });

  const year = dateRange.startDate
    ? new Date(dateRange.startDate).getFullYear()
    : new Date().getFullYear();

  const handleDateRangeChange = useCallback((range: DateRangeSelection) => {
    setDateRange({ startDate: range.startDate, endDate: range.endDate });
  }, []);

  return (
    <BrowserRouter basename={basename}>
      <AppRoutes dateRange={dateRange} onDateRangeChange={handleDateRangeChange} year={year} />
    </BrowserRouter>
  );
}
