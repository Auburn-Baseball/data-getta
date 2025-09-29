export interface ConferenceGroup {
  ConferenceName: string;
  teams: ConferenceGroupTeam[];
}

export interface ConferenceGroupTeam {
  TeamName: string;
  TrackmanAbbreviation: string;
}

export type PitchType =
  | 'All'
  | 'FourSeam'
  | 'Sinker'
  | 'Slider'
  | 'Curveball'
  | 'Changeup'
  | 'Cutter'
  | 'Splitter'
  | 'Other';
