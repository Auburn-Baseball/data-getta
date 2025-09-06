export interface ConferenceGroup {
  ConferenceName: string;
  teams: ConferenceGroupTeam[];
}

export interface ConferenceGroupTeam {
  TeamName: string;
  TrackmanAbbreviation: string;
}
