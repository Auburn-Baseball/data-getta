"""
Pytest suite for scripts.utils.pitcher_pitch_bins_upload.py

Covers:
- Pitch type and side normalization
- Zone classification logic (classify_13)
- File exclusion logic
- Data aggregation functions (empty_row, get_pitcher_bins_from_buffer)
- Upload batching behavior with mocked Supabase client
"""

import io
import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from scripts.utils import pitcher_pitch_bins_upload as mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_csv_buffer():
    """Return a CSV buffer simulating valid pitch tracking data."""
    csv_data = """Pitcher,PitcherTeam,BatterSide,AutoPitchType,PlateLocSide,PlateLocHeight
John Doe,TeamA,L,Four-Seam,0.1,2.5
John Doe,TeamA,R,Slider,-0.2,3.0
Jane Roe,TeamB,L,Sinker,0.9,1.8
"""
    return io.StringIO(csv_data)


@pytest.fixture
def sample_meta():
    """Sample classification meta dict used for empty_row tests."""
    return {
        "ZoneId": 5,
        "InZone": True,
        "ZoneRow": 2,
        "ZoneCol": 2,
        "ZoneCell": 5,
        "OuterLabel": "NA",
    }


# ---------------------------------------------------------------------------
# Normalization Tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("four-seam", "FourSeam"),
        ("Two Seam", "Sinker"),
        ("SL", "Slider"),
        ("Curve", "Curveball"),
        ("CH", "Changeup"),
        ("Splitter", "Splitter"),
        ("Cutter", "Cutter"),
        ("FC", "Cutter"),
        ("fastball", "FourSeam"),
        ("unknown", "Other"),
        (None, "Other"),
    ],
)
def test_norm_pitch_type(input_str, expected):
    """Ensure pitch type normalization handles variants correctly."""
    assert mod.norm_pitch_type(input_str) == expected


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("Left", "L"),
        ("Right", "R"),
        ("l", "L"),
        ("r", "R"),
        (None, "R"),
        ("unknown", "R"),
    ],
)
def test_norm_side(input_str, expected):
    """Ensure side normalization outputs 'L' or 'R'."""
    assert mod.norm_side(input_str) == expected


# ---------------------------------------------------------------------------
# Zone Classification Tests
# ---------------------------------------------------------------------------
def test_classify_inner_zone_center():
    """Point near center should be in inner zone 5 (middle cell)."""
    result = mod.classify_13(0.0, 2.5)
    assert result["InZone"] is True
    assert result["ZoneId"] == 5
    assert result["OuterLabel"] == "NA"


@pytest.mark.parametrize(
    "x,y,expected_label",
    [
        (-1.0, 4.0, "OTL"),
        (1.0, 4.0, "OTR"),
        (-1.0, 1.0, "OBL"),
        (1.0, 1.0, "OBR"),
    ],
)
def test_classify_outer_zones(x, y, expected_label):
    """Points outside box are correctly classified into 4 outer quadrants."""
    result = mod.classify_13(x, y)
    assert result["InZone"] is False
    assert result["OuterLabel"] == expected_label
    assert result["ZoneId"] == mod.OUTER_ID[expected_label]


# ---------------------------------------------------------------------------
# File Exclusion Tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "filename,expected",
    [
        ("game_fhc.csv", True),
        ("playerpositioning_2023.csv", True),
        ("verified_game.csv", False),
    ],
)
def test_should_exclude_file(filename, expected):
    """Verify exclusion filter correctly flags unwanted files."""
    assert mod.should_exclude_file(filename) == expected


# ---------------------------------------------------------------------------
# Aggregation Tests
# ---------------------------------------------------------------------------
def test_empty_row_contains_all_pitch_columns(sample_meta):
    """empty_row should return all expected columns with zeros."""
    row = mod.empty_row("TeamA", "2024-07-04", "John Doe", sample_meta)
    # Verify base fields
    assert row["PitcherTeam"] == "TeamA"
    assert row["ZoneId"] == 5
    assert row["ZoneVersion"] == mod.ZONE_VERSION
    # Verify pitch count fields exist and are zero
    for col in mod.ALL_PITCH_COLUMNS:
        assert col in row
        assert row[col] == 0


@patch("scripts.utils.pitcher_pitch_bins_upload.CSVFilenameParser")
def test_get_pitcher_bins_from_buffer(mock_parser, sample_csv_buffer):
    """Ensure aggregation groups pitches correctly and counts by zone/type."""
    mock_parser.return_value.get_date_object.return_value = "2024-07-04"
    bins = mod.get_pitcher_bins_from_buffer(sample_csv_buffer, "TeamA_2024.csv")

    assert isinstance(bins, dict)
    # Expect multiple keys (unique pitcher + zone_id combos)
    assert all(isinstance(v, dict) for v in bins.values())

    # Check one of the aggregated records
    first_record = next(iter(bins.values()))
    assert "TotalPitchCount" in first_record
    assert first_record["TotalPitchCount"] >= 1


def test_get_pitcher_bins_from_buffer_missing_columns(monkeypatch):
    """If required columns are missing, should return empty dict."""
    buf = io.StringIO("A,B,C\n1,2,3")
    mock_parser = MagicMock()
    monkeypatch.setattr(mod, "CSVFilenameParser", lambda: mock_parser)
    result = mod.get_pitcher_bins_from_buffer(buf, "missing.csv")
    assert result == {}


@patch("scripts.utils.pitcher_pitch_bins_upload.CSVFilenameParser")
def test_get_pitcher_bins_from_buffer_with_invalid_coords(mock_parser):
    """Rows with non-numeric PlateLocSide/Height are skipped without crashing."""
    csv_data = """Pitcher,PitcherTeam,BatterSide,AutoPitchType,PlateLocSide,PlateLocHeight
John Doe,TeamA,L,Four-Seam,0.1,2.5
Jane Roe,TeamB,R,Slider,invalid,3.0
Jack Smith,TeamC,L,Curve,0.2,NaN
"""
    buffer = io.StringIO(csv_data)
    mock_parser.return_value.get_date_object.return_value = "2024-07-04"

    bins = mod.get_pitcher_bins_from_buffer(buffer, "game.csv")

    # Only the valid first row should appear in the output
    keys = list(bins.keys())
    assert len(keys) == 1
    team, date, pitcher, zone_id = keys[0]
    assert team == "TeamA"
    assert pitcher == "John Doe"

    record = bins[keys[0]]
    assert record["TotalPitchCount"] == 1
    assert record["Count_FourSeam"] == 1
    assert record["Count_L_FourSeam"] == 1


# ---------------------------------------------------------------------------
# Upload Tests (mocked Supabase)
# ---------------------------------------------------------------------------
@patch("scripts.utils.pitcher_pitch_bins_upload.supabase")
def test_upload_pitcher_pitch_bins(mock_supabase):
    """Ensure upload batching works and interacts with Supabase API."""
    bins = {
        ("TeamA", "2024-07-04", "John Doe", 5): {
            "PitcherTeam": "TeamA",
            "Date": "2024-07-04",
            "Pitcher": "John Doe",
            "ZoneId": 5,
            "InZone": True,
            "ZoneRow": 2,
            "ZoneCol": 2,
            "ZoneCell": 5,
            "OuterLabel": "NA",
            "ZoneVersion": mod.ZONE_VERSION,
            "TotalPitchCount": 10,
        }
    }
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = None

    mod.upload_pitcher_pitch_bins(bins)

    mock_supabase.table.assert_called_once_with("PitcherPitchBins")
    mock_table.upsert.assert_called_once()


def test_upload_pitcher_pitch_bins_empty(capsys):
    """No upload should occur if bins dict is empty."""
    mod.upload_pitcher_pitch_bins({})
    captured = capsys.readouterr()
    assert "No bins data to upload" in captured.out


def test_upload_pitcher_pitch_bins_exception(capsys):
    """Simulate an exception during Supabase upload to hit the except block."""
    # Prepare a minimal bins dict
    bins = {
        ("TeamA", "2024-07-04", "John Doe", 5): {
            "PitcherTeam": "TeamA",
            "Date": "2024-07-04",
            "Pitcher": "John Doe",
            "ZoneId": 5,
            "InZone": True,
            "ZoneRow": 2,
            "ZoneCol": 2,
            "ZoneCell": 5,
            "OuterLabel": "NA",
            "ZoneVersion": mod.ZONE_VERSION,
            "TotalPitchCount": 1,
        }
    }

    # Mock the supabase client to raise an exception when upsert is called
    mock_table = MagicMock()
    mock_table.upsert.return_value.execute.side_effect = Exception("Upload failed")

    with patch("scripts.utils.pitcher_pitch_bins_upload.supabase") as mock_supabase:
        mock_supabase.table.return_value = mock_table

        mod.upload_pitcher_pitch_bins(bins)

    # Capture printed output
    captured = capsys.readouterr()
    assert "Error uploading batch" in captured.out
    assert "Sample record" in captured.out
    assert "Upload failed" in captured.out


def test_main_prints_message(capsys):
    """Ensure the main() function prints the startup message."""
    mod.main()
    captured = capsys.readouterr()
    assert "Starting pitch bins CSV processing..." in captured.out
