from io import StringIO

from utils.advanced_pitching_stats_upload import (
    combine_advanced_pitching_stats,
    get_advanced_pitching_stats_from_buffer,
    is_in_strike_zone,
)


def test_is_in_strike_zone_pitching():
    assert is_in_strike_zone(2.5, 0.0)
    assert not is_in_strike_zone(4.0, 0.0)


def test_get_advanced_pitching_stats_from_buffer():
    csv = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,PlateLocHeight,PlateLocSide,TaggedHitType,TaggedPitchType,RelSpeed
Ace,AUB_TIG,,InPlay,Single,100,10,2.5,0.1,GroundBall,Fastball,95
Ace,AUB_TIG,Strikeout,StrikeSwinging,,0,0,2.6,0.1,,Fastball,96
Ace,AUB_TIG,Walk,BallCalled,,0,0,1.0,1.2,,Fastball,97
"""
    stats = get_advanced_pitching_stats_from_buffer(
        StringIO(csv), "20240216-Game-1.csv"
    )
    key = ("Ace", "AUB_TIG", 2024)
    assert key in stats
    record = stats[key]

    assert record["plate_app"] == 3
    assert record["batted_balls"] == 1
    assert record["ground_balls"] == 1
    assert record["avg_exit_velo"] == 100.0
    assert record["avg_fastball_velo"] == 96.0
    assert record["fastballs"] == 3
    assert record["k_per"] == 0.333
    assert record["bb_per"] == 0.333
    assert record["gb_per"] == 1.0
    assert record["la_sweet_spot_per"] == 1.0
    assert record["hard_hit_per"] == 1.0
    assert record["in_zone_pitches"] == 2
    assert record["whiff_per"] == 0.5
    assert record["out_of_zone_pitches"] == 1
    assert record["chase_per"] == 0
    assert record["processed_dates"] == ["2024-02-16"]


def test_combine_advanced_pitching_stats():
    existing = {
        "Pitcher": "Ace",
        "PitcherTeam": "AUB_TIG",
        "Year": 2024,
        "plate_app": 120,
        "batted_balls": 80,
        "ground_balls": 40,
        "avg_exit_velo": 85,
        "k_per": 0.25,
        "bb_per": 0.08,
        "gb_per": 0.5,
        "la_sweet_spot_per": 0.22,
        "hard_hit_per": 0.35,
        "in_zone_pitches": 200,
        "whiff_per": 0.2,
        "out_of_zone_pitches": 150,
        "chase_per": 0.18,
        "fastballs": 100,
        "avg_fastball_velo": 94,
        "processed_dates": ["2024-02-14"],
    }
    new = {
        "Pitcher": "Ace",
        "PitcherTeam": "AUB_TIG",
        "Year": 2024,
        "plate_app": 60,
        "batted_balls": 30,
        "ground_balls": 12,
        "avg_exit_velo": 90,
        "k_per": 0.2,
        "bb_per": 0.12,
        "gb_per": 0.4,
        "la_sweet_spot_per": 0.3,
        "hard_hit_per": 0.4,
        "in_zone_pitches": 80,
        "whiff_per": 0.25,
        "out_of_zone_pitches": 60,
        "chase_per": 0.15,
        "fastballs": 40,
        "avg_fastball_velo": 97,
        "processed_dates": ["2024-02-15"],
    }

    combined = combine_advanced_pitching_stats(existing, new)
    assert combined["plate_app"] == 180
    assert combined["batted_balls"] == 110
    assert combined["ground_balls"] == 52
    # Weighted averages
    expected_exit = ((85 * 80) + (90 * 30)) / 110
    assert combined["avg_exit_velo"] == round(expected_exit, 1)
    expected_k = ((0.25 * 120) + (0.2 * 60)) / 180
    assert combined["k_per"] == round(expected_k, 3)
    expected_bb = ((0.08 * 120) + (0.12 * 60)) / 180
    assert combined["bb_per"] == round(expected_bb, 3)
    expected_gb = ((0.5 * 80) + (0.4 * 30)) / 110
    assert combined["gb_per"] == round(expected_gb, 3)
    expected_whiff = ((0.2 * 200) + (0.25 * 80)) / 280
    assert combined["whiff_per"] == round(expected_whiff, 3)
    expected_chase = ((0.18 * 150) + (0.15 * 60)) / 210
    assert combined["chase_per"] == round(expected_chase, 3)
    expected_fastball_velo = ((94 * 100) + (97 * 40)) / 140
    assert combined["avg_fastball_velo"] == round(expected_fastball_velo, 1)
    assert combined["processed_dates"] == ["2024-02-14", "2024-02-15"]


def test_combine_advanced_pitching_stats_skips_duplicate_dates():
    existing = {
        "Pitcher": "Ace",
        "PitcherTeam": "AUB_TIG",
        "Year": 2024,
        "plate_app": 10,
        "batted_balls": 5,
        "processed_dates": ["2024-02-16"],
    }
    new = {
        "Pitcher": "Ace",
        "PitcherTeam": "AUB_TIG",
        "Year": 2024,
        "plate_app": 5,
        "batted_balls": 3,
        "processed_dates": ["2024-02-16"],
    }

    combined = combine_advanced_pitching_stats(existing, new)
    assert combined == existing
