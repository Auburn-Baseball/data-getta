from io import StringIO

from utils.update_players_table import get_players_from_buffer


def test_get_players_from_buffer_combines_pitcher_and_batter():
    csv = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
Doe,D123,AUB_TIG,Doe,B456,AUB_TIG
Smith,S789,AUB_TIG,,,
,,,
"""
    players = get_players_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    key = ("Doe", "AUB_TIG", 2025)
    assert key in players
    record = players[key]
    assert record["PitcherId"] == "D123"
    assert record["BatterId"] == "B456"
    assert record["TeamTrackmanAbbreviation"] == "AUB_TIG"


def test_get_players_from_buffer_missing_columns():
    csv = "Name,Team\nJane,AUB\n"
    players = get_players_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    assert players == {}
