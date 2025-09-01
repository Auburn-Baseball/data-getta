/*
* Dummy page to redirect to the stats page
* since the startDate and endDate are required to query the database.
* 
* A redirect is used to make it easier to route to a player's page from other parts of the app,
* then from here the dynamic routes will be filled out to query the database and populate the stats tables.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import dayjs from 'dayjs';
import { permanentRedirect } from 'next/navigation';

export default function Page (
    { params }:
    { params: { teamName: string, playerName: string } })
{
    const decodedTeamName = decodeURIComponent(params.teamName);
    const decodedPlayerName = decodeURIComponent(params.playerName);
    
    // Will have to change to the start of the current season
    const startOfSeason = '2024-02-16';
    
    const currentDate = dayjs().format('YYYY-MM-DD');

    const baseURL = '/the-eye/player/'
    
    permanentRedirect(baseURL.concat(decodedTeamName + '/' + decodedPlayerName + '/' + 'stats' + '/' + startOfSeason + '/' + currentDate))
}