/*
* Creates a heat map based on the percentages it is given.
* 
* author: Braden Mosley
* lastEdit: 04-25-2024
*/

const LIGHT_RED = [255, 0, 0];
const DARK_RED = [82, 1, 1];
const LIGHT_BLUE = [76, 137, 255];
const DARK_BLUE = [0, 0, 128];

// Creates a rgb color between the lightColor and darkColor based on the ratio given
function blendColors(lightColor: number[], darkColor: number[], ratio: number) {    
    let color : string[] = [];

    for (let i in lightColor) {
        color.push(((lightColor[i] * (1 - ratio)) + (darkColor[i] * ratio)).toFixed(0));
    };

    // Format: 'rgb(red, green, blue)'
    return 'rgb('.concat(color + ')');
}

// Determines the colors for each section
function assignColors(percentages: number[]) {
    let colors : string[] = [];
    const minPercent = Math.min(...percentages);
    const maxPercent = Math.max(...percentages);
    const middlePercent = ((maxPercent + minPercent) / 2);
    
    for (let percent in percentages) {
        if (percentages[percent] < middlePercent) {
            colors.push(blendColors(DARK_BLUE, LIGHT_BLUE, percentages[percent]/middlePercent));
        } else {
            colors.push(blendColors(LIGHT_RED, DARK_RED, percentages[percent]/maxPercent));
        }
    }

    return colors;
}

// Calculates the x position of the square based on value's index of the array.
const xCord = (index: number) => (((index % 16) + 1) * 10);

// Calculates the y position of the square based on value's index of the array.
const yCord = (index: number) => ((Math.floor(index / 16) + 1) * 10)

export default function HeatMap({percentages}: {percentages: number[]}) {
    const colors = assignColors(percentages);

    // Creates the heatmap.
    // 16 squares by 20 squares.
    // Each square is 10 pixels.
    let heatmaps : React.ReactNode[] = [];
    colors.map((color, index) => {
        heatmaps.push(<rect key={index} x={xCord(index)} y={yCord(index)} width="10" height="10" fill={color} strokeWidth="0"/>)
    })

    // Adds the strike-zone to the heatmap.
    heatmaps.push(<path key={321} d="M118.5,60.4v62h-57v-62h57M120.5,58.4h-61v66h61V58.4h0Z" fill="#fff" strokeWidth="0"/>)
    
    return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
            {heatmaps}
        </svg>
    );
}