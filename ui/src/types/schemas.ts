export interface TeamsTable {
  Year: number;
  TeamName: string;
  TrackmanAbbreviation: string;
  Conference: string;
  Mascot: string;
}

export interface PlayersTable {
  Name: string;
  PitcherId: string | null;
  BatterId: string | null;
  TeamTrackmanAbbreviation: string;
  Year: number;
}

export interface BatterStatsTable {
  Batter: string;
  BatterTeam: string;
  Date: string;
  hits: number;
  doubles: number;
  triples: number;
  singles?: number;
  at_bats: number;
  strikes: number;
  walks: number;
  strikeouts: number;
  homeruns: number;
  extra_base_hits: number;
  plate_appearances: number;
  hit_by_pitch: number;
  sacrifice: number;
  total_bases: number;
  batted_balls?: number;
  total_exit_velo?: number;
  batting_average: number;
  on_base_percentage: number;
  slugging_percentage: number;
  onbase_plus_slugging: number;
  isolated_power: number;
  k_percentage: number;
  base_on_ball_percentage: number;
  chase_percentage: number;
  in_zone_whiff_percentage: number;
  games: number;
  k_per: number;
  bb_per: number;
  avg_exit_velo: number;
  is_practice?: boolean;
}

export interface PitcherStatsTable {
  Pitcher: string;
  PitcherTeam: string;
  Year: number;
  total_strikeouts_pitcher: number;
  total_walks_pitcher: number;
  total_out_of_zone_pitches: number;
  total_in_zone_pitches: number;
  misses_in_zone: number;
  swings_in_zone: number;
  total_num_chases: number;
  pitches: number;
  games_started: number;
  total_innings_pitched: number;
  total_batters_faced: number;
  k_percentage: number;
  base_on_ball_percentage: number;
  in_zone_whiff_percentage: number;
  chase_percentage: number;
  games: number;
}

export interface PitchCountsTable {
  Pitcher: string;
  PitcherTeam: string;
  Year: number;
  total_pitches: number;
  curveball_count: number;
  fourseam_count: number;
  sinker_count: number;
  slider_count: number;
  twoseam_count: number;
  changeup_count: number;
  cutter_count: number;
  splitter_count: number;
  other_count: number;
  games: number;
}

export interface SeasonDatesTable {
  year: number;
  season_start: string;
  season_end: string;
}

export interface PitcherPitchBinsTable {
  PitcherTeam: string;
  Year: number;
  Pitcher: string;
  ZoneId: number; // 1..13 (1..9 inner; 10..13 outer)
  InZone: boolean; // true for inner
  ZoneRow: number; // 1..3 for inner, 0 outer
  ZoneCol: number; // 1..3 for inner, 0 outer
  ZoneCell: number; // 1..9 for inner, 0 outer
  OuterLabel: 'NA' | 'OTL' | 'OTR' | 'OBL' | 'OBR';
  ZoneVersion: string;
  TotalPitchCount: number;
  Count_FourSeam: number;
  Count_Sinker: number;
  Count_Slider: number;
  Count_Curveball: number;
  Count_Changeup: number;
  Count_Cutter: number;
  Count_Splitter: number;
  Count_Other: number;
  Count_L_FourSeam: number;
  Count_L_Sinker: number;
  Count_L_Slider: number;
  Count_L_Curveball: number;
  Count_L_Changeup: number;
  Count_L_Cutter: number;
  Count_L_Splitter: number;
  Count_L_Other: number;
  Count_R_FourSeam: number;
  Count_R_Sinker: number;
  Count_R_Slider: number;
  Count_R_Curveball: number;
  Count_R_Changeup: number;
  Count_R_Cutter: number;
  Count_R_Splitter: number;
  Count_R_Other: number;
}

export interface BatterPitchBinsTable {
  BatterTeam: string;
  Year: number;
  Batter: string;
  ZoneId: number; // 1..13 (1..9 inner; 10..13 outer)
  InZone: boolean; // true for inner
  ZoneRow: number; // 1..3 for inner, 0 outer
  ZoneCol: number; // 1..3 for inner, 0 outer
  ZoneCell: number; // 1..9 for inner, 0 outer
  OuterLabel: 'NA' | 'OTL' | 'OTR' | 'OBL' | 'OBR';
  ZoneVersion: string;
  TotalPitchCount: number;
  TotalSwingCount: number;
  TotalHitCount: number;
  Count_FourSeam: number;
  Count_Sinker: number;
  Count_Slider: number;
  Count_Curveball: number;
  Count_Changeup: number;
  Count_Cutter: number;
  Count_Splitter: number;
  Count_Other: number;
  SwingCount_FourSeam: number;
  SwingCount_Sinker: number;
  SwingCount_Slider: number;
  SwingCount_Curveball: number;
  SwingCount_Changeup: number;
  SwingCount_Cutter: number;
  SwingCount_Splitter: number;
  SwingCount_Other: number;
  HitCount_FourSeam: number;
  HitCount_Sinker: number;
  HitCount_Slider: number;
  HitCount_Curveball: number;
  HitCount_Changeup: number;
  HitCount_Cutter: number;
  HitCount_Splitter: number;
  HitCount_Other: number;
}
