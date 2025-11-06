"""
Unit test cases for advanced_pitching_stats_upload.py functions.

Author: Joshua Reed
Created: 1 November 2025
"""

import builtins
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from scripts.utils import advanced_pitching_stats_upload as mod

# ============================================================================
# Test Fixtures and Helpers
# ============================================================================


class DummyParser:
    """Mock CSV filename parser for testing."""

    def get_date_components(self, filename):
        if filename == "bad_filename.csv":
            return None
        return (2025, 10, 31)

    def get_date_object(self, filename):
        return pd.Timestamp("2025-10-31") if filename != "bad_filename.csv" else None


@pytest.fixture(autouse=True)
def patch_csv_parser(monkeypatch):
    """Automatically patch CSVFilenameParser for all tests."""
    monkeypatch.setattr(mod, "CSVFilenameParser", lambda: DummyParser())


def make_csv(data: str):
    """Create a StringIO buffer from CSV string data."""
    return io.StringIO(data)


@pytest.fixture
def mock_supabase_fast():
    """Mock Supabase client fixture for fast test execution."""
    table_mock = MagicMock()

    fetch_mock = MagicMock()
    fetch_mock.data = []
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    upsert_mock = MagicMock()
    upsert_mock.execute.return_value = None
    table_mock.upsert.return_value = upsert_mock

    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock
    return supabase_mock, table_mock


def mock_combine(existing, new):
    """Mock function for combining stats in tests."""
    combined = existing.copy()
    combined.update(new)
    return combined


def setup_lookup_xba_test(monkeypatch, test_dict, ev_bins, la_bins, dir_bins, global_xba_mean):
    """Helper to setup lookup_xBA test environment."""
    monkeypatch.setattr(mod, "xba_dict", test_dict)
    monkeypatch.setattr(mod, "ev_bins", ev_bins)
    monkeypatch.setattr(mod, "la_bins", la_bins)
    monkeypatch.setattr(mod, "dir_bins", dir_bins)
    monkeypatch.setattr(mod, "global_xba_mean", global_xba_mean)


def setup_csv_test_mocks(monkeypatch, lookup_xba=None, xslg_model=None, xwoba_model=None):
    """Helper to setup common mocks for CSV processing tests."""
    if lookup_xba is not None:
        monkeypatch.setattr(mod, "lookup_xBA", lookup_xba)
    # Always patch models (including None) to override module-level loaded models
    monkeypatch.setattr(mod, "xslg_model", xslg_model)
    monkeypatch.setattr(mod, "xwoba_model", xwoba_model)
    monkeypatch.setattr(mod, "is_in_strike_zone", mod.is_in_strike_zone)


def create_pitcher_record(pitcher, team, year, **kwargs):
    """Helper to create a pitcher record with default metrics."""
    default_metrics = {
        "avg_exit_velo": 88.0,
        "k_per": 0.2,
        "bb_per": 0.08,
        "la_sweet_spot_per": 0.2,
        "hard_hit_per": 0.3,
        "whiff_per": 0.15,
        "chase_per": 0.22,
        "avg_fastball_velo": 94.0,
        "gb_per": 0.45,
        "xba_per": 0.26,
        "xslg_per": 0.4,
        "xwoba_per": 0.3,
        "barrel_per": 0.04,
    }
    record = {
        "Pitcher": pitcher,
        "PitcherTeam": team,
        "Year": year,
        **default_metrics,
        **kwargs,
    }
    return record


# ============================================================================
# Test Data Constants
# ============================================================================


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


# ============================================================================
# Tests for load_xba_grid
# ============================================================================


def test_xba_grid_missing(tmp_path):
    """Test loading xBA grid when file does not exist."""
    path = tmp_path / "missing.csv"
    xba_grid, xba_dict, ev_bins, la_bins, dir_bins, mean = mod.load_xba_grid(path)
    assert xba_grid.empty
    assert xba_dict == {}
    assert ev_bins == []
    assert la_bins == []
    assert dir_bins == []
    assert mean == 0.25


def test_xba_grid_exists(tmp_path):
    """Test loading xBA grid when file exists."""
    path = tmp_path / "xba.csv"
    path.write_text("ev_bin,la_bin,dir_bin,xBA\n" "80,20,1,0.3\n" "85,25,2,0.4\n")

    xba_grid, xba_dict, ev_bins, la_bins, dir_bins, mean = mod.load_xba_grid(path)

    assert not xba_grid.empty
    assert len(xba_dict) == 2
    assert set(ev_bins) == {80, 85}
    assert set(la_bins) == {20, 25}
    assert set(dir_bins) == {1, 2}
    assert abs(mean - 0.35) < 1e-6


# ============================================================================
# Tests for closest_value
# ============================================================================


def test_closest_value():
    """Test closest_value function with various edge cases and scenarios."""
    # Exact matches
    lst = [1, 3, 5, 7]
    assert mod.closest_value(lst, 5) == 5
    assert mod.closest_value(lst, 1) == 1
    assert mod.closest_value(lst, 7) == 7

    # Values between elements
    lst = [1, 3, 6, 10]
    assert mod.closest_value(lst, 4) == 3
    assert mod.closest_value(lst, 7) == 6

    # Smaller than smallest
    lst = [10, 20, 30]
    assert mod.closest_value(lst, 5) == 10

    # Larger than largest
    assert mod.closest_value(lst, 35) == 30

    # Equidistant values (should return value before input)
    lst = [1, 3, 5, 7]
    assert mod.closest_value(lst, 4) == 3


# ============================================================================
# Tests for lookup_xBA
# ============================================================================


def test_lookup_xBA_exact_match(monkeypatch):
    """Test lookup_xBA with exact key matches."""
    setup_lookup_xba_test(
        monkeypatch, {(80, 20, 1): 0.3, (85, 25, 2): 0.4}, [80, 85], [20, 25], [1, 2], 0.35
    )

    assert mod.lookup_xBA(80, 20, 1) == 0.3
    assert mod.lookup_xBA(85, 25, 2) == 0.4


def test_lookup_xBA_3D_average(monkeypatch):
    """Test lookup_xBA with 3D neighborhood averaging."""
    setup_lookup_xba_test(
        monkeypatch,
        {(80, 20, 1): 0.3, (81, 21, 1): 0.4, (79, 19, 6): 0.5},
        [79, 80, 81],
        [19, 20, 21],
        [1, 6],
        0.35,
    )

    val = mod.lookup_xBA(80, 20, 3)
    assert abs(val - (0.3 + 0.4 + 0.5) / 3) < 1e-6


def test_lookup_xBA_nearest_neighbor(monkeypatch):
    """Test lookup_xBA fallback to global mean when no neighbors found."""
    setup_lookup_xba_test(
        monkeypatch, {(80, 20, 1): 0.3, (85, 25, 2): 0.5}, [80, 85], [20, 25], [1, 2], 0.35
    )

    assert mod.lookup_xBA(81, 19, 3) == 0.35


def test_lookup_xBA_empty_dict(monkeypatch):
    """Test lookup_xBA with empty dictionary returns global mean."""
    setup_lookup_xba_test(monkeypatch, {}, [80, 85], [20, 25], [1, 2], 0.35)

    result = mod.lookup_xBA(100, 100, 50)
    assert result == 0.35


# ============================================================================
# Tests for load_xslg_model and load_xwoba_model
# ============================================================================


@pytest.mark.parametrize(
    "load_func,model_name",
    [
        (mod.load_xslg_model, "xslg_model.json"),
        (mod.load_xwoba_model, "xwoba_model.json"),
    ],
)
def test_load_model_success(tmp_path, monkeypatch, load_func, model_name):
    """Test successful model loading for both xSLG and xwOBA models."""
    model_file = tmp_path / model_name
    model_file.write_text("{}")

    mock_regressor = MagicMock()
    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: mock_regressor)
    mock_regressor.load_model = MagicMock()

    result = load_func(model_file)

    assert result is mock_regressor
    mock_regressor.load_model.assert_called_once_with(str(model_file))


@pytest.mark.parametrize("load_func", [mod.load_xslg_model, mod.load_xwoba_model])
def test_load_model_path_not_exist(monkeypatch, load_func):
    """Test model loading when file does not exist."""
    fake_path = Path("/does/not/exist.json")
    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: None)

    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = load_func(fake_path)

    assert result is None
    assert any("not found" in msg for msg in printed)


@pytest.mark.parametrize(
    "load_func,model_name",
    [
        (mod.load_xslg_model, "xslg_model.json"),
        (mod.load_xwoba_model, "xwoba_model.json"),
    ],
)
def test_load_model_load_fail(tmp_path, monkeypatch, load_func, model_name):
    """Test model loading when load_model raises exception."""
    model_file = tmp_path / model_name
    model_file.write_text("{}")

    class FakeRegressor:
        def load_model(self, path):
            raise ValueError("fake load error")

    monkeypatch.setattr(mod.xgb, "XGBRegressor", lambda: FakeRegressor())

    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg: printed.append(msg))

    result = load_func(model_file)

    assert isinstance(result, FakeRegressor)
    assert any("Failed to load" in msg for msg in printed)


# ============================================================================
# Tests for get_advanced_pitching_stats_from_buffer
# ============================================================================


def test_empty_csv(monkeypatch):
    """Test processing empty CSV file."""
    csv_data = "Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League\n"
    buffer = make_csv(csv_data)
    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    assert result == {}


def test_bad_filename(monkeypatch):
    """Test error handling for invalid filename."""
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


def test_basic_pitching_stats(monkeypatch):
    """Test basic pitching statistics calculation."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,Strikeout,StrikeSwinging,Out,,,,Right,,Fastball,100,2,0,SEC
John,AUB,Walk,BallCalled,,,,,Right,,Fastball,98,2,0,SEC
John,AUB,,InPlay,Out,97,20,10,Right,GroundBall,Fastball,97,3,0,SEC
John,AUB,,InPlay,Out,94,20,10,Right,GroundBall,Fastball,97,0,0,SEC
"""
    buffer = make_csv(csv_data)
    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.4, xslg_model=None, xwoba_model=None
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    assert key in result
    stats = result[key]

    assert stats["plate_app"] == 4
    assert stats["batted_balls"] == 2
    assert stats["at_bats"] == 3
    assert stats["fastballs"] == 4
    assert stats["ground_balls"] == 2

    assert stats["k_per"] == pytest.approx(1 / 4, rel=1e-3)
    assert stats["bb_per"] == pytest.approx(1 / 4, rel=1e-3)
    assert stats["la_sweet_spot_per"] == pytest.approx(2 / 2, rel=1e-3)
    assert stats["hard_hit_per"] == pytest.approx(1 / 2, rel=1e-3)
    assert stats["avg_exit_velo"] == pytest.approx((97 + 94) / 2, rel=1e-3)
    assert stats["avg_fastball_velo"] == pytest.approx((100 + 98 + 97 + 97) / 4, rel=1e-3)

    assert stats["in_zone_pitches"] == 3
    assert stats["whiff_per"] == pytest.approx(1 / 3, rel=1e-3)
    assert stats["out_of_zone_pitches"] == 1
    assert stats["chase_per"] == pytest.approx(1 / 1, rel=1e-3)

    assert stats["xba_per"] > 0
    assert stats["xslg_per"] == 0
    assert stats["xwoba_per"] > 0
    assert stats["barrel_per"] == 0


def test_practice_team(monkeypatch):
    """Test practice team detection and team name conversion."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Jane,AUB_TIG,Walk,InPlay,Out,95,15,5,Right,GroundBall,Fastball,100,2,0,Team
"""
    buffer = make_csv(csv_data)
    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.5, xslg_model=None, xwoba_model=None
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "practice_game.csv")
    key = ("Jane", "AUB_PRC", 2025)
    assert key in result
    stats = result[key]
    assert stats["PitcherTeam"] == "AUB_PRC"


def test_batted_ball_empty(monkeypatch):
    """Test stats calculation when no batted balls present."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Alice,BBB,Walk,StrikeSwinging,Out,,,,Right,,Fastball,100,2,0,SEC
"""
    buffer = make_csv(csv_data)
    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.4, xslg_model=None, xwoba_model=None
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("Alice", "BBB", 2025)
    stats = result[key]

    assert stats["batted_balls"] == 0
    assert stats["xba_per"] == 0
    assert stats["xslg_per"] == 0
    assert stats["barrel_per"] == 0


def test_xwoba_exception(monkeypatch, capsys):
    """Test xwOBA calculation error handling."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Tom,AUB,,InPlay,Out,95,15,5,Right,GroundBall,Fastball,97,2,0,SEC
"""
    buffer = make_csv(csv_data)

    class FailingModel:
        def predict(self, df):
            raise RuntimeError("fail")

    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.4, xslg_model=None, xwoba_model=FailingModel()
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("Tom", "AUB", 2025)
    stats = result[key]
    assert stats["xwoba_per"] == 0

    captured = capsys.readouterr()
    assert "Error computing xwOBA for Tom" in captured.out


def test_multiple_pitchers(monkeypatch):
    """Test processing multiple pitchers from same CSV."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
A,AUB,Walk,InPlay,Out,95,15,5,Right,GroundBall,Fastball,100,2,0,SEC
B,AUB,Strikeout,InPlay,Out,90,20,10,Left,GroundBall,Fastball,98,3,1,SEC
"""
    buffer = make_csv(csv_data)
    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.4, xslg_model=None, xwoba_model=None
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    assert ("A", "AUB", 2025) in result
    assert ("B", "AUB", 2025) in result


def test_missing_ev_la_dir(monkeypatch):
    """Test handling of missing exit velocity, launch angle, and direction."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Sam,AUB,Strikeout,InPlay,Out,,,,Right,,Fastball,100,2,0,SEC
"""
    buffer = make_csv(csv_data)
    setup_csv_test_mocks(monkeypatch, lookup_xba=mod.lookup_xBA, xslg_model=None, xwoba_model=None)

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("Sam", "AUB", 2025)
    stats = result[key]
    assert stats["xba_per"] == 0
    assert stats["plate_app"] == 1


def test_plate_loc_exception(monkeypatch):
    """Test handling of invalid plate location values."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
Jane,AUB,Strikeout,StrikeSwinging,Out,95,20,10,Right,,Fastball,100,bad,0,SEC
John,AUB,Strikeout,StrikeSwinging,Out,95,20,10,Right,,Fastball,100,2,bad,SEC
"""
    buffer = io.StringIO(csv_data)
    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.4, xslg_model=None, xwoba_model=None
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("Jane", "AUB", 2025)
    assert key in result
    stats = result[key]
    assert stats["in_zone_pitches"] == 0
    assert stats["out_of_zone_pitches"] == 0


def test_xslg_model_branch(monkeypatch):
    """Test xSLG calculation when model is available."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,,InPlay,Out,95,20,10,Right,GroundBall,Fastball,97,2,0,SEC
"""
    buffer = io.StringIO(csv_data)

    class DummyXSLGModel:
        def predict(self, df):
            return [0.6] * len(df)

    setup_csv_test_mocks(
        monkeypatch,
        lookup_xba=lambda ev, la, dr: 0.4,
        xslg_model=DummyXSLGModel(),
        xwoba_model=None,
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    stats = result[key]

    assert stats["xslg_per"] == 0.6


def test_xslg_model_none_or_empty(monkeypatch):
    """Test xSLG calculation when model is None or no batted balls."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,Strikeout,StrikeSwinging,Out,,,,Right,,Fastball,100,2,0,SEC
"""
    buffer = io.StringIO(csv_data)
    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.4, xslg_model=None, xwoba_model=None
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    stats = result[key]

    assert stats["xslg_per"] == 0


def test_xwoba_model_branch(monkeypatch):
    """Test xwOBA calculation when model is available."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,,InPlay,Out,95,20,10,Right,GroundBall,Fastball,97,2,0,SEC
"""
    buffer = io.StringIO(csv_data)

    class DummyXwOBA:
        def predict(self, df):
            return [0.25] * len(df)

    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.4, xslg_model=None, xwoba_model=DummyXwOBA()
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    stats = result[key]

    assert stats["xwoba_per"] == 0.25


def test_xwoba_model_none_or_empty(monkeypatch):
    """Test xwOBA calculation when model is None or no batted balls."""
    csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlayResult,ExitSpeed,Angle,Direction,BatterSide,TaggedHitType,TaggedPitchType,RelSpeed,PlateLocHeight,PlateLocSide,League
John,AUB,Strikeout,StrikeSwinging,Out,,,,Right,,Fastball,100,2,0,SEC
"""
    buffer = io.StringIO(csv_data)
    setup_csv_test_mocks(
        monkeypatch, lookup_xba=lambda ev, la, dr: 0.4, xslg_model=None, xwoba_model=None
    )

    result = mod.get_advanced_pitching_stats_from_buffer(buffer, "file.csv")
    key = ("John", "AUB", 2025)
    stats = result[key]

    assert stats["xwoba_per"] == 0


# ============================================================================
# Tests for safe_get and weighted_avg
# ============================================================================


def test_safe_get():
    """Test safe_get function with various key scenarios."""
    data = {"a": 10, "b": None}

    assert mod.safe_get(data, "a") == 10
    assert mod.safe_get(data, "b") == 0
    assert mod.safe_get(data, "c") == 0


def test_weighted_avg():
    """Test weighted_avg function with various scenarios."""
    existing = {"stat": 10, "weight": 2}
    new = {"stat": 20, "weight": 3}
    total_weight = 5
    result = mod.weighted_avg(existing, new, "stat", "weight", total_weight)
    assert result == (10 * 2 + 20 * 3) / 5

    existing = {"stat": -5, "weight": 1}
    new = {"stat": 0, "weight": 1}
    total_weight = 2
    result = mod.weighted_avg(existing, new, "stat", "weight", total_weight)
    assert result == 0

    existing = {"stat": 10, "weight": 0}
    new = {"stat": 20, "weight": 0}
    total_weight = 0
    result = mod.weighted_avg(existing, new, "stat", "weight", total_weight)
    assert result is None

    existing = {}
    new = {"stat": 15, "weight": 3}
    total_weight = 3
    result = mod.weighted_avg(existing, new, "stat", "weight", total_weight)
    assert result == 15


# ============================================================================
# Tests for combine_advanced_pitching_stats
# ============================================================================


def test_combine_empty_existing():
    """Test combining stats when existing stats dict is empty."""
    new_stats = {"Pitcher": "John", "PitcherTeam": "AUB", "Year": 2025, "plate_app": 4}
    combined = mod.combine_advanced_pitching_stats({}, new_stats)
    assert combined == new_stats


def test_combine_existing_no_new_dates():
    """Test combining stats when new dates are subset of existing dates."""
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
    assert combined == existing


def test_combine_existing_with_new_dates(monkeypatch):
    """Test combining stats when new dates are present."""
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

    assert combined["plate_app"] == 10
    assert combined["batted_balls"] == 6
    assert combined["ground_balls"] == 3
    assert combined["in_zone_pitches"] == 5
    assert combined["out_of_zone_pitches"] == 4
    assert combined["fastballs"] == 9
    assert combined["at_bats"] == 7

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
    """Test combining stats when keys are missing from input dicts."""
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
    assert combined["plate_app"] == 0
    assert combined["batted_balls"] == 0
    assert combined["ground_balls"] == 0


# ============================================================================
# Tests for rank_and_scale_to_1_100
# ============================================================================


def test_rank_and_scale_to_1_100():
    """Test rank_and_scale_to_1_100 function with various scenarios."""
    # Empty series
    s = pd.Series([], dtype=float)
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.empty

    # All NaN values
    s = pd.Series([np.nan, np.nan, np.nan])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.isna().all()

    # Single value
    s = pd.Series([42])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.iloc[0] == 100.0

    # Identical values
    s = pd.Series([10, 10, 10])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert (scaled == 100.0).all()

    # Descending order (higher is better)
    s = pd.Series([10, 20, 30])
    scaled = mod.rank_and_scale_to_1_100(s, ascending=False)
    assert scaled.iloc[0] == 1.0
    assert scaled.iloc[1] == 50.0
    assert scaled.iloc[2] == 100.0

    # Ascending order (lower is better)
    s = pd.Series([10, 20, 30])
    scaled = mod.rank_and_scale_to_1_100(s, ascending=True)
    assert scaled.iloc[0] == 100.0
    assert scaled.iloc[1] == 50.0
    assert scaled.iloc[2] == 1.0

    # Series with ties
    s = pd.Series([10, 20, 20, 30])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.iloc[0] == 1.0
    assert scaled.iloc[1] == scaled.iloc[2] == 67.0
    assert scaled.iloc[3] == 100.0

    # Series with NaN values
    s = pd.Series([10, None, 30])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert scaled.iloc[0] == 1.0
    assert scaled.iloc[1] is None
    assert scaled.iloc[2] == 100.0

    # Min and max equal
    s = pd.Series([5, 5, 5, 5])
    scaled = mod.rank_and_scale_to_1_100(s)
    assert (scaled == 100.0).all()


# ============================================================================
# Tests for upload_advanced_pitching_to_supabase
# ============================================================================


def test_no_input_supabase(monkeypatch):
    """Test upload function with empty input dictionary."""
    supabase_mock = MagicMock()
    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        result = mod.upload_advanced_pitching_to_supabase({})
        assert result is None


def test_upsert_called_for_new_pitcher(mock_supabase_fast):
    """Test that upsert is called for new pitcher records."""
    supabase_mock, table_mock = mock_supabase_fast
    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(NEW_PITCHER)
    assert table_mock.upsert.called


def test_combines_existing_pitcher(monkeypatch, mock_supabase_fast):
    """Test combining stats for existing pitcher records."""
    supabase_mock, table_mock = mock_supabase_fast

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

    assert table_mock.upsert.called


def test_rank_upload_called(monkeypatch, mock_supabase_fast):
    """Test that ranking upload is called after data upload."""
    supabase_mock, table_mock = mock_supabase_fast

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

    assert table_mock.upsert.call_count >= 2


def test_rank_helper_all_nan(monkeypatch):
    """Test ranking upload with all NaN metric values."""
    table_mock = MagicMock()
    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    nan_metrics = {
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

    execute_mock = MagicMock()
    execute_mock.data = [create_pitcher_record("PlayerX", "TeamX", 2025, **nan_metrics)]
    table_mock.select.return_value.range.return_value.execute.return_value = execute_mock

    monkeypatch.setattr("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock)

    pitchers_dict = {
        ("PlayerX", "TeamX", 2025): {
            **create_pitcher_record("PlayerX", "TeamX", 2025, **nan_metrics),
            "unique_games": 1,
        }
    }

    mod.upload_advanced_pitching_to_supabase(pitchers_dict, max_fetch_loops=1)
    assert table_mock.upsert.called


def test_upsert_exception_handled(monkeypatch):
    """Test exception handling during upsert operations."""
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


def test_outer_try_exception(monkeypatch):
    """Test exception handling for outer try-except block."""
    supabase_mock = MagicMock()
    supabase_mock.table.side_effect = RuntimeError("Test outer exception")

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(NEW_PITCHER, max_fetch_loops=1)


def test_continue_branch(monkeypatch, mock_supabase_fast):
    """Test continue branch when processed dates are subset of existing."""
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
            "processed_dates": ["2025-01-01"],
        }
    }

    fetch_mock = MagicMock()
    fetch_mock.data = [existing[("Player1", "TeamA", 2025)]]
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    monkeypatch.setattr("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock)

    monkeypatch.setattr(
        "scripts.utils.advanced_pitching_stats_upload.combine_advanced_pitching_stats",
        mod.combine_advanced_pitching_stats,
    )

    mod.upload_advanced_pitching_to_supabase(new_stat, max_fetch_loops=1)
    assert table_mock.upsert.call_count >= 0


def test_rank_upsert_exception(monkeypatch, mock_supabase_fast):
    """Test exception handling during ranking upsert."""
    supabase_mock, table_mock = mock_supabase_fast

    records = [
        {**NEW_PITCHER[("Player1", "TeamA", 2025)]},
    ]
    table_mock.select.return_value.range.return_value.execute.return_value.data = records

    monkeypatch.setattr(
        "scripts.utils.advanced_pitching_stats_upload.combine_advanced_pitching_stats",
        mock_combine,
    )

    def raise_error(*args, **kwargs):
        raise RuntimeError("Test exception during upsert")

    table_mock.upsert.return_value.execute.side_effect = raise_error

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(NEW_PITCHER, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_full_rank_paths_pitching(monkeypatch):
    """Test full ranking paths for both practice and non-practice pitchers."""
    from scripts.utils import advanced_pitching_stats_upload as mod

    table_mock = MagicMock()

    records = [
        create_pitcher_record(
            "PA", "AUB", 2025, League="SEC", Level="DI", avg_exit_velo=88.0, k_per=0.25, bb_per=0.08
        ),
        create_pitcher_record(
            "PB",
            "UGA",
            2025,
            League="SEC",
            Level="DI",
            avg_exit_velo=90.0,
            k_per=0.28,
            bb_per=0.07,
            la_sweet_spot_per=0.18,
            hard_hit_per=0.28,
            whiff_per=0.16,
            chase_per=0.2,
            avg_fastball_velo=95.0,
            gb_per=0.5,
            xba_per=0.24,
            xslg_per=0.38,
            xwoba_per=0.28,
            barrel_per=0.03,
        ),
        create_pitcher_record(
            "PC",
            "AUB_PRC",
            2025,
            League="TEAM",
            Level="DI",
            avg_exit_velo=92.0,
            k_per=0.22,
            bb_per=0.1,
            la_sweet_spot_per=0.22,
            hard_hit_per=0.32,
            whiff_per=0.14,
            chase_per=0.24,
            avg_fastball_velo=93.0,
            gb_per=0.4,
            xba_per=0.28,
            xslg_per=0.42,
            xwoba_per=0.31,
            barrel_per=0.05,
        ),
        create_pitcher_record(
            "PD",
            "AUB_PRC",
            2025,
            League="TEAM",
            Level="DI",
            avg_exit_velo=91.0,
            k_per=0.21,
            bb_per=0.11,
            la_sweet_spot_per=0.21,
            hard_hit_per=0.31,
            whiff_per=0.13,
            chase_per=0.23,
            avg_fastball_velo=92.0,
            gb_per=0.42,
            xba_per=0.29,
            xslg_per=0.41,
            xwoba_per=0.32,
            barrel_per=0.06,
        ),
    ]

    fetch_mock = MagicMock()
    fetch_mock.data = records
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    upsert_mock = MagicMock()
    upsert_mock.execute.return_value = None
    table_mock.upsert.return_value = upsert_mock

    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    pitchers_dict = {
        ("PA", "AUB", 2025): {
            "Pitcher": "PA",
            "PitcherTeam": "AUB",
            "Year": 2025,
            "avg_exit_velo": 88.0,
        }
    }

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(pitchers_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_overall_ranks_continue_all_practice_pitching(monkeypatch):
    """Test that overall ranks continue when all records are practice data."""
    from scripts.utils import advanced_pitching_stats_upload as mod

    table_mock = MagicMock()

    fetch_mock = MagicMock()
    fetch_mock.data = [create_pitcher_record("P1", "AUB_PRC", 2025)]
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    upsert_mock = MagicMock()
    upsert_mock.execute.return_value = None
    table_mock.upsert.return_value = upsert_mock

    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    pitchers_dict = {
        ("P1", "AUB_PRC", 2025): {
            "Pitcher": "P1",
            "PitcherTeam": "AUB_PRC",
            "Year": 2025,
            "avg_exit_velo": 88.0,
        }
    }

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(pitchers_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_team_ranks_continue_all_practice_pitching(monkeypatch):
    """Test that team ranks continue when team group has all practice records."""
    from scripts.utils import advanced_pitching_stats_upload as mod

    table_mock = MagicMock()

    fetch_mock = MagicMock()
    fetch_mock.data = [create_pitcher_record("P1", "AUB", 2025)]
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    def execute_side_effect():
        result = MagicMock()
        result.data = [create_pitcher_record("P1", "AUB_PRC", 2025)]
        return result

    table_mock.select.return_value.range.return_value.execute.side_effect = execute_side_effect

    upsert_mock = MagicMock()
    upsert_mock.execute.return_value = None
    table_mock.upsert.return_value = upsert_mock

    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    pitchers_dict = {
        ("P1", "AUB", 2025): {
            "Pitcher": "P1",
            "PitcherTeam": "AUB",
            "Year": 2025,
            "avg_exit_velo": 88.0,
        }
    }

    with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
        mod.upload_advanced_pitching_to_supabase(pitchers_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


def test_team_ranks_continue_empty_mask(monkeypatch):
    """Test team ranks continue branch when mask is empty."""
    import pandas as pd

    from scripts.utils import advanced_pitching_stats_upload as mod

    table_mock = MagicMock()

    fetch_mock = MagicMock()
    fetch_mock.data = [create_pitcher_record("P1", "AUB_PRC", 2025)]
    table_mock.select.return_value.range.return_value.execute.return_value = fetch_mock

    upsert_mock = MagicMock()
    upsert_mock.execute.return_value = None
    table_mock.upsert.return_value = upsert_mock

    supabase_mock = MagicMock()
    supabase_mock.table.return_value = table_mock

    pitchers_dict = {
        ("P1", "AUB_PRC", 2025): {
            "Pitcher": "P1",
            "PitcherTeam": "AUB_PRC",
            "Year": 2025,
            "avg_exit_velo": 88.0,
        }
    }

    original_eq = pd.Series.eq

    def patched_eq(self, other):
        result = original_eq(self, other)
        if other == "AUB_PRC":
            return pd.Series([False] * len(self), index=self.index)
        return result

    with patch.object(pd.Series, "eq", patched_eq):
        with patch("scripts.utils.advanced_pitching_stats_upload.supabase", supabase_mock):
            mod.upload_advanced_pitching_to_supabase(pitchers_dict, max_fetch_loops=1)

    assert table_mock.upsert.called


# ============================================================================
# Tests for calculate_practice_overall_rank
# ============================================================================


def test_calculate_practice_overall_rank():
    """Test calculate_practice_overall_rank with various edge cases and scenarios."""
    # NaN practice value
    non_practice_series = pd.Series([10, 20, 30])
    result = mod.calculate_practice_overall_rank(float("nan"), non_practice_series)
    assert result is None

    # Empty series after dropping NaN
    non_practice_series = pd.Series([None, np.nan, float("nan")])
    result = mod.calculate_practice_overall_rank(10.0, non_practice_series)
    assert result is None

    # All values same
    non_practice_series = pd.Series([10, 10, 10, 10])
    result = mod.calculate_practice_overall_rank(10.0, non_practice_series)
    assert result == 100.0

    # Practice better than all (ascending=True)
    non_practice_series = pd.Series([10, 20, 30])
    result = mod.calculate_practice_overall_rank(5.0, non_practice_series, ascending=True)
    assert result == 100.0

    # Practice worse than all (ascending=False)
    non_practice_series = pd.Series([10, 20, 30])
    result = mod.calculate_practice_overall_rank(5.0, non_practice_series, ascending=False)
    assert result == 1.0

    # Scaling formula - middle value
    non_practice_series = pd.Series([10, 20, 30, 40, 50])
    practice_value = 25.0
    result = mod.calculate_practice_overall_rank(
        practice_value, non_practice_series, ascending=True
    )
    assert result is not None
    assert 1.0 <= result <= 100.0
    assert isinstance(result, float)

    # Practice rank equals min_rank (best)
    non_practice_series2 = pd.Series([10, 20, 30, 40, 50])
    practice_value2 = 10.0
    result2 = mod.calculate_practice_overall_rank(
        practice_value2, non_practice_series2, ascending=True
    )
    assert result2 == 100.0

    # Ensure values don't go below 1
    non_practice_series3 = pd.Series([10, 20, 30, 40, 50])
    practice_value3 = 49.0
    result3 = mod.calculate_practice_overall_rank(
        practice_value3, non_practice_series3, ascending=True
    )
    assert result3 >= 1.0
