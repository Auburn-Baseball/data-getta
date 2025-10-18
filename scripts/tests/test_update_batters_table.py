from io import StringIO

from utils.update_batters_table import (
    calculate_total_bases,
    get_batter_stats_from_buffer,
    is_in_strike_zone,
)


def test_is_in_strike_zone_basic():
    assert is_in_strike_zone(2.5, 0.1) is True
    assert is_in_strike_zone(1.0, 0.0) is False
    assert is_in_strike_zone(2.0, 1.0) is False


def test_calculate_total_bases():
    assert calculate_total_bases("Single") == 1
    assert calculate_total_bases("Triple") == 3
    assert calculate_total_bases("Unknown") == 0


def test_get_batter_stats_from_buffer_aggregates():
    csv = """Batter,BatterTeam,PlayResult,KorBB,PitchCall,PlateLocHeight,PlateLocSide,TaggedHitType,GameUID,ExitSpeed
Doe,AUB_TIG,Single,,InPlay,2.5,0.1,LineDrive,G1,90
Doe,AUB_TIG,,Strikeout,StrikeSwinging,2.4,0.0,LineDrive,G1,
Doe,AUB_TIG,,Walk,BallCalled,1.0,1.5,LineDrive,G1,
Doe,AUB_TIG,HomeRun,,InPlay,2.8,0.2,FlyBall,G1,105
"""
    buffer = StringIO(csv)
    stats = get_batter_stats_from_buffer(buffer, "20240216-Game-1.csv")
    key = ("Doe", "AUB_TIG", 2025)
    assert key in stats
    record = stats[key]

    assert record["hits"] == 2
    assert record["at_bats"] == 3
    assert record["walks"] == 1
    assert record["strikeouts"] == 1
    assert record["total_bases"] == 5
    assert record["plate_appearances"] == 4
    assert record["batting_average"] == 0.667
    assert record["on_base_percentage"] == 0.75
    assert record["slugging_percentage"] == 1.667
    assert record["in_zone_whiff_percentage"] == 0.333
    assert record["chase_percentage"] == 0
    assert record["total_exit_velo"] == 195.0
    assert record["games"] == 1


def test_get_batter_stats_missing_columns_returns_empty():
    csv = "Batter,BatterTeam\nDoe,AUB_TIG\n"
    stats = get_batter_stats_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    assert stats == {}
