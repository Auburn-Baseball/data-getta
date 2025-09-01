/*
* Tabs to switch between which model shows for a player.
* 
* author: Braden Mosley
* lastEdit: 04-23-2024
*/

'use client'

import Box from "@mui/material/Box";
import Link from "@/app/utils/Link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

export default function ModelTabs ({team, player}: {team: string, player: string}) {
    const currentURL = '/the-eye/player/';
    
    const pathName = usePathname();

    const [statsUnderline, setStatsUnderline] = useState<'none' | 'hover' | 'always' | undefined>('hover');
    const [model1Underline, setModel1Underline] = useState<'none' | 'hover' | 'always' | undefined>('hover');
    const [model2Underline, setModel2Underline] = useState<'none' | 'hover' | 'always' | undefined>('hover');
    const [model3Underline, setModel3Underline] = useState<'none' | 'hover' | 'always' | undefined>('hover');
    
    useEffect(() => {
        setStatsUnderline('hover');
        setModel1Underline('hover');
        setModel2Underline('hover');
        setModel3Underline('hover');

        if (pathName.includes('/stats')) {
            setStatsUnderline('always');
        } else if (pathName.includes('/shiftModel')) {
            setModel1Underline('always');
        } else if (pathName.includes('/heatMap')) {
            setModel2Underline('always');
        } else if (pathName.includes('/runValue')) {
            setModel3Underline('always');
        }
    }, [pathName])
    
    return (
        <Box
            sx={{
                display: 'flex',
                columnGap: 8, rowGap: 2,
                flexWrap: 'wrap',
            }}
        >
            <Link 
                href = {currentURL.concat(team + '/' + player).concat('/stats')}
                name = 'Stats'
                fontWeight = {600}
                underline = {statsUnderline}
            />
            <Link 
                href = {currentURL.concat(team + '/' + player).concat('/shiftModel')}
                name = 'Defensive Shift'
                fontWeight = {600}
                underline = {model1Underline}
            />
            <Link 
                href = {currentURL.concat(team + '/' + player).concat('/heatMap')}
                name = 'Heat Maps'
                fontWeight = {600}
                underline = {model2Underline}
            />
            <Link 
                href = {currentURL.concat(team + '/' + player).concat('/runValue/AUB_TIG')}
                name = 'Run Values'
                fontWeight = {600}
                underline = {model3Underline}
            />
        </Box>
    )
}