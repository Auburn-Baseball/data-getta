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
  hits: number | null;
  at_bats: number | null;
  strikes: number | null;
  walks: number | null;
  strikeouts: number | null;
  homeruns: number | null;
  extra_base_hits: number | null;
  plate_appearances: number | null;
  hit_by_pitch: number | null;
  sacrifice: number | null;
  total_bases: number | null;
  batting_average: number | null;
  on_base_percentage: number | null;
  slugging_percentage: number | null;
  onbase_plus_slugging: number | null;
  isolated_power: number | null;
  k_percentage: number | null;
  base_on_ball_percentage: number | null;
  chase_percentage: number | null;
  in_zone_whiff_percentage: number | null;
  games: number | null;
}

export interface PitcherStatsTable {
  Pitcher: string;
  PitcherTeam: string;
  Year: number;
  total_strikeouts_pitcher: number | null;
  total_walks_pitcher: number | null;
  total_out_of_zone_pitches: number | null;
  total_in_zone_pitches: number | null;
  misses_in_zone: number | null;
  swings_in_zone: number | null;
  total_num_chases: number | null;
  pitches: number | null;
  games_started: number | null;
  total_innings_pitched: number | null;
  total_batters_faced: number | null;
  k_percentage: number | null;
  base_on_ball_percentage: number | null;
  in_zone_whiff_percentage: number | null;
  chase_percentage: number | null;
  games: number | null;
}

export interface PitchCountsTable {
  Pitcher: string;
  PitcherTeam: string;
  Year: number;
  total_pitches: number | null;
  curveball_count: number | null;
  fourseam_count: number | null;
  sinker_count: number | null;
  slider_count: number | null;
  twoseam_count: number | null;
  changeup_count: number | null;
  cutter_count: number | null;
  splitter_count: number | null;
  other_count: number | null;
  games: number | null;
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
