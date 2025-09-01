/*
* Creates the bar chart to display certain pitcher stats.
* 
* author: Braden Mosley
* lastEdit: 04-22-2024
*/

'use client'

import { BarChart } from "@mui/x-charts/BarChart";
import { pitch_sums_forTable } from "@/app/utils/types";
import { Theme } from "@/app/utils/theme";

// Format of the object to pass to the MUI BarChart component.
type barChart = {
    stat: string;
    value: number;
}

// Manipulates the given data to a format to work with the MUI BarChart component.
function manipulateData (param : pitch_sums_forTable[]) {
    let result : barChart[] = [];
    result.push({ stat: 'Total', value: param[0].total_pitches });
    result.push({ stat: '4 Seam', value: param[0].fourseam_count });
    result.push({ stat: '2 Seam', value: param[0].twoseam_count });
    result.push({ stat: 'Curve', value: param[0].curveball_count });
    result.push({ stat: 'Sinker', value: param[0].sinker_count });
    result.push({ stat: 'Slider', value: param[0].slider_count });
    result.push({ stat: 'Changeup', value: param[0].changeup_count });
    result.push({ stat: 'Cutter', value: param[0].cutter_count });
    result.push({ stat: 'Splitter', value: param[0].splitter_count });
    result.push({ stat: 'Other', value: param[0].other_count });
    return result;
}

export default function PitchSumsBarChart({player}: {player: pitch_sums_forTable[]}) {
    return (
        <BarChart 
            layout = 'horizontal'
            dataset = { manipulateData(player) }
            series = {[ { dataKey: 'value', color: Theme.palette.secondary.main } ]}
            yAxis = {[ { scaleType: 'band', dataKey: 'stat' } ]}
            height = { 500 }
            grid = {{ vertical: true }}
            margin = {{ left: 100 }}
        />
    );
}