from io import StringIO

from utils.pitcher_stats_upload import (
    calculate_innings_pitched,
    get_pitcher_stats_from_buffer,
    is_in_strike_zone,
)


def test_pitcher_is_in_strike_zone():
    assert is_in_strike_zone(2.5, 0.1) is True
    assert is_in_strike_zone(4.0, 0.0) is False
    assert is_in_strike_zone(2.0, 0.9) is False


def test_calculate_innings_pitched():
    assert calculate_innings_pitched(3, 0) == 1.0
    assert calculate_innings_pitched(2, 0) == 0.2
    assert calculate_innings_pitched(1, 1) == 0.2


def test_get_pitcher_stats_from_buffer():
    csv = """Pitcher,PitcherTeam,PlayResult,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,GameUID
Ace,AUB_TIG,,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,H1,G1
Ace,AUB_TIG,Single,,InPlay,2.3,0.1,1,0,0,1,2,0,H2,G1
Ace,AUB_TIG,,Walk,BallCalled,1.0,1.2,1,0,1,0,3,0,H3,G1
Ace,AUB_TIG,HomeRun,,InPlay,2.8,0.2,1,0,0,0,4,0,H4,G1
Ace,AUB_TIG,,Strikeout,StrikeSwinging,3.0,0.0,1,1,0,0,5,0,H5,G1
"""
    stats = get_pitcher_stats_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    key = ("Ace", "AUB_TIG", 2024)
    assert key in stats
    record = stats[key]

    assert record["total_strikeouts_pitcher"] == 2
    assert record["total_walks_pitcher"] == 1
    assert record["pitches"] == 5
    assert record["hits"] == 2
    assert record["homeruns"] == 1
    assert record["games_started"] == 1
    assert record["total_innings_pitched"] == 0.2
    assert record["k_per_9"] == 27.0
    assert record["bb_per_9"] == 13.5
    assert record["whip"] == 4.5
    assert record["total_batters_faced"] == 5
    assert record["total_in_zone_pitches"] == 4
    assert record["total_out_of_zone_pitches"] == 1
    assert record["chase_percentage"] == 0
    assert record["games"] == 1


def test_get_pitcher_stats_missing_columns():
    csv = "Pitcher,PitcherTeam\nAce,AUB_TIG\n"
    stats = get_pitcher_stats_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    assert stats == {}
