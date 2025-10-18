from io import StringIO

from utils.update_advanced_batting_table import (
    combine_advanced_batting_stats,
    get_advanced_batting_stats_from_buffer,
    is_in_strike_zone,
)


def test_is_in_strike_zone_bounds():
    assert is_in_strike_zone(2.5, 0.0)
    assert not is_in_strike_zone(1.0, 0.0)
    assert not is_in_strike_zone(2.5, 1.0)


def test_get_advanced_batting_stats_from_buffer():
    csv = """Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,PlateLocHeight,PlateLocSide,Distance,Bearing
Doe,AUB_TIG,,InPlay,Single,100,15,2.5,0.1,150,10
Doe,AUB_TIG,Strikeout,StrikeSwinging,,0,0,2.8,0.2,0,0
Doe,AUB_TIG,Walk,BallCalled,,0,0,1.0,1.2,0,0
"""
    stats = get_advanced_batting_stats_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    key = ("Doe", "AUB_TIG", 2024)
    assert key in stats
    record = stats[key]

    assert record["plate_app"] == 3
    assert record["batted_balls"] == 1
    assert record["avg_exit_velo"] == 100.0
    assert record["k_per"] == 0.333
    assert record["bb_per"] == 0.333
    assert record["la_sweet_spot_per"] == 1.0
    assert record["hard_hit_per"] == 1.0
    assert record["in_zone_pitches"] == 2
    assert record["whiff_per"] == 0.5
    assert record["out_of_zone_pitches"] == 1
    assert record["chase_per"] == 0
    assert record["infield_rc_slice"] == 1
    assert record["infield_rc_per"] == 1.0


def test_combine_advanced_batting_stats():
    existing = {
        "Batter": "Doe",
        "BatterTeam": "AUB_TIG",
        "Year": 2024,
        "plate_app": 100,
        "batted_balls": 80,
        "avg_exit_velo": 90,
        "k_per": 0.25,
        "bb_per": 0.1,
        "la_sweet_spot_per": 0.2,
        "hard_hit_per": 0.3,
        "in_zone_pitches": 200,
        "whiff_per": 0.2,
        "out_of_zone_pitches": 150,
        "chase_per": 0.15,
        "infield_left_slice": 5,
        "infield_lc_slice": 10,
        "infield_center_slice": 20,
        "infield_rc_slice": 25,
        "infield_right_slice": 20,
    }
    new = {
        "Batter": "Doe",
        "BatterTeam": "AUB_TIG",
        "Year": 2024,
        "plate_app": 50,
        "batted_balls": 40,
        "avg_exit_velo": 100,
        "k_per": 0.1,
        "bb_per": 0.2,
        "la_sweet_spot_per": 0.3,
        "hard_hit_per": 0.5,
        "in_zone_pitches": 100,
        "whiff_per": 0.3,
        "out_of_zone_pitches": 50,
        "chase_per": 0.1,
        "infield_left_slice": 2,
        "infield_lc_slice": 4,
        "infield_center_slice": 6,
        "infield_rc_slice": 8,
        "infield_right_slice": 10,
    }

    combined = combine_advanced_batting_stats(existing, new)
    assert combined["plate_app"] == 150
    assert combined["batted_balls"] == 120
    # Weighted average exit velocity: (90*80 + 100*40) / 120 = 93.333...
    assert combined["avg_exit_velo"] == 93.3
    # Strikeouts: 0.25*100 + 0.1*50 = 25 + 5 = 30 -> 30/150 = 0.2
    assert combined["k_per"] == 0.2
    # Walks: 0.1*100 + 0.2*50 = 10 + 10 = 20 -> 20/150 = 0.133...
    assert combined["bb_per"] == 0.133
    # Sweet spot: (0.2*80 + 0.3*40)/120 = (16 + 12)/120 = 0.2333
    assert combined["la_sweet_spot_per"] == 0.233
    # Hard hit: (0.3*80 + 0.5*40)/120 = (24 + 20)/120 = 0.3666
    assert combined["hard_hit_per"] == 0.367
    assert combined["in_zone_pitches"] == 300
    # Whiff: (0.2*200 + 0.3*100)/300 = (40 + 30)/300 = 0.2333
    assert combined["whiff_per"] == 0.233
    assert combined["out_of_zone_pitches"] == 200
    # Chase: (0.15*150 + 0.1*50)/200 = (22.5 + 5)/200 = 0.1375
    assert combined["chase_per"] == 0.138
    # Infield slices
    assert combined["infield_left_slice"] == 7
    assert combined["infield_rc_slice"] == 33
    total_infield = (
        combined["infield_left_slice"]
        + combined["infield_lc_slice"]
        + combined["infield_center_slice"]
        + combined["infield_rc_slice"]
        + combined["infield_right_slice"]
    )
    assert total_infield == 7 + 14 + 26 + 33 + 30
    assert combined["infield_rc_per"] == round(
        combined["infield_rc_slice"] / total_infield, 3
    )
