"""
Author: Joshua Reed
Created: 1 November 2025

Unit test cases for advanced_batting_stats_upload.py functions.
"""

import builtins
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from scripts.utils import advanced_batting_stats_upload as mod


def test_xba_grid_missing(tmp_path):
    path = tmp_path / "missing.csv"  # does not exist
    xba_grid, xba_dict, ev_bins, la_bins, dir_bins, mean = mod.load_xba_grid(path)
    assert xba_grid.empty
    assert xba_dict == {}
    assert ev_bins == []
    assert la_bins == []
    assert dir_bins == []
    assert mean == 0.25


def test_xba_grid_exists(tmp_path):
    path = tmp_path / "xba.csv"
    path.write_text("ev_bin,la_bin,dir_bin,xBA\n" "80,20,1,0.3\n" "85,25,2,0.4\n")

    xba_grid, xba_dict, ev_bins, la_bins, dir_bins, mean = mod.load_xba_grid(path)

    assert not xba_grid.empty
    assert len(xba_dict) == 2
    assert set(ev_bins) == {80, 85}
    assert set(la_bins) == {20, 25}
    assert set(dir_bins) == {1, 2}
    assert abs(mean - 0.35) < 1e-6


def test_exact_value():
    lst = [1, 3, 5, 7]
    assert mod.closest_value(lst, 5) == 5
    assert mod.closest_value(lst, 1) == 1
    assert mod.closest_value(lst, 7) == 7


def test_between_values():
    lst = [1, 3, 6, 10]
    assert mod.closest_value(lst, 4) == 3  # 3 is closer than 6
    assert mod.closest_value(lst, 7) == 6  # 6 is closer than 10


def test_smaller_than_smallest():
    lst = [10, 20, 30]
    assert mod.closest_value(lst, 5) == 10


def test_larger_than_largest():
    lst = [10, 20, 30]
    assert mod.closest_value(lst, 35) == 30


def test_equidistant_values():
    lst = [1, 3, 5, 7]
    assert mod.closest_value(lst, 4) == 3  # Should retrun value before the input


def test_lookup_xBA_exact_match(monkeypatch):
    # Setup minimal globals
    test_dict = {(80, 20, 1): 0.3, (85, 25, 2): 0.4}
    monkeypatch.setattr(mod, "xba_dict", test_dict)
    monkeypatch.setattr(mod, "ev_bins", [80, 85])
    monkeypatch.setattr(mod, "la_bins", [20, 25])
    monkeypatch.setattr(mod, "dir_bins", [1, 2])
    monkeypatch.setattr(mod, "global_xba_mean", 0.35)

    # Exact match
    assert mod.lookup_xBA(80, 20, 1) == 0.3
    assert mod.lookup_xBA(85, 25, 2) == 0.4


def test_lookup_xBA_3D_average(monkeypatch):
    # Setup globals
    test_dict = {(80, 20, 1): 0.3, (81, 21, 1): 0.4, (79, 19, 6): 0.5}
    monkeypatch.setattr(mod, "xba_dict", test_dict)
    monkeypatch.setattr(mod, "ev_bins", [79, 80, 81])
    monkeypatch.setattr(mod, "la_bins", [19, 20, 21])
    monkeypatch.setattr(mod, "dir_bins", [1, 6])
    monkeypatch.setattr(mod, "global_xba_mean", 0.35)

    # Should average neighbors in 3D window
    val = mod.lookup_xBA(80, 20, 3)
    assert abs(val - (0.3 + 0.4 + 0.5) / 3) < 1e-6


def test_lookup_xBA_nearest_neighbor(monkeypatch):
    test_dict = {(80, 20, 1): 0.3, (85, 25, 2): 0.5}
    monkeypatch.setattr(mod, "xba_dict", test_dict)
    monkeypatch.setattr(mod, "ev_bins", [80, 85])
    monkeypatch.setattr(mod, "la_bins", [20, 25])
    monkeypatch.setattr(mod, "dir_bins", [1, 2])
    monkeypatch.setattr(mod, "global_xba_mean", 0.35)

    # There is no neighbor for (81,19,3) in the 3D window
    # So function should return global mean
    assert mod.lookup_xBA(81, 19, 3) == 0.35


def test_lookup_xBA_empty_dict(monkeypatch):
    # Empty dictionary guarantees fallback to global_xba_mean
    monkeypatch.setattr(mod, "xba_dict", {})
    monkeypatch.setattr(mod, "ev_bins", [80, 85])
    monkeypatch.setattr(mod, "la_bins", [20, 25])
    monkeypatch.setattr(mod, "dir_bins", [1, 2])
    monkeypatch.setattr(mod, "global_xba_mean", 0.35)

    # Should return global mean because dictionary is empty
    result = mod.lookup_xBA(100, 100, 50)
    assert result == 0.35


def test_load_xslg_model_success(tmp_path, monkeypatch):
    # Create a fake path that "exists"
    model_file = tmp_path / "xslg_model.json"
    model_file.write_text("{}")  # dummy content

    # Mock XGBRegressor to avoid real loading
    mock_regressor = MagicMock()
    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: mock_regressor)

    # Mock load_model to just record call
    mock_regressor.load_model = MagicMock()

    result = mod.load_xslg_model(model_file)

    assert result is mock_regressor
    mock_regressor.load_model.assert_called_once_with(str(model_file))


def test_load_xslg_model_path_not_exist(monkeypatch):
    # Create a Path object that does NOT exist
    fake_path = Path("/does/not/exist.json")

    # Mock XGBRegressor so it won't actually be called
    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: None)

    # Capture print output
    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = mod.load_xslg_model(fake_path)

    assert result is None
    assert any("not found" in msg for msg in printed)


def test_load_xslg_model_load_fail(tmp_path, monkeypatch):
    # Create a fake path that exists
    model_file = tmp_path / "xslg_model.json"
    model_file.write_text("{}")

    # Mock XGBRegressor to raise an exception when load_model is called
    class FakeRegressor:
        def load_model(self, path):
            raise ValueError("fake load error")

    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: FakeRegressor())

    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = mod.load_xslg_model(model_file)

    # It should still return the regressor object even though loading failed
    assert isinstance(result, FakeRegressor)
    assert any("Failed to load" in msg for msg in printed)


def test_load_xwoba_model_success(tmp_path, monkeypatch):
    # Create a fake path that "exists"
    model_file = tmp_path / "xwoba_model.json"
    model_file.write_text("{}")  # dummy content

    # Mock XGBRegressor to avoid real loading
    mock_regressor = MagicMock()
    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: mock_regressor)

    # Mock load_model to just record call
    mock_regressor.load_model = MagicMock()

    result = mod.load_xwoba_model(model_file)

    assert result is mock_regressor
    mock_regressor.load_model.assert_called_once_with(str(model_file))


def test_load_xwoba_model_path_not_exist(monkeypatch):
    # Create a Path object that does NOT exist
    fake_path = Path("/does/not/exist.json")

    # Mock XGBRegressor so it won't actually be called
    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: None)

    # Capture print output
    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = mod.load_xwoba_model(fake_path)

    assert result is None
    assert any("not found" in msg for msg in printed)


def test_load_xwoba_model_load_fail(tmp_path, monkeypatch):
    # Create a fake path that exists
    model_file = tmp_path / "xwoba_model.json"
    model_file.write_text("{}")

    # Mock XGBRegressor to raise an exception when load_model is called
    class FakeRegressor:
        def load_model(self, path):
            raise ValueError("fake load error")

    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: FakeRegressor())

    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = mod.load_xwoba_model(model_file)

    # It should still return the regressor object even though loading failed
    assert isinstance(result, FakeRegressor)
    assert any("Failed to load" in msg for msg in printed)


class DummyParser:
    def get_date_components(self, filename):
        if filename == "bad_filename.csv":
            return None
        return (2025, 5, 20)  # year, month, day


@pytest.fixture(autouse=True)
def patch_csv_parser(monkeypatch):
    # Patch CSVFilenameParser globally
    monkeypatch.setattr(mod, "CSVFilenameParser", lambda: DummyParser())


def make_csv(data: str):
    """Helper to create buffer from CSV string."""
    return io.StringIO(data)


def test_missing_required_columns_returns_empty(monkeypatch, capsys):
    csv_data = "Batter,KorBB\nJohnDoe,Walk"  # missing multiple required columns
    buffer = make_csv(csv_data)

    result = mod.get_advanced_batting_stats_from_buffer(buffer, "file.csv")

    # Should return empty dict
    assert result == {}

    # Should print an error message
    captured = capsys.readouterr()
    assert "Usecols do not match columns" in captured.out


def test_empty_csv(monkeypatch):
    csv_data = "Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League\n"
    buffer = make_csv(csv_data)
    result = mod.get_advanced_batting_stats_from_buffer(buffer, "file.csv")
    assert result == {}  # No rows to process


def test_bad_filename(monkeypatch):
    csv_data = "Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League\nJohnDoe,DoeTeam,Walk,InPlay,Out,90,20,10,Left,1.5,0.5,30,150,College"
    buffer = make_csv(csv_data)

    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = mod.get_advanced_batting_stats_from_buffer(buffer, "bad_filename.csv")
    assert result == {}
    assert any("Unable to extract date from filename" in msg for msg in printed)


def test_regular_game_stats(monkeypatch):
    csv_data = (
        "Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League\n"
        # Plate appearance 1: Walk
        "JohnDoe,DoeTeam,Walk,,,,NaN,NaN,NaN,Left,NaN,NaN,NaN,NaN,College\n"
        # Plate appearance 2: Batted ball in play
        "JohnDoe,DoeTeam,,InPlay,Out,95,25,10,Right,1.5,0.5,0,150,College\n"
        # Plate appearance 3: Strikeout
        "JohnDoe,DoeTeam,Strikeout,,,,NaN,NaN,NaN,Left,NaN,NaN,NaN,NaN,College"
    )
    buffer = make_csv(csv_data)

    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", lambda h, s: True)

    result = mod.get_advanced_batting_stats_from_buffer(buffer, "file_2025.csv")
    key = ("JohnDoe", "DoeTeam", 2025)
    assert key in result
    stats = result[key]

    assert stats["plate_app"] == 3
    assert stats["at_bats"] == 2  # Strikeout + Batted ball
    assert stats["batted_balls"] == 1
    assert stats["k_per"] == pytest.approx(1 / 3, rel=1e-3)
    assert stats["bb_per"] == pytest.approx(1 / 3, rel=1e-3)
    assert stats["xba_per"] >= 0
    assert stats["xslg_per"] >= 0


def test_practice_game_team_override(monkeypatch):
    csv_data = (
        "Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League\n"
        "Alice,TeamA,Walk,InPlay,Out,95,25,10,Left,1.5,0.5,0,150,Team"
    )
    buffer = make_csv(csv_data)

    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.5)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", lambda h, s: True)

    result = mod.get_advanced_batting_stats_from_buffer(buffer, "file.csv")
    key = ("Alice", "AUB_PRC", 2025)
    assert key in result
    stats = result[key]
    assert stats["BatterTeam"] == "AUB_PRC"


def test_infield_slices():
    csv_data = """Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League
John,AUB,,InPlay,Out,95,15,5,Right,2,0,-30,150,SEC
John,AUB,,InPlay,Out,95,15,5,Right,2,0,-20,150,SEC
John,AUB,,InPlay,Out,95,15,5,Right,2,0,0,150,SEC
John,AUB,,InPlay,Out,95,15,5,Right,2,0,10,150,SEC
John,AUB,,InPlay,Out,95,15,5,Right,2,0,30,150,SEC
"""
    buffer = make_csv(csv_data)
    filename = "sample_2025.csv"

    result = mod.get_advanced_batting_stats_from_buffer(buffer, filename)
    key = ("John", "AUB", 2025)
    stats = result[key]

    # Each slice should have one ball
    assert stats["infield_left_slice"] == 1
    assert stats["infield_lc_slice"] == 1
    assert stats["infield_center_slice"] == 1
    assert stats["infield_rc_slice"] == 1
    assert stats["infield_right_slice"] == 1

    # Percentages should all be 0.2
    assert stats["infield_left_per"] == 0.2
    assert stats["infield_lc_per"] == 0.2
    assert stats["infield_center_per"] == 0.2
    assert stats["infield_rc_per"] == 0.2
    assert stats["infield_right_per"] == 0.2


def test_infield_slices_with_invalid_values():
    csv_data = """Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League
John,AUB,,InPlay,Out,95,15,5,Right,2,0,invalid,150,SEC
John,AUB,,InPlay,Out,95,15,5,Right,2,0,30,invalid,SEC
John,AUB,,InPlay,Out,95,15,5,Right,2,0,50,150,SEC
"""
    buffer = make_csv(csv_data)
    filename = "sample_2025.csv"

    result = mod.get_advanced_batting_stats_from_buffer(buffer, filename)
    key = ("John", "AUB", 2025)
    stats = result[key]

    # Only the valid row (Bearing=50) is out of all slices (>45) → all slices should be 0
    assert stats["infield_left_slice"] == 0
    assert stats["infield_lc_slice"] == 0
    assert stats["infield_center_slice"] == 0
    assert stats["infield_rc_slice"] == 0
    assert stats["infield_right_slice"] == 0

    # Percentages should all be None since total_infield_batted_balls == 0
    assert stats["infield_left_per"] is None
    assert stats["infield_lc_per"] is None
    assert stats["infield_center_per"] is None
    assert stats["infield_rc_per"] is None
    assert stats["infield_right_per"] is None


def test_in_out_of_zone_counts():
    csv_data = f"""Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League
John,AUB,Walk,StrikeSwinging,Out,95,15,5,Right,2.0,0.0,0,250,SEC
John,AUB,Strikeout,InPlay,Out,95,15,5,Right,4.0,2.0,0,250,SEC
John,AUB,Walk,FoulBallNotFieldable,Out,95,15,5,Right,5.0,3.0,0,250,SEC
"""
    buffer = make_csv(csv_data)
    filename = "sample_2025.csv"

    result = mod.get_advanced_batting_stats_from_buffer(buffer, filename)

    key = ("John", "AUB", 2025)
    stats = result[key]

    # First row: in-zone StrikeSwinging → in_zone_pitches=1, in_zone_whiffs=1
    # Second row: out-of-zone InPlay → out_of_zone_pitches=1, out_of_zone_swings=1
    # Third row: out-of-zone FoulBallNotFieldable → out_of_zone_pitches=2, out_of_zone_swings=2

    # Expected calculations based on your test CSV

    assert stats["in_zone_pitches"] == 1
    assert stats["out_of_zone_pitches"] == 2

    # in_zone_whiffs / in_zone_pitches = 1/1 = 1.0
    # out_of_zone_swings / out_of_zone_pitches = 2/2 = 1.0

    assert stats["whiff_per"] == 1.0
    assert stats["chase_per"] == 1.0


def test_batter_xba_else_branch():
    # All rows are either not InPlay or missing required batted ball columns
    csv_data = """Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League
John,AUB,Walk,StrikeSwinging,Out,,,,,Right,2,0,0,250,SEC
John,AUB,Walk,HitByPitch,Out,,,,,Left,2,0,0,250,SEC
"""
    buffer = make_csv(csv_data)
    filename = "sample_2025.csv"

    result = mod.get_advanced_batting_stats_from_buffer(buffer, filename)
    key = ("John", "AUB", 2025)
    stats = result[key]

    # Since there are no valid batted balls, batter_xba should be 0
    assert stats["xba_per"] == 0


def test_xwoba_except_branch(monkeypatch, capsys):
    # Minimal CSV with a valid InPlay batted ball
    csv_data = """Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League
John,AUB,,InPlay,Out,95,15,5,Right,2,0,0,250,SEC
"""
    buffer = make_csv(csv_data)
    filename = "sample_2025.csv"

    # Patch xwoba_model to raise an exception when predict is called
    class FailingModel:
        def predict(self, df):
            raise RuntimeError("forced failure")

    monkeypatch.setattr(mod, "xwoba_model", FailingModel())

    # Run function
    result = mod.get_advanced_batting_stats_from_buffer(buffer, filename)
    key = ("John", "AUB", 2025)
    stats = result[key]

    # Should catch exception and set xwoba_per to 0
    assert stats["xwoba_per"] == 0

    # Check that the error was printed
    captured = capsys.readouterr()
    assert "Error computing xwOBA for John" in captured.out
    assert "forced failure" in captured.out


def test_combine_basic_stats():
    existing = {
        "Batter": "John Doe",
        "BatterTeam": "AAA",
        "Year": 2025,
        "plate_app": 50,
        "batted_balls": 40,
        "at_bats": 45,
        "avg_exit_velo": 90.0,
        "k_per": 0.2,
        "bb_per": 0.1,
        "la_sweet_spot_per": 0.3,
        "hard_hit_per": 0.4,
        "in_zone_pitches": 30,
        "whiff_per": 0.15,
        "out_of_zone_pitches": 20,
        "chase_per": 0.25,
        "infield_left_slice": 5,
        "infield_lc_slice": 5,
        "infield_center_slice": 10,
        "infield_rc_slice": 10,
        "infield_right_slice": 10,
        "xba_per": 0.28,
        "xslg_per": 0.45,
        "xwoba_per": 0.32,
        "barrel_per": 0.05,
    }

    new = {
        "Batter": "John Doe",
        "BatterTeam": "AAA",
        "Year": 2025,
        "plate_app": 30,
        "batted_balls": 20,
        "at_bats": 25,
        "avg_exit_velo": 95.0,
        "k_per": 0.1,
        "bb_per": 0.15,
        "la_sweet_spot_per": 0.25,
        "hard_hit_per": 0.5,
        "in_zone_pitches": 15,
        "whiff_per": 0.2,
        "out_of_zone_pitches": 10,
        "chase_per": 0.3,
        "infield_left_slice": 2,
        "infield_lc_slice": 3,
        "infield_center_slice": 5,
        "infield_rc_slice": 5,
        "infield_right_slice": 5,
        "xba_per": 0.3,
        "xslg_per": 0.5,
        "xwoba_per": 0.35,
        "barrel_per": 0.08,
    }

    combined = mod.combine_advanced_batting_stats(existing, new)

    # Totals
    assert combined["plate_app"] == 80
    assert combined["batted_balls"] == 60
    assert combined["at_bats"] == 70
    assert combined["in_zone_pitches"] == 45
    assert combined["out_of_zone_pitches"] == 30

    # Weighted averages
    assert combined["avg_exit_velo"] == pytest.approx((90 * 40 + 95 * 20) / 60)
    assert combined["k_per"] == pytest.approx((0.2 * 50 + 0.1 * 30) / 80)
    assert combined["bb_per"] == pytest.approx((0.1 * 50 + 0.15 * 30) / 80)
    assert combined["la_sweet_spot_per"] == pytest.approx((0.3 * 40 + 0.25 * 20) / 60)
    assert combined["hard_hit_per"] == pytest.approx((0.4 * 40 + 0.5 * 20) / 60)
    assert combined["whiff_per"] == pytest.approx((0.15 * 30 + 0.2 * 15) / 45)
    assert combined["chase_per"] == pytest.approx((0.25 * 20 + 0.3 * 10) / 30)
    assert combined["xba_per"] == pytest.approx((0.28 * 45 + 0.3 * 25) / 70)
    assert combined["xslg_per"] == pytest.approx((0.45 * 45 + 0.5 * 25) / 70)
    assert combined["xwoba_per"] == pytest.approx((0.32 * 50 + 0.35 * 30) / 80)
    assert combined["barrel_per"] == pytest.approx((0.05 * 40 + 0.08 * 20) / 60)

    # Infield slices
    total_infield = sum([5, 5, 10, 10, 10, 2, 3, 5, 5, 5])
    assert combined["infield_left_per"] == pytest.approx((5 + 2) / total_infield)
    assert combined["infield_lc_per"] == pytest.approx((5 + 3) / total_infield)
    assert combined["infield_center_per"] == pytest.approx((10 + 5) / total_infield)
    assert combined["infield_rc_per"] == pytest.approx((10 + 5) / total_infield)
    assert combined["infield_right_per"] == pytest.approx((10 + 5) / total_infield)


def test_combine_empty_existing():
    new = {
        "Batter": "Jane Doe",
        "BatterTeam": "BBB",
        "Year": 2025,
        "plate_app": 10,
        "batted_balls": 5,
        "at_bats": 8,
        "avg_exit_velo": 85.0,
        "k_per": 0.25,
        "bb_per": 0.05,
        "la_sweet_spot_per": 0.2,
        "hard_hit_per": 0.3,
        "in_zone_pitches": 6,
        "whiff_per": 0.1,
        "out_of_zone_pitches": 4,
        "chase_per": 0.15,
        "infield_left_slice": 1,
        "infield_lc_slice": 1,
        "infield_center_slice": 2,
        "infield_rc_slice": 2,
        "infield_right_slice": 2,
        "xba_per": 0.22,
        "xslg_per": 0.33,
        "xwoba_per": 0.28,
        "barrel_per": 0.02,
    }

    combined = mod.combine_advanced_batting_stats({}, new)
    assert combined == new


def test_combine_with_none_and_zeros():
    existing = {
        "Batter": "Player",
        "BatterTeam": "CCC",
        "Year": 2025,
        "plate_app": None,
        "batted_balls": 0,
        "at_bats": None,
        "avg_exit_velo": None,
        "k_per": None,
        "bb_per": None,
        "la_sweet_spot_per": None,
        "hard_hit_per": None,
        "in_zone_pitches": 0,
        "whiff_per": None,
        "out_of_zone_pitches": 0,
        "chase_per": None,
        "infield_left_slice": 0,
        "infield_lc_slice": 0,
        "infield_center_slice": 0,
        "infield_rc_slice": 0,
        "infield_right_slice": 0,
        "xba_per": None,
        "xslg_per": None,
        "xwoba_per": None,
        "barrel_per": None,
    }

    new = {
        "Batter": "Player",
        "BatterTeam": "CCC",
        "Year": 2025,
        "plate_app": 10,
        "batted_balls": 5,
        "at_bats": 8,
        "avg_exit_velo": 80.0,
        "k_per": 0.2,
        "bb_per": 0.1,
        "la_sweet_spot_per": 0.25,
        "hard_hit_per": 0.3,
        "in_zone_pitches": 5,
        "whiff_per": 0.15,
        "out_of_zone_pitches": 3,
        "chase_per": 0.2,
        "infield_left_slice": 1,
        "infield_lc_slice": 1,
        "infield_center_slice": 1,
        "infield_rc_slice": 1,
        "infield_right_slice": 1,
        "xba_per": 0.3,
        "xslg_per": 0.4,
        "xwoba_per": 0.35,
        "barrel_per": 0.05,
    }

    combined = mod.combine_advanced_batting_stats(existing, new)
    assert combined["plate_app"] == 10
    assert combined["batted_balls"] == 5
    assert combined["at_bats"] == 8
    assert combined["avg_exit_velo"] == 80.0


def test_weighted_avg_returns_none_when_zero_total_weight():
    existing_stats = {"stat": 10, "weight": 0}
    new_stats = {"stat": 20, "weight": 0}

    total_weight = 0  # triggers the None branch

    result = mod.weighted_avg(existing_stats, new_stats, "stat", "weight", total_weight)

    assert result is None


# Minimal test data
batters_dict = {
    ("Player1", "TeamA", 2025): {
        "Batter": "Player1",
        "BatterTeam": "TeamA",
        "Year": 2025,
        "avg_exit_velo": np.float64(88.5),
        "k_per": np.float64(20.3),
        "unique_games": 10,
    }
}


def test_upload_calls_upsert():
    table_mock = MagicMock()
    table_mock.select.return_value.range.return_value.execute.return_value.data = []
    table_mock.upsert.return_value.execute.return_value = None
    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(batters_dict)

    assert supabase_mock.table().upsert.called, "Expected upsert() to be called"


# Sample data
NEW_BATTER = {
    ("Player1", "TeamA", 2025): {
        "Batter": "Player1",
        "BatterTeam": "TeamA",
        "Year": 2025,
        "avg_exit_velo": np.float64(88.5),
        "k_per": np.float64(20.3),
        "bb_per": np.float64(10.0),
        "la_sweet_spot_per": np.float64(15.0),
        "hard_hit_per": np.float64(25.0),
        "whiff_per": np.float64(5.0),
        "chase_per": np.float64(3.0),
        "xba_per": np.float64(0.300),
        "xslg_per": np.float64(0.450),
        "xwoba_per": np.float64(0.320),
        "barrel_per": np.float64(2.0),
        "unique_games": 10,
    }
}

EXISTING_BATTER = {
    ("Player2", "TeamB", 2025): {
        "Batter": "Player2",
        "BatterTeam": "TeamB",
        "Year": 2025,
        "avg_exit_velo": np.float64(90.0),
        "k_per": np.float64(18.0),
        "bb_per": np.float64(12.0),
        "la_sweet_spot_per": np.float64(14.0),
        "hard_hit_per": np.float64(20.0),
        "whiff_per": np.float64(6.0),
        "chase_per": np.float64(4.0),
        "xba_per": np.float64(0.310),
        "xslg_per": np.float64(0.470),
        "xwoba_per": np.float64(0.330),
        "barrel_per": np.float64(3.0),
        "unique_games": 12,
    }
}


# Helper: mock combine function
def mock_combine(existing, new):
    combined = existing.copy()
    combined.update(new)
    return combined


@pytest.fixture
def mock_supabase_fast():
    """Minimal supabase mock that avoids infinite loops in fetch"""
    table_mock = MagicMock()

    # Mock fetch: return empty list first to break loop
    fetch_mock = MagicMock()
    fetch_mock.data = []  # ensures while loop exits immediately
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    # Mock upsert: returns mock with execute()
    upsert_mock = MagicMock()
    upsert_mock.execute.return_value = None
    table_mock.upsert.return_value = upsert_mock

    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock
    return supabase_mock, table_mock


def test_no_input_supabase(monkeypatch):
    """If batters_dict is empty, function exits early"""
    supabase_mock = MagicMock()
    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        result = mod.upload_advanced_batting_to_supabase({})
        assert result is None


def test_upsert_called_for_new_batter(mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast
    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(NEW_BATTER)
    assert table_mock.upsert.called, "Expected upsert() to be called for new batters"


def test_combines_existing_batter(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    # simulate fetching existing record
    existing_fetch = MagicMock()
    existing_fetch.data = [EXISTING_BATTER[("Player2", "TeamB", 2025)]]
    table_mock.select.return_value.range.return_value.execute.return_value = existing_fetch

    monkeypatch.setattr(
        "scripts.utils.advanced_batting_stats_upload.combine_advanced_batting_stats", mock_combine
    )

    batters_dict = {
        ("Player2", "TeamB", 2025): {
            "Batter": "Player2",
            "BatterTeam": "TeamB",
            "Year": 2025,
            "avg_exit_velo": np.float64(91.0),
        }
    }

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    assert table_mock.upsert.called, "Expected upsert() to be called for combined records"


def test_rank_upload_called(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    # simulate existing records for ranking
    records = [
        NEW_BATTER[("Player1", "TeamA", 2025)],
        EXISTING_BATTER[("Player2", "TeamB", 2025)],
    ]
    rank_fetch = MagicMock()
    rank_fetch.data = records
    table_mock.select.return_value.range.return_value.execute.return_value = rank_fetch

    monkeypatch.setattr(
        "scripts.utils.advanced_batting_stats_upload.combine_advanced_batting_stats", mock_combine
    )

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(
            {**NEW_BATTER, **EXISTING_BATTER}, max_fetch_loops=1
        )

    # upsert should be called at least twice (raw + rank)
    assert table_mock.upsert.call_count >= 2, "Expected upsert() to be called for ranking updates"


def test_rank_helper_all_nan(monkeypatch):
    import numpy as np
    from pandas import Series

    # Patch supabase client
    table_mock = MagicMock()
    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    # Patch fetch for ranking to return records with all NaNs for metrics
    execute_mock = MagicMock()
    execute_mock.data = [
        {
            "Batter": "PlayerX",
            "BatterTeam": "TeamX",
            "Year": 2025,
            "avg_exit_velo": np.nan,
            "k_per": np.nan,
            "bb_per": np.nan,
            "la_sweet_spot_per": np.nan,
            "hard_hit_per": np.nan,
            "whiff_per": np.nan,
            "chase_per": np.nan,
            "xba_per": np.nan,
            "xslg_per": np.nan,
            "xwoba_per": np.nan,
            "barrel_per": np.nan,
        }
    ]
    table_mock.select.return_value.range.return_value.execute.return_value = execute_mock

    monkeypatch.setattr("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock)

    # Provide a minimal batters_dict so function proceeds to ranking
    batters_dict = {
        ("PlayerX", "TeamX", 2025): {
            "Batter": "PlayerX",
            "BatterTeam": "TeamX",
            "Year": 2025,
            "avg_exit_velo": np.nan,
            "k_per": np.nan,
            "bb_per": np.nan,
            "la_sweet_spot_per": np.nan,
            "hard_hit_per": np.nan,
            "whiff_per": np.nan,
            "chase_per": np.nan,
            "xba_per": np.nan,
            "xslg_per": np.nan,
            "xwoba_per": np.nan,
            "barrel_per": np.nan,
            "unique_games": 1,
        }
    }

    # Call function (max_fetch_loops=1 to prevent infinite loop)
    mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    # upsert should be called for rank updates even if all NaNs
    assert table_mock.upsert.called, "Expected upsert() to be called even with all NaN metrics"


def test_upsert_exception_handled(monkeypatch):
    # Patch supabase client and table
    table_mock = MagicMock()
    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    # Patch select().range().execute() to return empty list so function proceeds to upload
    execute_mock = MagicMock()
    execute_mock.data = []
    table_mock.select.return_value.range.return_value.execute.return_value = execute_mock

    # Patch upsert().execute() to raise an exception
    def raise_exception(*args, **kwargs):
        raise ValueError("Simulated upsert error")

    table_mock.upsert.return_value.execute.side_effect = raise_exception

    # Provide a minimal batters_dict to trigger the upload loop
    batters_dict = {
        ("Player1", "TeamA", 2025): {
            "Batter": "Player1",
            "BatterTeam": "TeamA",
            "Year": 2025,
            "avg_exit_velo": 88.5,
            "k_per": 20.0,
            "bb_per": 10.0,
            "la_sweet_spot_per": 15.0,
            "hard_hit_per": 25.0,
            "whiff_per": 5.0,
            "chase_per": 3.0,
            "xba_per": 0.3,
            "xslg_per": 0.45,
            "xwoba_per": 0.32,
            "barrel_per": 2.0,
            "unique_games": 10,
        }
    }

    # Patch the supabase in the actual module
    monkeypatch.setattr("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock)

    # Call the function (max_fetch_loops=1 to avoid infinite loop)
    mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    # upsert was called and exception was handled
    assert table_mock.upsert.called


def test_rank_upsert_exception(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    # Simulate records that will be ranked
    records = [
        {**NEW_BATTER[("Player1", "TeamA", 2025)]},
    ]
    table_mock.select.return_value.range.return_value.execute.return_value.data = records

    # Patch combine function (even though not needed for new batter)
    monkeypatch.setattr(
        "scripts.utils.advanced_batting_stats_upload.combine_advanced_batting_stats", mock_combine
    )

    # Make upsert().execute() raise an exception
    def raise_error(*args, **kwargs):
        raise RuntimeError("Test exception during upsert")

    table_mock.upsert.return_value.execute.side_effect = raise_error

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(NEW_BATTER, max_fetch_loops=1)

    # Check that upsert was called (it tried)
    assert table_mock.upsert.called, "Expected upsert() to be attempted even if it raises"


def test_outer_try_exception(monkeypatch):
    # Create a supabase mock that will raise an exception immediately
    supabase_mock = MagicMock()
    supabase_mock.table.side_effect = RuntimeError("Test outer exception")

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        # Call with some data, it doesn't matter what, the exception happens first
        mod.upload_advanced_batting_to_supabase(NEW_BATTER, max_fetch_loops=1)

    # If needed, you can capture stdout to check the print
    # Example:
    # with capsys.disabled():  # or capsys to capture
    #     mod.upload_advanced_batting_to_supabase(NEW_BATTER)
