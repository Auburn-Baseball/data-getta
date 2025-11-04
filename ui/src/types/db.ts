export interface TeamsTable {
  Year: number;
  TeamName: string | null;
  TrackmanAbbreviation: string;
  Conference: string | null;
  Mascot: string | null;
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
  is_practice: boolean;
}

export interface PitcherStatsTable {
  Pitcher: string;
  PitcherTeam: string;
  Date: string;
  Year: number;
  hits?: number;
  runs_allowed?: number;
  homeruns?: number;
  earned_runs?: number;
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
  k_per_9?: number;
  bb_per_9?: number;
  whip?: number;
  is_practice: boolean;
}

export interface PitchCountsTable {
  Pitcher: string;
  PitcherTeam: string;
  Date: string;
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
  is_practice: boolean;
}

export interface SeasonDatesTable {
  year: number;
  season_start: string | null;
  season_end: string | null;
}

// Updated PitcherPitchBinsTable to include Date field
export interface PitcherPitchBinsTable {
  PitcherTeam: string;
  Date: string; // Added Date field
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

// Updated BatterPitchBinsTable to include Date field
export interface BatterPitchBinsTable {
  BatterTeam: string;
  Date: string; // Added Date field
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

export interface ProcessedFilesTable {
  id: number;
  file_hash: string;
  remote_path: string;
  file_size: number | null;
  last_modified: string | null;
  processed_at: string | null;
  stats_summary: unknown | null;
  created_at: string | null;
}

export interface AdvancedBattingStatsTable {
  Batter: string;
  BatterTeam: string;
  Year: number;
  plate_app?: number;
  batted_balls?: number;
  k_per: number | null;
  bb_per: number | null;
  avg_exit_velo: number | null;
  created_at?: string;
  la_sweet_spot_per: number | null;
  hard_hit_per: number | null;
  avg_exit_velo_rank: number | null;
  k_per_rank: number | null;
  bb_per_rank: number | null;
  la_sweet_spot_per_rank: number | null;
  hard_hit_per_rank: number | null;
  in_zone_pitches?: number;
  out_of_zone_pitches?: number;
  whiff_per: number | null;
  chase_per: number | null;
  whiff_per_rank: number | null;
  chase_per_rank: number | null;
  infield_left_slice?: number;
  infield_left_per?: number;
  infield_lc_slice?: number;
  infield_lc_per?: number;
  infield_center_slice?: number;
  infield_center_per?: number;
  infield_rc_slice?: number;
  infield_rc_per?: number;
  infield_right_slice?: number;
  infield_right_per?: number;
  xba_per?: number;
  xba_per_rank?: number;
  xslg_per?: number;
  xslg_per_rank?: number;
  at_bats?: number;
  xwoba_per?: number;
  xwoba_per_rank?: number;
  barrel_per?: number;
  barrel_per_rank?: number;
  avg_exit_velo_rank_team?: number | null;
  k_per_rank_team?: number | null;
  bb_per_rank_team?: number | null;
  la_sweet_spot_per_rank_team?: number | null;
  hard_hit_per_rank_team?: number | null;
  whiff_per_rank_team?: number | null;
  chase_per_rank_team?: number | null;
  xba_per_rank_team?: number | null;
  xslg_per_rank_team?: number | null;
  xwoba_per_rank_team?: number | null;
  barrel_per_rank_team?: number | null;
}

export interface AdvancedPitchingStatsTable {
  Pitcher: string;
  PitcherTeam: string;
  Year: number;
  fastballs?: number;
  batted_balls?: number;
  k_per: number | null;
  bb_per: number | null;
  avg_exit_velo: number | null;
  created_at?: string;
  la_sweet_spot_per: number | null;
  hard_hit_per: number | null;
  avg_exit_velo_rank: number | null;
  k_per_rank: number | null;
  bb_per_rank: number | null;
  la_sweet_spot_per_rank: number | null;
  hard_hit_per_rank: number | null;
  in_zone_pitches?: number;
  out_of_zone_pitches?: number;
  whiff_per: number | null;
  chase_per: number | null;
  whiff_per_rank: number | null;
  chase_per_rank: number | null;
  plate_app?: number;
  avg_fastball_velo?: number;
  avg_fastball_rank?: number;
  ground_balls?: number;
  gb_per?: number;
  gb_per_rank?: number;
  xba_per?: number;
  xba_per_rank?: number;
  xwoba_per?: number;
  xwoba_per_rank?: number;
  xslg_per?: number;
  xslg_per_rank?: number;
  at_bats?: number;
  barrel_per?: number;
  barrel_per_rank?: number;
}
