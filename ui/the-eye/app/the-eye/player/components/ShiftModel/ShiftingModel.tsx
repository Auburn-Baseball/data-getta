/*
* Creates the defensive shifting model svg based on the percentages it is given.
* 
* author: Braden Mosley
* lastEdit: 04-16-2024
*/

// Auburn Branding Color Codes in rgb format
const NAVY_DARK    = [11, 35, 65];
const NAVY_LIGHT   = [109, 123, 141];
const ORANGE_DARK  = [204, 78, 11];
const ORANGE_LIGHT = [248, 173, 118];

// Creates a rgb color between the lightColor and darkColor based on the ratio given
function blendColors(lightColor: number[], darkColor: number[], ratio: number) {    
    let color : string[] = [];

    for (let i in lightColor) {
        color.push(((lightColor[i] * (1 - ratio)) + (darkColor[i] * ratio)).toFixed(0));
    };

    // Format: 'rgb(red, green, blue)'
    return 'rgb('.concat(color + ')');
}

// Determines the colors for each infield section
function createInfieldColors(percentages: number[]) {
    let colors : string[] = [];
    const maxPercent = Math.max(...percentages);
    
    for (let percent in percentages) {
        colors.push(blendColors(ORANGE_LIGHT, ORANGE_DARK, percentages[percent]/maxPercent));
    }

    return colors;
}

// Determines the colors for each outfield section
function createOutfieldColors(percentages: number[]) {
    let colors : string[] = [];
    const maxPercent = Math.max(...percentages);
    
    for (let percent in percentages) {
        colors.push(blendColors(NAVY_LIGHT, NAVY_DARK, percentages[percent]/maxPercent));
    }

    return colors;
}

const decimalToPercent = (decimal: number) => (decimal * 100).toFixed(0).concat('%');

export default function ShiftingModel({percentages}: {percentages: number[]}) {
    const infieldPercentages = percentages.slice(0, 5);
    const outfieldPercentages = percentages.slice(5, 20);
    const infield = createInfieldColors(infieldPercentages);
    const outfield = createOutfieldColors(outfieldPercentages);

    return(
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 170">
            <path d="M195,69.33C179.23,31.48,142.56,6.43,101.9,5.68,59.89,4.91,21.31,30.21,5,69.33c0,0,95,95,95,95l95-95Z" fill="none" stroke="#0b2341" strokeMiterlimit="10" strokeWidth="4"/>
            
            <g>
                <path d="M54,118l46,46-33-64c-2.18,2.1-4.61,4.75-7,8-2.65,3.61-4.59,7.06-6,10Z" fill={infield[0]} strokeWidth="0"/>
                <text transform="translate(57.99 121.52)" fill="#FFF" fontSize="8" fontWeight="700"><tspan x="0" y="0">{decimalToPercent(percentages[0])}</tspan></text>
                <path d="M67,100l33,64-12-75c-2.94.66-6.8,1.83-11,4-4.41,2.28-7.72,4.9-10,7Z" fill={infield[1]} strokeWidth="0"/>
                <text transform="translate(72.99 108.52)" fill="#FFF" fontSize="8" fontWeight="700"><tspan x="0" y="0">{decimalToPercent(percentages[1])}</tspan></text>
                <path d="M88,89l12,75,12-75c-4.51-.76-8.58-1-12-1-4.58,0-8.62.43-12,1Z" fill={infield[2]} strokeWidth="0"/>
                <text transform="translate(91.99 100.52)" fill="#FFF" fontSize="8" fontWeight="700"><tspan x="0" y="0">{decimalToPercent(percentages[2])}</tspan></text>
                <path d="M112,89l-12,75,32-64c-1.89-2-4.84-4.69-9-7-4.29-2.38-8.25-3.47-11-4Z" fill={infield[3]} strokeWidth="0"/>
                <text transform="translate(110.99 108.52)" fill="#FFF" fontSize="8" fontWeight="700"><tspan x="0" y="0">{decimalToPercent(percentages[3])}</tspan></text>
                <path d="M132,100l-32,64,46-46c-.57-1.3-1.23-2.64-2-4-3.57-6.35-8.1-10.88-12-14Z" fill={infield[4]} strokeWidth="0"/>
                <text transform="translate(125.99 121.52)" fill="#FFF" fontSize="8" fontWeight="700"><tspan x="0" y="0">{decimalToPercent(percentages[4])}</tspan></text>
            </g>
            
            <g>
                <path d="M56,77c-2.82,2.65-5.93,5.96-9,10-4.12,5.43-6.99,10.65-9,15l16,16c1.76-3.34,4.04-7.1,7-11,2.03-2.67,4.06-4.99,6-7l-11-23Z" fill={outfield[0]} strokeWidth="0"/>
                <path d="M84,62c-4.11.87-9.83,2.55-16,6-5.29,2.96-9.25,6.3-12,9l11,23c2.28-2.1,5.59-4.72,10-7,4.2-2.17,8.06-3.34,11-4l-4-27Z" fill={outfield[1]} strokeWidth="0"/>
                <path d="M116,62c-6.29-1.6-11.82-2-16-2-6.49,0-11.95.97-16,2l4,27c4.51-.76,8.58-1,12-1,4.58,0,8.62.43,12,1l4-27Z" fill={outfield[2]} strokeWidth="0"/>
                <path d="M144,76c-3.38-2.8-8.03-6.11-14-9-5.24-2.54-10.07-4.06-14-5l-4,27c2.75.53,6.71,1.62,11,4,4.16,2.31,7.11,5,9,7l12-24Z" fill={outfield[3]} strokeWidth="0"/>
                <path d="M162,102c-1.25-3.07-2.88-6.46-5-10-4.22-7.03-8.99-12.28-13-16l-12,24c3.03,2.52,6.68,6.11,10,11,1.67,2.46,2.98,4.84,4,7l16-16Z" fill={outfield[4]} strokeWidth="0"/>
            </g>
            
            <g>
                <path d="M44,54c-3.71,3.36-7.89,7.65-12,13-5.02,6.52-8.54,12.79-11,18l17,17c2.01-4.35,4.88-9.57,9-15,3.07-4.04,6.18-7.35,9-10l-12-23Z" fill={outfield[5]} strokeWidth="0"/>
                <path d="M80,36c-5.71,1.12-13.56,3.33-22,8-5.9,3.26-10.53,6.87-14,10l12,23c3.07-2.97,7.69-6.78,14-10,5.32-2.71,10.22-4.18,14-5l-4-26Z" fill={outfield[6]} strokeWidth="0"/>
                <path d="M120,36c-8.03-2.46-15.07-3-20-3-8.4,0-15.28,1.55-20,3l4,26c6.29-1.6,11.82-2,16-2,6.49,0,11.95.97,16,2l4-26Z" fill={outfield[7]} strokeWidth="0"/>
                <path d="M155,54c-3.8-3.36-9.11-7.41-16-11-7.24-3.77-13.9-5.83-19-7l-4,26c4.37,1.05,9.96,2.83,16,6,4.97,2.61,8.95,5.47,12,8l11-22Z" fill={outfield[8]} strokeWidth="0"/>
                <path d="M178,86c-1.55-4.11-3.77-8.93-7-14-5.31-8.33-11.33-14.17-16-18l-11,22c3.34,3.16,7.27,7.44,11,13,3.17,4.73,5.41,9.21,7,13l16-16Z" fill={outfield[9]} strokeWidth="0"/>
            </g>
            
            <g>
                <path d="M32,31c-3.82,3.55-7.94,7.85-12,13-7.11,9.02-11.84,17.81-15,25l16,16c2.77-5.6,6.63-12.18,12-19,3.74-4.76,7.52-8.73,11-12l-12-23Z" fill={outfield[10]} strokeWidth="0"/>
                <path d="M75,9c-6.07,1.44-13.71,3.85-22,8-9.05,4.53-16.01,9.7-21,14l12,23c4.38-3.96,10.99-9.02,20-13,5.98-2.64,11.49-4.13,16-5l-5-27Z" fill={outfield[11]} strokeWidth="0"/>
                <path d="M124,9c-6.35-1.58-14.89-3.05-25-3-9.65.05-17.83,1.46-24,3l5,27c8.03-2.46,15.07-3,20-3,8.4,0,15.28,1.55,20,3l4-27Z" fill={outfield[12]} strokeWidth="0"/>
                <path d="M166,30c-4.43-3.95-10.72-8.78-19-13-8.84-4.51-16.96-6.78-23-8l-4,27c5.1,1.17,11.76,3.23,19,7,6.89,3.59,12.2,7.64,16,11l11-24Z" fill={outfield[13]} strokeWidth="0"/>
                <path d="M195,69c-2.32-5.33-5.53-11.52-10-18-6.43-9.33-13.34-16.19-19-21l-11,24c4.03,3.28,9.18,8.17,14,15,4.47,6.33,7.25,12.34,9,17l17-17Z" fill={outfield[14]} strokeWidth="0"/>
            </g>
        </svg>
    );
}