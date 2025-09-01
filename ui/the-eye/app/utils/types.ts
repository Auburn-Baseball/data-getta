/*
* Types relating to database views and functions.
* Created manually because Prisma does not support views and functions,
* so raw SQL is used to query views and functions.
* 
* author: Braden Mosley
* lastEdit: 04-24-2024
*/

export type batter_stats = {
    Batter : string;
    BatterTeam : string;
    hits : bigint;
    at_bats : bigint;
    strikes : bigint;
    walks : bigint;
    strikeouts : bigint;
    homeruns : bigint;
    extra_base_hits : bigint;
    plate_appearances : bigint;
    hit_by_pitch : bigint;
    sacrifice : bigint;
    total_bases : bigint;
    on_base_percentage : number;
    slugging_percentage : number;
    chase_percentage : number;
    in_zone_whiff_percentage : number;
    games : bigint;
    batting_average : number;
    onbase_plus_slugging : number;
    isolated_power : number;
    k_percentage : number;
    base_on_ball_percentage: number;
}

export type batter_stats_forTable = {
    Batter : string;
    BatterTeam : string;
    hits : number;
    at_bats : number;
    strikes : number;
    walks : number;
    strikeouts : number;
    homeruns : number;
    extra_base_hits : number;
    plate_appearances : number;
    hit_by_pitch : number;
    sacrifice : number;
    total_bases : number;
    on_base_percentage : number;
    slugging_percentage : number;
    chase_percentage : number;
    in_zone_whiff_percentage : number;
    games : number;
    batting_average : number;
    onbase_plus_slugging : number;
    isolated_power : number;
    k_percentage : number;
    base_on_ball_percentage: number;
}

export type pitcher_stats = {
    Pitcher : string;
    PitcherTeam : string;
    total_strikeouts_pitcher : bigint;
    total_walks_pitcher : bigint;
    total_out_of_zone_pitches : bigint;
    misses_in_zone : bigint;
    swings_in_zone : bigint;
    total_num_chases : bigint;
    pitches : bigint;
    games : bigint;
    games_started : bigint;
    total_innings_pitched : number;
    total_batters_faced : bigint;
    in_zone_whiff_percentage : number;
    chase_percentage : number;
    k_percentage : number;
    base_on_ball_percentage : number;
}

export type pitcher_stats_forTable = {
    Pitcher : string;
    PitcherTeam : string;
    total_strikeouts_pitcher : number;
    total_walks_pitcher : number;
    total_out_of_zone_pitches : number;
    misses_in_zone : number;
    swings_in_zone : number;
    total_num_chases : number;
    pitches : number;
    games : number;
    games_started : number;
    total_innings_pitched : number;
    total_batters_faced : number;
    in_zone_whiff_percentage : number;
    chase_percentage : number;
    k_percentage : number;
    base_on_ball_percentage : number;
}

export type pitch_sums = {
    Pitcher : string;
    PitcherTeam : string;
    total_pitches : bigint;
    curveball_count : bigint;
    fourseam_count : bigint;
    sinker_count : bigint;
    slider_count : bigint;
    twoseam_count : bigint;
    changeup_count : bigint;
    cutter_count : bigint;
    splitter_count : bigint;
    other_count : bigint;
}

export type pitch_sums_forTable = {
    Pitcher : string;
    PitcherTeam : string;
    total_pitches : number;
    curveball_count : number;
    fourseam_count : number;
    sinker_count : number;
    slider_count : number;
    twoseam_count : number;
    changeup_count : number;
    cutter_count : number;
    splitter_count : number;
    other_count : number;
}

export type pitcher_run_values = {
    Pitcher: string;
    PitcherTeam: string;
    PitchType: string;
    Score: number | null;
    Handedness: string | null;
}

export type batter_run_values = {
    Batter: string;
    BatterTeam: string;
    BatterSide: string;
    PitchType: string;
    PitcherThrows: string;
    NumPitches: number | null;
    Score: number | null;
}