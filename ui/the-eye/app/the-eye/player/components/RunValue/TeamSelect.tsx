/*
* Drop-down to select a team.
* The selected team replaces the current team in the url.
* 
* author: Braden Mosley
* lastEdit: 04-24-2024
*/

'use client'

import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

type teamInfo = {
    TeamName: string;
    DisplayName: string | null;
}

export default function TeamSelect({ team, allTeams }: { team: teamInfo, allTeams: teamInfo[] }) {
    const router = useRouter();
    const currentURL = usePathname();
    
    const [selectedTeam, setSelectedTeam] = useState<teamInfo>(team);

    const handleSelectedTeam = (team: teamInfo | null) => {
        if (team !== null) {
            const newURL = currentURL.replace('runValue/' + selectedTeam.TeamName, 'runValue/' + team.TeamName);
            setSelectedTeam(team);
            router.replace(newURL);
        }
    };

    return (
        <Autocomplete
            sx={{ width: 300 }}
            
            options={allTeams}
            getOptionLabel={(option) => (option.DisplayName === null || option.DisplayName === 'NotSet') ? option.TeamName : option.DisplayName}
            
            value = {selectedTeam}
            onChange = {(event: any, newValue: teamInfo | null) => {
                handleSelectedTeam(newValue);
            }}

            isOptionEqualToValue={(option, value) => option.TeamName === value.TeamName }

            renderInput={(params) => (
                <TextField
                    {...params}
                    label="Choose a team"
                    inputProps={{
                        ...params.inputProps,
                        autoComplete: 'new-password', // disable autocomplete and autofill
                    }}
                />
            )}
        />
    );
}