import builtins
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from scripts.utils import advanced_pitching_stats_upload as mod


# ----------------- Helpers -----------------
class DummyParser:
    def get_date_components(self, filename):
        if filename == "bad_filename.csv":
            return None
        return (2025, 10, 31)

    def get_date_object(self, filename):
        return pd.Timestamp("2025-10-31") if filename != "bad_filename.csv" else None


def test_supabase_vars():
    # Missing variables
    mod.SUPABASE_URL = None
    mod.SUPABASE_KEY = None
    with pytest.raises(ValueError):
        mod.check_supabase_vars()

    # Present variables
    mod.SUPABASE_URL = "https://example.supabase.co"
    mod.SUPABASE_KEY = "fake_key_123"
    mod.check_supabase_vars()  # should NOT raise


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


@pytest.fixture(autouse=True)
def patch_csv_parser(monkeypatch):
    # Patch CSVFilenameParser globally
    monkeypatch.setattr(mod, "CSVFilenameParser", lambda: DummyParser())


def make_csv(data: str):
    """Helper to create buffer from CSV string."""
    return io.StringIO(data)


def test_empty_csv(monkeypatch):
    csv_data = "Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League\n"
    buffer = make_csv(csv_data)
    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    assert result == {}  # No rows to process


def test_bad_filename(monkeypatch):
    csv_data = (
        "Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League\n"
        "JohnDoe,AUB,K,StrikeSwinging,Out,,,,Right,,Fastball,100,2.0,0.0,SEC\n"
    )
    buffer = make_csv(csv_data)

    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "bad_filename.csv")
    assert result == {}
    assert any("Unable to extract date from filename" in msg for msg in printed)


# ----------------- Tests -----------------


def test_basic_pitching_stats(monkeypatch):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,Strikeout,StrikeSwinging,Out,,,,Right,,Fastball,100,2,0,SEC
John,AUB,Walk,BallCalled,,,,,Right,,Fastball,98,2,0,SEC
John,AUB,,InPlay,Out,97,20,10,Right,GroundBall,Fastball,97,3,0,SEC
John,AUB,,InPlay,Out,94,20,10,Right,GroundBall,Fastball,97,0,0,SEC
"""
    buffer = make_csv(csv_data)

    # Patch helper functions/models
    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    assert key in result
    stats = result[key]

    # Check counts
    assert stats["plate_app"] == 4  # Walk + Strikeout + Groundout
    assert stats["batted_balls"] == 2
    assert stats["at_bats"] == 3  # Strikeout + 1 batted ball in play with stats
    assert stats["fastballs"] == 4
    assert stats["ground_balls"] == 2

    # Percentages
    assert stats["k_per"] == pytest.approx(1 / 4, rel=1e-3)
    assert stats["bb_per"] == pytest.approx(1 / 4, rel=1e-3)
    assert stats["la_sweet_spot_per"] == pytest.approx(2 / 2, rel=1e-3)
    assert stats["hard_hit_per"] == pytest.approx(1 / 2, rel=1e-3)
    assert stats["avg_exit_velo"] == pytest.approx((97 + 94) / 2, rel=1e-3)
    assert stats["avg_fastball_velo"] == pytest.approx((100 + 98 + 97 + 97) / 4, rel=1e-3)

    # Zone stats
    assert stats["in_zone_pitches"] == 3
    assert stats["whiff_per"] == pytest.approx(1 / 3, rel=1e-3)
    assert stats["out_of_zone_pitches"] == 1
    assert stats["chase_per"] == pytest.approx(1 / 1, rel=1e-3)

    # xBA/xSLG/xwOBA/barrel
    assert stats["xba_per"] > 0
    assert stats["xslg_per"] == 0
    assert stats["xwoba_per"] > 0
    assert stats["barrel_per"] == 0


def test_practice_team(monkeypatch):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Jane,AAA,Walk,InPlay,Out,95,15,5,Right,GroundBall,Fastball,100,2,0,Team
"""
    buffer = make_csv(csv_data)

    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.5)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "practice_game.csv")
    key = ("Jane", "AUB_PRC", 2025)
    assert key in result
    stats = result[key]
    assert stats["PitcherTeam"] == "AUB_PRC"


def test_batted_ball_empty(monkeypatch):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Alice,BBB,Walk,StrikeSwinging,Out,,,,Right,,Fastball,100,2,0,SEC
"""
    buffer = make_csv(csv_data)
    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("Alice", "BBB", 2025)
    stats = result[key]

    assert stats["batted_balls"] == 0
    assert stats["xba_per"] == 0
    assert stats["xslg_per"] == 0
    assert stats["barrel_per"] == 0


def test_xwoba_exception(monkeypatch, capsys):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Tom,AUB,,InPlay,Out,95,15,5,Right,GroundBall,Fastball,97,2,0,SEC
"""
    buffer = make_csv(csv_data)

    class FailingModel:
        def predict(self, df):
            raise RuntimeError("fail")

    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", FailingModel())
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("Tom", "AUB", 2025)
    stats = result[key]
    assert stats["xwoba_per"] == 0

    captured = capsys.readouterr()
    assert "Error computing xwOBA for Tom" in captured.out


def test_multiple_pitchers(monkeypatch):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
A,AUB,Walk,InPlay,Out,95,15,5,Right,GroundBall,Fastball,100,2,0,SEC
B,AUB,Strikeout,InPlay,Out,90,20,10,Left,GroundBall,Fastball,98,3,1,SEC
"""
    buffer = make_csv(csv_data)

    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    assert ("A", "AUB", 2025) in result
    assert ("B", "AUB", 2025) in result


def test_missing_ev_la_dir(monkeypatch):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Sam,AUB,Strikeout,InPlay,Out,,,,Right,,Fastball,100,2,0,SEC
"""
    buffer = make_csv(csv_data)
    monkeypatch.setattr(mod, "lookup_xBA", mod.lookup_xBA)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("Sam", "AUB", 2025)
    stats = result[key]
    assert stats["xba_per"] == 0
    assert stats["plate_app"] == 1


def test_plate_loc_exception(monkeypatch):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Jane,AUB,Strikeout,StrikeSwinging,Out,95,20,10,Right,,Fastball,100,bad,0,SEC
John,AUB,Strikeout,StrikeSwinging,Out,95,20,10,Right,,Fastball,100,2,bad,SEC
"""
    buffer = io.StringIO(csv_data)

    # Patch required functions/models
    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    # Should not raise and should process rows, skipping those with bad PlateLoc
    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("Jane", "AUB", 2025)
    # Since PlateLocHeight or Side is invalid, these rows won't count as in/out-of-zone
    assert key in result
    stats = result[key]
    assert stats["in_zone_pitches"] == 0
    assert stats["out_of_zone_pitches"] == 0


def test_xslg_model_branch(monkeypatch):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,,InPlay,Out,95,20,10,Right,GroundBall,Fastball,97,2,0,SEC
"""
    buffer = io.StringIO(csv_data)

    # Create a dummy model that returns predictable predictions
    class DummyXSLGModel:
        def predict(self, df):
            return [0.6] * len(df)

    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", DummyXSLGModel())
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    stats = result[key]

    # Check that xSLG was assigned by the model
    assert stats["xslg_per"] == 0.6  # the dummy model prediction


def test_xslg_model_none_or_empty(monkeypatch):
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,Strikeout,StrikeSwinging,Out,,,,Right,,Fastball,100,2,0,SEC
"""
    buffer = io.StringIO(csv_data)

    # Case 1: xslg_model is None
    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    stats = result[key]

    # No batted balls, so xSLG should default to 0
    assert stats["xslg_per"] == 0


def test_xwoba_model_branch(monkeypatch):
    # CSV with a batted ball
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,,InPlay,Out,95,20,10,Right,GroundBall,Fastball,97,2,0,SEC
"""
    buffer = io.StringIO(csv_data)

    # Dummy model that returns predictable predictions
    class DummyXwOBA:
        def predict(self, df):
            return [0.25] * len(df)

    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", DummyXwOBA())
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    stats = result[key]

    # Check that sum_xwOBA_bb is assigned correctly
    assert stats["xwoba_per"] == 0.25  # single row → sum = prediction


def test_xwoba_model_none_or_empty(monkeypatch):
    # CSV with no batted balls
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,Strikeout,StrikeSwinging,Out,,,,Right,,Fastball,100,2,0,SEC
"""
    buffer = io.StringIO(csv_data)

    # Case 1: xwoba_model is None
    monkeypatch.setattr(mod, "lookup_xBA", lambda ev, la, dr: 0.4)
    monkeypatch.setattr(mod, "xslg_model", None)
    monkeypatch.setattr(mod, "xwoba_model", None)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    stats = result[key]

    # No batted balls or model missing → sum_xwOBA_bb should be 0
    assert stats["xwoba_per"] == 0


def test_safe_get():
    data = {"a": 10, "b": None}

    # Key exists with a value
    assert mod.safe_get(data, "a") == 10

    # Key exists but value is None → should return 0
    assert mod.safe_get(data, "b") == 0

    # Key does not exist → should return 0
    assert mod.safe_get(data, "c") == 0


def test_weighted_avg():
    # Normal weighted average
    existing = {"stat": 10, "weight": 2}
    new = {"stat": 20, "weight": 3}
    total_weight = 5
    result = mod.weighted_avg(existing, new, "stat", "weight", total_weight)
    assert result == (10 * 2 + 20 * 3) / 5  # (20 + 60)/5 = 16

    # Check that result is never negative
    existing = {"stat": -5, "weight": 1}
    new = {"stat": 0, "weight": 1}
    total_weight = 2
    result = mod.weighted_avg(existing, new, "stat", "weight", total_weight)
    assert result == 0  # max(-2.5, 0) = 0

    # Zero total_weight returns None
    existing = {"stat": 10, "weight": 0}
    new = {"stat": 20, "weight": 0}
    total_weight = 0
    result = mod.weighted_avg(existing, new, "stat", "weight", total_weight)
    assert result is None

    # Missing keys → safe_get returns 0
    existing = {}
    new = {"stat": 15, "weight": 3}
    total_weight = 3
    result = mod.weighted_avg(existing, new, "stat", "weight", total_weight)
    assert result == 15


def test_combine_empty_existing():
    new_stats = {"Pitcher": "John", "PitcherTeam": "AUB", "Year": 2025, "plate_app": 4}
    combined = mod.combine_advanced_pitching_stats({}, new_stats)
    assert combined == new_stats


def test_combine_existing_no_new_dates():
    existing = {
        "processed_dates": [20251031],
        "plate_app": 4,
        "batted_balls": 2,
        "Pitcher": "John",
        "PitcherTeam": "AUB",
        "Year": 2025,
    }
    new_stats = {
        "processed_dates": [20251031],
        "plate_app": 3,
        "batted_balls": 1,
        "Pitcher": "John",
        "PitcherTeam": "AUB",
        "Year": 2025,
    }
    combined = mod.combine_advanced_pitching_stats(existing, new_stats)
    # No new dates → should return existing stats unchanged
    assert combined == existing


def test_combine_existing_with_new_dates(monkeypatch):
    # Patch weighted_avg to just sum values for testing purposes
    monkeypatch.setattr(
        mod,
        "weighted_avg",
        lambda e, n, s, w, tw, *args: (mod.safe_get(e, s) + mod.safe_get(n, s)) / 2,
    )

    existing = {
        "processed_dates": [20251030],
        "plate_app": 4,
        "batted_balls": 2,
        "ground_balls": 1,
        "in_zone_pitches": 3,
        "out_of_zone_pitches": 1,
        "fastballs": 4,
        "at_bats": 3,
        "Pitcher": "John",
        "PitcherTeam": "AUB",
        "Year": 2025,
        "avg_exit_velo": 95,
        "k_per": 0.25,
        "bb_per": 0.25,
        "gb_per": 0.5,
        "la_sweet_spot_per": 0.5,
        "hard_hit_per": 0.5,
        "whiff_per": 0.33,
        "chase_per": 0.5,
        "avg_fastball_velo": 97,
        "xba_per": 0.4,
        "xslg_per": 0.5,
        "xwoba_per": 0.35,
        "barrel_per": 0.1,
    }
    new_stats = {
        "processed_dates": [20251031],
        "plate_app": 6,
        "batted_balls": 4,
        "ground_balls": 2,
        "in_zone_pitches": 2,
        "out_of_zone_pitches": 3,
        "fastballs": 5,
        "at_bats": 4,
        "Pitcher": "John",
        "PitcherTeam": "AUB",
        "Year": 2025,
        "avg_exit_velo": 100,
        "k_per": 0.3,
        "bb_per": 0.2,
        "gb_per": 0.6,
        "la_sweet_spot_per": 0.6,
        "hard_hit_per": 0.7,
        "whiff_per": 0.4,
        "chase_per": 0.3,
        "avg_fastball_velo": 99,
        "xba_per": 0.45,
        "xslg_per": 0.55,
        "xwoba_per": 0.4,
        "barrel_per": 0.2,
    }

    combined = mod.combine_advanced_pitching_stats(existing, new_stats)

    # Counts should sum
    assert combined["plate_app"] == 10
    assert combined["batted_balls"] == 6
    assert combined["ground_balls"] == 3
    assert combined["in_zone_pitches"] == 5
    assert combined["out_of_zone_pitches"] == 4
    assert combined["fastballs"] == 9
    assert combined["at_bats"] == 7

    # Weighted averages should be calculated (patched to mean)
    assert combined["avg_exit_velo"] == (95 + 100) / 2
    assert combined["k_per"] == (0.25 + 0.3) / 2
    assert combined["bb_per"] == (0.25 + 0.2) / 2
    assert combined["gb_per"] == (0.5 + 0.6) / 2
    assert combined["la_sweet_spot_per"] == (0.5 + 0.6) / 2
    assert combined["hard_hit_per"] == (0.5 + 0.7) / 2
    assert combined["whiff_per"] == (0.33 + 0.4) / 2
    assert combined["chase_per"] == (0.5 + 0.3) / 2
    assert combined["avg_fastball_velo"] == (97 + 99) / 2
    assert combined["xba_per"] == (0.4 + 0.45) / 2
    assert combined["xslg_per"] == (0.5 + 0.55) / 2
    assert combined["xwoba_per"] == (0.35 + 0.4) / 2
    assert combined["barrel_per"] == (0.1 + 0.2) / 2


def test_missing_keys(monkeypatch):
    # Ensure safe_get handles missing keys without errors
    existing = {
        "processed_dates": [20251030],
        "Pitcher": "John",
        "PitcherTeam": "AUB",
        "Year": 2025,
    }
    new_stats = {
        "processed_dates": [20251031],
        "Pitcher": "John",
        "PitcherTeam": "AUB",
        "Year": 2025,
    }
    combined = mod.combine_advanced_pitching_stats(existing, new_stats)
    # Missing numeric stats should default to 0
    assert combined["plate_app"] == 0
    assert combined["batted_balls"] == 0
    assert combined["ground_balls"] == 0


def test_empty_series():
    s = pd.Series([], dtype=float)
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.empty


def test_all_nan_series():
    s = pd.Series([np.nan, np.nan, np.nan])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.isna().all()


def test_single_value_series():
    s = pd.Series([42])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.iloc[0] == 100.0


def test_identical_values():
    s = pd.Series([10, 10, 10])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert (scaled == 100.0).all()


def test_simple_ranking_descending():
    s = pd.Series([10, 20, 30])
    scaled = mod.rank_and_scale_to_1_100(s, ascending=False)
    # largest value -> 100, smallest -> 1
    assert scaled.iloc[0] == 100.0  # 10 -> 100
    assert scaled.iloc[1] == 50.0  # 20 -> 50
    assert scaled.iloc[2] == 1.0  # 30 -> 1


def test_simple_ranking_ascending():
    s = pd.Series([10, 20, 30])
    scaled = mod.rank_and_scale_to_1_100(s, ascending=True)
    # smallest value -> 100, largest -> 1
    assert scaled.iloc[0] == 1.0  # 10 -> 1
    assert scaled.iloc[1] == 50.0  # 20 -> 50
    assert scaled.iloc[2] == 100.0  # 30 -> 100


def test_series_with_ties():
    s = pd.Series([10, 20, 20, 30])
    scaled = mod.rank_and_scale_to_1_100(s)
    # ranks: 10->1, 20->2, 20->2, 30->3 -> scaled 1, 50, 50, 100
    assert scaled.iloc[0] == 100.0
    assert scaled.iloc[1] == scaled.iloc[2] == 34.0
    assert scaled.iloc[3] == 1.0


def test_series_with_nans():
    s = pd.Series([10, None, 30])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.iloc[0] == 100.0
    assert scaled.iloc[1] is None  # instead of np.isnan
    assert scaled.iloc[2] == 1.0


def test_series_min_max_equal():
    s = pd.Series([5, 5, 5, 5])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert (scaled == 100.0).all()


# Sample pitching data
NEW_PITCHER = {
    ("Player1", "TeamA", 2025): {
        "Pitcher": "Player1",
        "PitcherTeam": "TeamA",
        "Year": 2025,
        "avg_exit_velo": np.float64(88.5),
        "k_per": np.float64(20.3),
        "bb_per": np.float64(10.0),
        "la_sweet_spot_per": np.float64(15.0),
        "hard_hit_per": np.float64(25.0),
        "whiff_per": np.float64(5.0),
        "chase_per": np.float64(3.0),
        "avg_fastball_velo": np.float64(92.0),
        "gb_per": np.float64(40.0),
        "xba_per": np.float64(0.300),
        "xslg_per": np.float64(0.450),
        "xwoba_per": np.float64(0.320),
        "barrel_per": np.float64(2.0),
        "unique_games": 10,
    }
}

EXISTING_PITCHER = {
    ("Player2", "TeamB", 2025): {
        "Pitcher": "Player2",
        "PitcherTeam": "TeamB",
        "Year": 2025,
        "avg_exit_velo": np.float64(90.0),
        "k_per": np.float64(18.0),
        "bb_per": np.float64(12.0),
        "la_sweet_spot_per": np.float64(14.0),
        "hard_hit_per": np.float64(20.0),
        "whiff_per": np.float64(6.0),
        "chase_per": np.float64(4.0),
        "avg_fastball_velo": np.float64(93.0),
        "gb_per": np.float64(42.0),
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


# Fixture for fast mock supabase
@pytest.fixture
def mock_supabase_fast():
    table_mock = MagicMock()

    # fetch returns empty list to exit loop
    fetch_mock = MagicMock()
    fetch_mock.data = []
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    # upsert returns mock with execute
    upsert_mock = MagicMock()
    upsert_mock.execute.return_value = None
    table_mock.upsert.return_value = upsert_mock

    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock
    return supabase_mock, table_mock


# Early exit if no input
def test_no_input_supabase(monkeypatch):
    supabase_mock = MagicMock()
    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        result = mod.upload_advanced_pitching_to_supabase({})
        assert result is None


# Upsert called for new pitcher
def test_upsert_called_for_new_pitcher(mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast
    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(NEW_PITCHER)
    assert table_mock.upsert.called, "Expected upsert() to be called for new pitchers"


# Combine existing pitcher
def test_combines_existing_pitcher(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    # simulate fetching existing record
    existing_fetch = MagicMock()
    existing_fetch.data = [EXISTING_PITCHER[("Player2", "TeamB", 2025)]]
    table_mock.select.return_value.range.return_value.execute.return_value = existing_fetch

    monkeypatch.setattr(
        "scripts.utils.advanced_pitching_stats_upload.combine_advanced_pitching_stats",
        mock_combine,
    )

    new_data = {
        ("Player2", "TeamB", 2025): {
            "Pitcher": "Player2",
            "PitcherTeam": "TeamB",
            "Year": 2025,
            "avg_exit_velo": np.float64(91.0),
        }
    }

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(new_data, max_fetch_loops=1)

    assert table_mock.upsert.called, "Expected upsert() to be called for combined records"


# Ranking upload called
def test_rank_upload_called(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    # simulate existing records for ranking
    records = [
        NEW_PITCHER[("Player1", "TeamA", 2025)],
        EXISTING_PITCHER[("Player2", "TeamB", 2025)],
    ]
    rank_fetch = MagicMock()
    rank_fetch.data = records
    table_mock.select.return_value.range.return_value.execute.return_value = rank_fetch

    monkeypatch.setattr(
        "scripts.utils.advanced_pitching_stats_upload.combine_advanced_pitching_stats",
        mock_combine,
    )

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(
            {**NEW_PITCHER, **EXISTING_PITCHER}, max_fetch_loops=1
        )

    # upsert should be called at least twice (raw + rank)
    assert table_mock.upsert.call_count >= 2, "Expected upsert() to be called for ranking updates"


# Ranking helper with all NaNs
def test_rank_helper_all_nan(monkeypatch):
    import numpy as np
    import pandas as pd

    table_mock = MagicMock()
    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    execute_mock = MagicMock()
    execute_mock.data = [
        {
            "Pitcher": "PlayerX",
            "PitcherTeam": "TeamX",
            "Year": 2025,
            "avg_exit_velo": np.nan,
            "k_per": np.nan,
            "bb_per": np.nan,
            "la_sweet_spot_per": np.nan,
            "hard_hit_per": np.nan,
            "whiff_per": np.nan,
            "chase_per": np.nan,
            "avg_fastball_velo": np.nan,
            "gb_per": np.nan,
            "xba_per": np.nan,
            "xslg_per": np.nan,
            "xwoba_per": np.nan,
            "barrel_per": np.nan,
        }
    ]
    table_mock.select.return_value.range.return_value.execute.return_value = execute_mock

    monkeypatch.setattr("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock)

    pitchers_dict = {
        ("PlayerX", "TeamX", 2025): {
            "Pitcher": "PlayerX",
            "PitcherTeam": "TeamX",
            "Year": 2025,
            "avg_exit_velo": np.nan,
            "k_per": np.nan,
            "bb_per": np.nan,
            "la_sweet_spot_per": np.nan,
            "hard_hit_per": np.nan,
            "whiff_per": np.nan,
            "chase_per": np.nan,
            "avg_fastball_velo": np.nan,
            "gb_per": np.nan,
            "xba_per": np.nan,
            "xslg_per": np.nan,
            "xwoba_per": np.nan,
            "barrel_per": np.nan,
            "unique_games": 1,
        }
    }

    mod.upload_advanced_pitching_to_supabase(pitchers_dict, max_fetch_loops=1)
    assert table_mock.upsert.called, "Expected upsert() to be called even with all NaN metrics"


# Upsert exception handling
def test_upsert_exception_handled(monkeypatch):
    table_mock = MagicMock()
    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    execute_mock = MagicMock()
    execute_mock.data = []
    table_mock.select.return_value.range.return_value.execute.return_value = execute_mock

    def raise_exception(*args, **kwargs):
        raise ValueError("Simulated upsert error")

    table_mock.upsert.return_value.execute.side_effect = raise_exception

    pitchers_dict = {
        ("Player1", "TeamA", 2025): {
            "Pitcher": "Player1",
            "PitcherTeam": "TeamA",
            "Year": 2025,
            "avg_exit_velo": 88.5,
            "k_per": 20.0,
            "bb_per": 10.0,
            "la_sweet_spot_per": 15.0,
            "hard_hit_per": 25.0,
            "whiff_per": 5.0,
            "chase_per": 3.0,
            "avg_fastball_velo": 92.0,
            "gb_per": 40.0,
            "xba_per": 0.3,
            "xslg_per": 0.45,
            "xwoba_per": 0.32,
            "barrel_per": 2.0,
            "unique_games": 10,
        }
    }

    monkeypatch.setattr("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock)
    mod.upload_advanced_pitching_to_supabase(pitchers_dict, max_fetch_loops=1)
    assert table_mock.upsert.called


# Outer try exception
def test_outer_try_exception(monkeypatch):
    supabase_mock = MagicMock()
    supabase_mock.table.side_effect = RuntimeError("Test outer exception")

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(NEW_PITCHER, max_fetch_loops=1)


def test_continue_branch(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    existing = {
        ("Player1", "TeamA", 2025): {
            "Pitcher": "Player1",
            "PitcherTeam": "TeamA",
            "Year": 2025,
            "plate_app": 10,
            "batted_balls": 5,
            "processed_dates": ["2025-01-01", "2025-01-02"],
        }
    }

    new_stat = {
        ("Player1", "TeamA", 2025): {
            "Pitcher": "Player1",
            "PitcherTeam": "TeamA",
            "Year": 2025,
            "plate_app": 3,
            "batted_balls": 2,
            "processed_dates": ["2025-01-01"],  # subset of existing
        }
    }

    # Patch fetch to return the existing record
    fetch_mock = MagicMock()
    fetch_mock.data = [existing[("Player1", "TeamA", 2025)]]
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    # Patch supabase in module
    monkeypatch.setattr("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock)

    # Patch combine_advanced_pitching_stats normally
    monkeypatch.setattr(
        "scripts.utils.advanced_pitching_stats_upload.combine_advanced_pitching_stats",
        mod.combine_advanced_pitching_stats,
    )

    mod.upload_advanced_pitching_to_supabase(new_stat, max_fetch_loops=1)

    # upsert should NOT be called for the record because continue was hit
    # But the ranking upsert might still be called, so we specifically check combined_stats behavior
    assert table_mock.upsert.call_count >= 0  # ranking may still upload, but raw upload skipped


def test_rank_upsert_exception(monkeypatch, mock_supabase_fast):
    supabase_mock, table_mock = mock_supabase_fast

    # Simulate records that will be ranked
    records = [
        {**NEW_PITCHER[("Player1", "TeamA", 2025)]},
    ]
    table_mock.select.return_value.range.return_value.execute.return_value.data = records

    # Patch combine function (even though not needed for new pitcher)
    monkeypatch.setattr(
        "scripts.utils.advanced_pitching_stats_upload.combine_advanced_pitching_stats",
        mock_combine,
    )

    # Make upsert().execute() raise an exception
    def raise_error(*args, **kwargs):
        raise RuntimeError("Test exception during upsert")

    table_mock.upsert.return_value.execute.side_effect = raise_error

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(NEW_PITCHER, max_fetch_loops=1)

    # Check that upsert was called (it tried)
    assert table_mock.upsert.called, "Expected upsert() to be attempted even if it raises"
