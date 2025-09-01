/*
* Creates the date pickers for the startDate and endDate
* used for querying player stats between the two dates.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

'use client'

import Box from '@mui/material/Box';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';
import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export default function DateSelector({start, end}: {start: string, end: string}) {
    const router = useRouter();
    const currentURL = usePathname();
    
    const [startDate, setStartDate] = useState<Dayjs | null>(dayjs(start));
    const [endDate, setEndDate] = useState<Dayjs | null>(dayjs(end));

    const handleStartDate = (date: Dayjs | null) => {
        if (startDate !== null && date !== null) {
            const newURL = currentURL.replace('stats/' + startDate.format('YYYY-MM-DD'), 'stats/' + date.format('YYYY-MM-DD'));
            setStartDate(date);
            router.replace(newURL);
        };
    };

    const handleEndDate = (date: Dayjs | null) => {
        if (endDate !== null && date !== null) {
            const oldURL = currentURL.substring(0, currentURL.length - 10);
            const newURL = oldURL.concat(date.format('YYYY-MM-DD'));
            setEndDate(date);
            router.replace(newURL);
        };
    };
    
    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Box>
                <Box sx={{display: 'inline-block', paddingRight: 2, paddingY: 1}}>
                    <DatePicker 
                        label = 'Start Date'
                        value = {startDate}
                        onChange={(newStartDate) => handleStartDate(newStartDate)}
                    />
                </Box>

                <Box sx={{display: 'inline-block', paddingY: 1}}>
                    <DatePicker 
                        label = 'End Date'
                        value = {endDate}
                        onChange={(newEndDate) => handleEndDate(newEndDate)}
                    />
                </Box>
            </Box>
        </LocalizationProvider>
    );
}