"""
Author: Joshua Reed
Created: 1 November 2025
Updated: 4 November 2025

Unit test cases for advanced_batting_stats_upload.py functions.
"""

import builtins
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from scripts.utils import advanced_batting_stats_upload as mod


def test_xba_grid_missing(tmp_path):
    path = tmp_path / "missing.csv"
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


@pytest.mark.parametrize(
    "lst,value,expected",
    [
        ([1, 3, 5, 7], 5, 5),
        ([1, 3, 5, 7], 1, 1),
        ([1, 3, 5, 7], 7, 7),
        ([1, 3, 6, 10], 4, 3),
        ([1, 3, 6, 10], 7, 6),
        ([10, 20, 30], 5, 10),
        ([10, 20, 30], 35, 30),
        ([1, 3, 5, 7], 4, 3),
    ],
)
def test_closest_value(lst, value, expected):
    assert mod.closest_value(lst, value) == expected


def _setup_xba_lookup(monkeypatch, test_dict, ev_bins, la_bins, dir_bins, global_xba_mean=0.35):
    monkeypatch.setattr(mod, "xba_dict", test_dict)
    monkeypatch.setattr(mod, "ev_bins", ev_bins)
    monkeypatch.setattr(mod, "la_bins", la_bins)
    monkeypatch.setattr(mod, "dir_bins", dir_bins)
    monkeypatch.setattr(mod, "global_xba_mean", global_xba_mean)


def test_lookup_xBA_exact_match(monkeypatch):
    _setup_xba_lookup(monkeypatch, {(80, 20, 1): 0.3, (85, 25, 2): 0.4}, [80, 85], [20, 25], [1, 2])
    assert mod.lookup_xBA(80, 20, 1) == 0.3
    assert mod.lookup_xBA(85, 25, 2) == 0.4


def test_lookup_xBA_3D_average(monkeypatch):
    _setup_xba_lookup(
        monkeypatch,
        {(80, 20, 1): 0.3, (81, 21, 1): 0.4, (79, 19, 6): 0.5},
        [79, 80, 81],
        [19, 20, 21],
        [1, 6],
    )
    val = mod.lookup_xBA(80, 20, 3)
    assert abs(val - (0.3 + 0.4 + 0.5) / 3) < 1e-6


def test_lookup_xBA_nearest_neighbor(monkeypatch):
    _setup_xba_lookup(monkeypatch, {(80, 20, 1): 0.3, (85, 25, 2): 0.5}, [80, 85], [20, 25], [1, 2])
    assert mod.lookup_xBA(81, 19, 3) == 0.35


def test_lookup_xBA_empty_dict(monkeypatch):
    _setup_xba_lookup(monkeypatch, {}, [80, 85], [20, 25], [1, 2])
    assert mod.lookup_xBA(100, 100, 50) == 0.35


@pytest.mark.parametrize(
    "load_function,model_filename",
    [
        (mod.load_xslg_model, "xslg_model.json"),
        (mod.load_xwoba_model, "xwoba_model.json"),
    ],
)
def test_load_model_success(tmp_path, monkeypatch, load_function, model_filename):
    model_file = tmp_path / model_filename
    model_file.write_text("{}")

    mock_regressor = MagicMock()
    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: mock_regressor)
    mock_regressor.load_model = MagicMock()

    result = load_function(model_file)

    assert result is mock_regressor
    mock_regressor.load_model.assert_called_once_with(str(model_file))


@pytest.mark.parametrize(
    "load_function",
    [mod.load_xslg_model, mod.load_xwoba_model],
)
def test_load_model_path_not_exist(monkeypatch, load_function):
    fake_path = Path("/does/not/exist.json")
    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: None)

    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = load_function(fake_path)

    assert result is None
    assert any("not found" in msg for msg in printed)


@pytest.mark.parametrize(
    "load_function,model_filename",
    [
        (mod.load_xslg_model, "xslg_model.json"),
        (mod.load_xwoba_model, "xwoba_model.json"),
    ],
)
def test_load_model_load_fail(tmp_path, monkeypatch, load_function, model_filename):
    model_file = tmp_path / model_filename
    model_file.write_text("{}")

    class FakeRegressor:
        def load_model(self, path):
            raise ValueError("fake load error")

    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: FakeRegressor())
    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = load_function(model_file)
    assert isinstance(result, FakeRegressor)
    assert any("Failed to load" in msg for msg in printed)


class DummyParser:
    def get_date_components(self, filename):
        if filename == "bad_filename.csv":
            return None
        return (2025, 5, 20)


@pytest.fixture(autouse=True)
def patch_csv_parser(monkeypatch):
    monkeypatch.setattr(mod, "CSVFilenameParser", lambda: DummyParser())


def make_csv(data: str):
    """Helper to create buffer from CSV string."""
    return io.StringIO(data)


def test_missing_required_columns_returns_empty(monkeypatch, capsys):
    csv_data = "Batter,KorBB\nJohnDoe,Walk"
    buffer = make_csv(csv_data)

    result = mod.get_advanced_batting_stats_from_buffer(buffer, "file.csv")

    assert result == {}
    captured = capsys.readouterr()
    assert "Error processing" in captured.out


def test_empty_csv(monkeypatch):
    csv_data = "Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League\n"
    buffer = make_csv(csv_data)
    result = mod.get_advanced_batting_stats_from_buffer(buffer, "file.csv")
    assert result == {}


def test_bad_filename(monkeypatch):
    csv_data = "Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League\nJohnDoe,DoeTeam,Walk,InPlay,Out,90,20,10,Left,1.5,0.5,30,150,College"
    buffer = make_csv(csv_data)

    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = mod.get_advanced_batting_stats_from_buffer(buffer, "bad_filename.csv")
    assert result == {}
    assert any("Unable to extract date from filename" in msg for msg in printed)


def _setup_stats_mocks(monkeypatch, xba_value=0.4):
    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: xba_value)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", lambda h, s: True)


def test_regular_game_stats(monkeypatch):
    csv_data = (
        "Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League\n"
        "JohnDoe,DoeTeam,Walk,,,,NaN,NaN,NaN,Left,NaN,NaN,NaN,NaN,College\n"
        "JohnDoe,DoeTeam,,InPlay,Out,95,25,10,Right,1.5,0.5,0,150,College\n"
        "JohnDoe,DoeTeam,Strikeout,,,,NaN,NaN,NaN,Left,NaN,NaN,NaN,NaN,College"
    )
    buffer = make_csv(csv_data)
    _setup_stats_mocks(monkeypatch)

    result = mod.get_advanced_batting_stats_from_buffer(buffer, "file_2025.csv")
    key = ("JohnDoe", "DoeTeam", 2025)
    assert key in result
    stats = result[key]

    assert stats["plate_app"] == 3
    assert stats["at_bats"] == 2
    assert stats["batted_balls"] == 1
    assert stats["k_per"] == pytest.approx(1 / 3, rel=1e-3)
    assert stats["bb_per"] == pytest.approx(1 / 3, rel=1e-3)
    assert stats["xba_per"] >= 0
    assert stats["xslg_per"] >= 0


def test_practice_game_team_override(monkeypatch):
    csv_data = (
        "Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League\n"
        "Alice,AUB_TIG,Walk,InPlay,Out,95,25,10,Left,1.5,0.5,0,150,Team"
    )
    buffer = make_csv(csv_data)
    _setup_stats_mocks(monkeypatch, xba_value=0.5)

    result = mod.get_advanced_batting_stats_from_buffer(buffer, "file.csv")
    key = ("Alice", "AUB_PRC", 2025)
    assert key in result
    assert result[key]["BatterTeam"] == "AUB_PRC"


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

    assert stats["infield_left_slice"] == 1
    assert stats["infield_lc_slice"] == 1
    assert stats["infield_center_slice"] == 1
    assert stats["infield_rc_slice"] == 1
    assert stats["infield_right_slice"] == 1
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

    assert stats["infield_left_slice"] == 0
    assert stats["infield_lc_slice"] == 0
    assert stats["infield_center_slice"] == 0
    assert stats["infield_rc_slice"] == 0
    assert stats["infield_right_slice"] == 0
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

    assert stats["in_zone_pitches"] == 1
    assert stats["out_of_zone_pitches"] == 2
    assert stats["whiff_per"] == 1.0
    assert stats["chase_per"] == 1.0


def test_batter_xba_else_branch():
    csv_data = """Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League
John,AUB,Walk,StrikeSwinging,Out,,,,,Right,2,0,0,250,SEC
John,AUB,Walk,HitByPitch,Out,,,,,Left,2,0,0,250,SEC
"""
    buffer = make_csv(csv_data)
    filename = "sample_2025.csv"

    result = mod.get_advanced_batting_stats_from_buffer(buffer, filename)
    key = ("John", "AUB", 2025)
    stats = result[key]

    assert stats["xba_per"] == 0


def test_xwoba_except_branch(monkeypatch, capsys):
    csv_data = """Batter,BatterTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,PlateLocHeight,PlateLocSide,Bearing,Distance,League
John,AUB,,InPlay,Out,95,15,5,Right,2,0,0,250,SEC
"""
    buffer = make_csv(csv_data)
    filename = "sample_2025.csv"

    class FailingModel:
        def predict(self, df):
            raise RuntimeError("forced failure")

    monkeypatch.setattr(mod, "xwoba_model", FailingModel())

    result = mod.get_advanced_batting_stats_from_buffer(buffer, filename)
    key = ("John", "AUB", 2025)
    stats = result[key]

    assert stats["xwoba_per"] == 0
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

    assert combined["plate_app"] == 80
    assert combined["batted_balls"] == 60
    assert combined["at_bats"] == 70
    assert combined["in_zone_pitches"] == 45
    assert combined["out_of_zone_pitches"] == 30
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
    total_weight = 0

    result = mod.weighted_avg(existing_stats, new_stats, "stat", "weight", total_weight)

    assert result is None


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

    assert supabase_mock.table().upsert.called


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


def mock_combine(existing, new):
    combined = existing.copy()
    combined.update(new)
    return combined


def _create_supabase_mock(fetch_data=None, upsert_side_effect=None):
    """Helper to create a Supabase mock with configurable fetch and upsert behavior."""
    table_mock = MagicMock()
    fetch_mock = MagicMock()
    fetch_mock.data = fetch_data if fetch_data is not None else []
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    upsert_mock = MagicMock()
    if upsert_side_effect:
        upsert_mock.execute.side_effect = upsert_side_effect
    else:
        upsert_mock.execute.return_value = None
    table_mock.upsert.return_value = upsert_mock

    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock
    return supabase_mock, table_mock


@pytest.fixture
def mock_supabase_fast():
    """Fixture providing a minimal Supabase mock that prevents infinite loops."""
    return _create_supabase_mock()


def test_no_input_supabase(monkeypatch):
    supabase_mock = MagicMock()
    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        result = mod.upload_advanced_batting_to_supabase({})
        assert result is None


def test_upsert_called_for_new_batter(mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast
    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(NEW_BATTER)
    assert table_mock.upsert.called


def test_combines_existing_batter(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    existing_fetch = MagicMock()
    existing_fetch.data = [EXISTING_BATTER[("Player2", "TeamB", 2025)]]
    table_mock.select.return_value.range.return_value.execute.return_value = existing_fetch

    monkeypatch.setattr(
        "scripts.utils.advanced_batting_stats_upload.combine_advanced_batting_stats",
        mock_combine,
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

    assert table_mock.upsert.called


def test_rank_upload_called(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    records = [
        NEW_BATTER[("Player1", "TeamA", 2025)],
        EXISTING_BATTER[("Player2", "TeamB", 2025)],
    ]
    rank_fetch = MagicMock()
    rank_fetch.data = records
    table_mock.select.return_value.range.return_value.execute.return_value = rank_fetch

    monkeypatch.setattr(
        "scripts.utils.advanced_batting_stats_upload.combine_advanced_batting_stats",
        mock_combine,
    )

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(
            {**NEW_BATTER, **EXISTING_BATTER}, max_fetch_loops=1
        )

    assert table_mock.upsert.call_count >= 2


def test_rank_helper_all_nan(monkeypatch):
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
    supabase_mock, table_mock = _create_supabase_mock()
    table_mock.select.return_value.range.return_value.execute.return_value = execute_mock

    monkeypatch.setattr("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock)

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

    mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)
    assert table_mock.upsert.called


def test_upsert_exception_handled(monkeypatch):
    def raise_exception(*args, **kwargs):
        raise ValueError("Simulated upsert error")

    supabase_mock, table_mock = _create_supabase_mock(upsert_side_effect=raise_exception)

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

    monkeypatch.setattr("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock)
    mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)
    assert table_mock.upsert.called


def test_rank_upsert_exception(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    records = [
        {**NEW_BATTER[("Player1", "TeamA", 2025)]},
    ]
    table_mock.select.return_value.range.return_value.execute.return_value.data = records

    monkeypatch.setattr(
        "scripts.utils.advanced_batting_stats_upload.combine_advanced_batting_stats",
        mock_combine,
    )

    def raise_error(*args, **kwargs):
        raise RuntimeError("Test exception during upsert")

    table_mock.upsert.return_value.execute.side_effect = raise_error

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(NEW_BATTER, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_outer_try_exception(monkeypatch):
    supabase_mock = MagicMock()
    supabase_mock.table.side_effect = RuntimeError("Test outer exception")

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(NEW_BATTER, max_fetch_loops=1)


def test_rank_team_group_continue_branch(monkeypatch):
    fetch_data = [{"Batter": "Y", "BatterTeam": "AUB", "Year": 2025, "avg_exit_velo": 88.0}]
    supabase_mock, table_mock = _create_supabase_mock(fetch_data=fetch_data)

    batters_dict = {
        ("Y", "AUB", 2025): {
            "Batter": "Y",
            "BatterTeam": "AUB",
            "Year": 2025,
            "avg_exit_velo": 88.0,
            "unique_games": 1,
        }
    }

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_full_rank_paths_batting(monkeypatch):
    records = [
        {
            "Batter": "A",
            "BatterTeam": "AUB",
            "Year": 2025,
            "League": "SEC",
            "Level": "DI",
            "avg_exit_velo": 90.0,
            "k_per": 0.2,
            "bb_per": 0.1,
            "la_sweet_spot_per": 0.3,
            "hard_hit_per": 0.4,
            "whiff_per": 0.15,
            "chase_per": 0.25,
            "xba_per": 0.28,
            "xslg_per": 0.45,
            "xwoba_per": 0.32,
            "barrel_per": 0.05,
        },
        {
            "Batter": "B",
            "BatterTeam": "BAMA",
            "Year": 2025,
            "League": "SEC",
            "Level": "DI",
            "avg_exit_velo": 92.0,
            "k_per": 0.1,
            "bb_per": 0.12,
            "la_sweet_spot_per": 0.25,
            "hard_hit_per": 0.35,
            "whiff_per": 0.1,
            "chase_per": 0.2,
            "xba_per": 0.3,
            "xslg_per": 0.5,
            "xwoba_per": 0.35,
            "barrel_per": 0.08,
        },
        {
            "Batter": "C",
            "BatterTeam": "AUB_PRC",
            "Year": 2025,
            "League": "TEAM",
            "Level": "DI",
            "avg_exit_velo": 85.0,
            "k_per": 0.25,
            "bb_per": 0.08,
            "la_sweet_spot_per": 0.2,
            "hard_hit_per": 0.3,
            "whiff_per": 0.2,
            "chase_per": 0.3,
            "xba_per": 0.22,
            "xslg_per": 0.33,
            "xwoba_per": 0.28,
            "barrel_per": 0.02,
        },
        {
            "Batter": "D",
            "BatterTeam": "AUB_PRC",
            "Year": 2025,
            "League": "TEAM",
            "Level": "DI",
            "avg_exit_velo": 88.0,
            "k_per": 0.22,
            "bb_per": 0.09,
            "la_sweet_spot_per": 0.22,
            "hard_hit_per": 0.31,
            "whiff_per": 0.19,
            "chase_per": 0.28,
            "xba_per": 0.24,
            "xslg_per": 0.36,
            "xwoba_per": 0.3,
            "barrel_per": 0.03,
        },
    ]

    supabase_mock, table_mock = _create_supabase_mock(fetch_data=records)

    batters_dict = {
        ("A", "AUB", 2025): {
            "Batter": "A",
            "BatterTeam": "AUB",
            "Year": 2025,
            "avg_exit_velo": 90.0,
            "unique_games": 1,
        }
    }

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_league_group_continue_only_batting(monkeypatch):
    fetch_data = [
        {
            "Batter": "LC",
            "BatterTeam": "AUB_PRC",
            "Year": 2025,
            "Level": None,
            "League": "SEC",
            "avg_exit_velo": 90.0,
            "k_per": 0.2,
            "bb_per": 0.1,
            "la_sweet_spot_per": 0.3,
            "hard_hit_per": 0.4,
            "whiff_per": 0.15,
            "chase_per": 0.25,
            "xba_per": 0.28,
            "xslg_per": 0.45,
            "xwoba_per": 0.32,
            "barrel_per": 0.05,
        }
    ]
    supabase_mock, table_mock = _create_supabase_mock(fetch_data=fetch_data)

    batters_dict = {
        ("LC", "AUB_PRC", 2025): {
            "Batter": "LC",
            "BatterTeam": "AUB_PRC",
            "Year": 2025,
            "avg_exit_velo": 90.0,
        }
    }

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_overall_ranks_continue_all_practice_batting(monkeypatch):
    fetch_data = [
        {
            "Batter": "P1",
            "BatterTeam": "AUB_PRC",
            "Year": 2025,
            "avg_exit_velo": 90.0,
            "k_per": 0.2,
            "bb_per": 0.1,
            "la_sweet_spot_per": 0.3,
            "hard_hit_per": 0.4,
            "whiff_per": 0.15,
            "chase_per": 0.25,
            "xba_per": 0.28,
            "xslg_per": 0.45,
            "xwoba_per": 0.32,
            "barrel_per": 0.05,
        }
    ]
    supabase_mock, table_mock = _create_supabase_mock(fetch_data=fetch_data)

    batters_dict = {
        ("P1", "AUB_PRC", 2025): {
            "Batter": "P1",
            "BatterTeam": "AUB_PRC",
            "Year": 2025,
            "avg_exit_velo": 90.0,
        }
    }

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_team_ranks_continue_all_practice_batting(monkeypatch):
    def execute_side_effect():
        result = MagicMock()
        result.data = [
            {
                "Batter": "P1",
                "BatterTeam": "AUB_PRC",
                "Year": 2025,
                "avg_exit_velo": 90.0,
                "k_per": 0.2,
                "bb_per": 0.1,
                "la_sweet_spot_per": 0.3,
                "hard_hit_per": 0.4,
                "whiff_per": 0.15,
                "chase_per": 0.25,
                "xba_per": 0.28,
                "xslg_per": 0.45,
                "xwoba_per": 0.32,
                "barrel_per": 0.05,
            }
        ]
        return result

    fetch_data = [
        {
            "Batter": "P1",
            "BatterTeam": "AUB",
            "Year": 2025,
            "avg_exit_velo": 90.0,
            "k_per": 0.2,
            "bb_per": 0.1,
            "la_sweet_spot_per": 0.3,
            "hard_hit_per": 0.4,
            "whiff_per": 0.15,
            "chase_per": 0.25,
            "xba_per": 0.28,
            "xslg_per": 0.45,
            "xwoba_per": 0.32,
            "barrel_per": 0.05,
        }
    ]
    supabase_mock, table_mock = _create_supabase_mock(fetch_data=fetch_data)
    table_mock.select.return_value.range.return_value.execute.side_effect = execute_side_effect

    batters_dict = {
        ("P1", "AUB", 2025): {
            "Batter": "P1",
            "BatterTeam": "AUB",
            "Year": 2025,
            "avg_exit_velo": 90.0,
        }
    }

    with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_team_ranks_continue_empty_mask(monkeypatch):
    """Tests that team ranking continues when mask is empty after filtering."""
    fetch_data = [
        {
            "Batter": "P1",
            "BatterTeam": "AUB_PRC",
            "Year": 2025,
            "avg_exit_velo": 90.0,
            "k_per": 0.2,
            "bb_per": 0.1,
            "la_sweet_spot_per": 0.3,
            "hard_hit_per": 0.4,
            "whiff_per": 0.15,
            "chase_per": 0.25,
            "xba_per": 0.28,
            "xslg_per": 0.45,
            "xwoba_per": 0.32,
            "barrel_per": 0.05,
        }
    ]
    supabase_mock, table_mock = _create_supabase_mock(fetch_data=fetch_data)

    batters_dict = {
        ("P1", "AUB_PRC", 2025): {
            "Batter": "P1",
            "BatterTeam": "AUB_PRC",
            "Year": 2025,
            "avg_exit_velo": 90.0,
        }
    }

    original_eq = pd.Series.eq

    def patched_eq(self, other):
        result = original_eq(self, other)
        if other == "AUB_PRC":
            return pd.Series([False] * len(self), index=self.index)
        return result

    with patch.object(pd.Series, "eq", patched_eq):
        with patch("scripts.utils.advanced_batting_stats_upload.supabase", supabase_mock):
            mod.upload_advanced_batting_to_supabase(batters_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


@pytest.mark.parametrize(
    "practice_value,non_practice_series",
    [
        (float("nan"), [10, 20, 30]),
        (10.0, [None, np.nan, float("nan")]),
    ],
)
def test_calculate_practice_overall_rank_returns_none(practice_value, non_practice_series):
    """Tests that function returns None for edge cases."""
    series = pd.Series(non_practice_series)
    result = mod.calculate_practice_overall_rank(practice_value, series)
    assert result is None


def test_calculate_practice_overall_rank_all_values_same():
    """Tests that function returns 100.0 when all non-practice values are identical."""
    non_practice_series = pd.Series([10, 10, 10, 10])
    result = mod.calculate_practice_overall_rank(10.0, non_practice_series)
    assert result == 100.0


def test_calculate_practice_overall_rank_practice_better_than_all_ascending_true():
    """Tests that function returns 100.0 when practice value is best with ascending=True."""
    non_practice_series = pd.Series([10, 20, 30])
    result = mod.calculate_practice_overall_rank(5.0, non_practice_series, ascending=True)
    assert result == 100.0


def test_calculate_practice_overall_rank_practice_better_than_all_ascending_false():
    """Tests ranking behavior when practice value is worst with ascending=False."""
    non_practice_series = pd.Series([10, 20, 30])
    result = mod.calculate_practice_overall_rank(5.0, non_practice_series, ascending=False)
    assert result == 1.0


def test_calculate_practice_overall_rank_scaling_formula():
    """Tests the scaling formula for various edge cases."""
    non_practice_series = pd.Series([10, 20, 30, 40, 50])
    practice_value = 25.0

    result = mod.calculate_practice_overall_rank(
        practice_value, non_practice_series, ascending=True
    )

    assert result is not None
    assert 1.0 <= result <= 100.0
    assert isinstance(result, float)

    non_practice_series2 = pd.Series([10, 20, 30, 40, 50])
    practice_value2 = 10.0
    result2 = mod.calculate_practice_overall_rank(
        practice_value2, non_practice_series2, ascending=True
    )
    assert result2 == 100.0

    non_practice_series3 = pd.Series([10, 20, 30, 40, 50])
    practice_value3 = 49.0
    result3 = mod.calculate_practice_overall_rank(
        practice_value3, non_practice_series3, ascending=True
    )
    assert result3 >= 1.0
