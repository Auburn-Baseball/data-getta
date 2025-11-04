import io
import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from scripts.utils import pitch_counts_upload as mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_csv_buffer():
    """Return a CSV buffer with varied pitch types for testing."""
    csv_data = """Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType,GameUID,League
John Doe,TeamA,Four-Seam,Fastball,game1,PRO
John Doe,TeamA,,Fastball,game1,PRO
John Doe,TeamA,Two-Seam,,game1,PRO
John Doe,TeamA,Slider,Slider,game1,PRO
Jane Roe,TeamB,Curveball,Curveball,game2,TEAM
Jane Roe,TeamB,Sinker,Sinker,game2,TEAM
Jane Roe,TeamB,Cutter,,game2,TEAM
Jane Roe,TeamB,Splitter,Splitter,game2,TEAM
Jane Roe,TeamB,Changeup,Changeup,game2,TEAM
Unknown Pitcher,TeamC,,,game3,
"""
    return io.StringIO(csv_data)


# ---------------------------------------------------------------------------
# get_pitch_counts_from_buffer Tests
# ---------------------------------------------------------------------------
@patch("scripts.utils.pitch_counts_upload.CSVFilenameParser")
def test_get_pitch_counts_from_buffer_counts(mock_parser, sample_csv_buffer):
    """Ensure counts for all pitch types are correct."""
    mock_parser.return_value.get_date_object.return_value = pd.Timestamp("2024-07-04")
    bins = mod.get_pitch_counts_from_buffer(sample_csv_buffer, "game.csv")

    # There should be 3 pitcher-team-season keys
    assert len(bins) == 3

    john_key = ("John Doe", "TeamA", 2024)
    jane_key = ("Jane Roe", "TeamB", 2024)
    unknown_key = ("Unknown Pitcher", "TeamC", 2024)

    john_record = bins[john_key]
    jane_record = bins[jane_key]
    unknown_record = bins[unknown_key]

    # Total pitches
    assert john_record["total_pitches"] == 4
    assert jane_record["total_pitches"] == 5
    assert unknown_record["total_pitches"] == 1

    # John Doe: check twoseam and fourseam
    assert john_record["fourseam_count"] == 2  # First row + empty Auto + Fastball Tagged
    assert john_record["twoseam_count"] == 1  # Explicit Two-Seam
    assert john_record["slider_count"] == 1
    assert john_record["curveball_count"] == 0
    assert john_record["changeup_count"] == 0
    assert john_record["cutter_count"] == 0
    assert john_record["splitter_count"] == 0
    assert john_record["sinker_count"] == 0
    assert john_record["other_count"] == 0

    # Jane Roe: practice flag, counts
    assert jane_record["is_practice"] is True
    assert jane_record["curveball_count"] == 1
    assert jane_record["sinker_count"] == 1
    assert jane_record["cutter_count"] == 1
    assert jane_record["splitter_count"] == 1
    assert jane_record["changeup_count"] == 1
    assert jane_record["fourseam_count"] == 0
    assert jane_record["slider_count"] == 0
    assert jane_record["twoseam_count"] == 0
    assert jane_record["other_count"] == 0

    # Unknown pitcher: missing Auto/Tagged counts as other
    assert unknown_record["other_count"] == 1


@patch("scripts.utils.pitch_counts_upload.CSVFilenameParser")
def test_get_pitch_counts_from_buffer_missing_columns(mock_parser):
    """Missing required columns should return empty dict."""
    buf = io.StringIO("Pitcher,PitcherTeam\nA,B\n")
    mock_parser.return_value.get_date_object.return_value = pd.Timestamp("2024-07-04")
    result = mod.get_pitch_counts_from_buffer(buf, "file.csv")
    assert result == {}


def test_get_pitch_counts_from_buffer_invalid_filename_date(capsys):
    buffer = StringIO("Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType\n")
    mod.get_pitch_counts_from_buffer(buffer, "invalid_filename.csv")

    captured = capsys.readouterr()
    assert "Unable to parse game date from filename: invalid_filename.csv" in captured.out


@patch("scripts.utils.pitch_counts_upload.supabase")
def test_upload_pitches_to_supabase_batches(mock_supabase):
    """Test upload with batching and mocked Supabase client."""
    bins = {
        ("John Doe", "TeamA", 2024): {
            "Pitcher": "John Doe",
            "PitcherTeam": "TeamA",
            "Date": "2024-07-04",
            "total_pitches": 10,
            "curveball_count": 0,
            "fourseam_count": 10,
            "sinker_count": 0,
            "slider_count": 0,
            "twoseam_count": 0,
            "changeup_count": 0,
            "cutter_count": 0,
            "splitter_count": 0,
            "other_count": 0,
            "unique_games": {"game1"},
            "games": 1,
            "is_practice": False,
        }
    }
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = None

    mod.upload_pitches_to_supabase(bins)

    mock_supabase.table.assert_any_call("PitchCounts")
    mock_table.upsert.assert_called_once()


def test_upload_pitches_to_supabase_empty(capsys):
    """No upload occurs if dict is empty."""
    mod.upload_pitches_to_supabase({})
    captured = capsys.readouterr()
    assert "No pitch data to upload" in captured.out


@patch("scripts.utils.pitch_counts_upload.supabase")
def test_upload_pitches_to_supabase_exception(mock_supabase, capsys):
    """Simulate exception during Supabase upload."""
    bins = {
        ("John Doe", "TeamA", 2024): {
            "Pitcher": "John Doe",
            "PitcherTeam": "TeamA",
            "Date": "2024-07-04",
            "total_pitches": 1,
            "curveball_count": 0,
            "fourseam_count": 1,
            "sinker_count": 0,
            "slider_count": 0,
            "twoseam_count": 0,
            "changeup_count": 0,
            "cutter_count": 0,
            "splitter_count": 0,
            "other_count": 0,
            "unique_games": {"game1"},
            "games": 1,
            "is_practice": False,
        }
    }

    mock_table = MagicMock()
    mock_table.upsert.return_value.execute.side_effect = Exception("Upload failed")
    mock_supabase.table.return_value = mock_table

    mod.upload_pitches_to_supabase(bins)
    captured = capsys.readouterr()
    assert "Error uploading batch" in captured.out
    assert "Sample record" in captured.out


def test_upload_pitches_continue_branch(monkeypatch):
    # 3 fake pitchers
    fake_pitchers = {}
    for i in range(3):
        fake_pitchers[(f"Pitcher{i}", f"Team{i}", 2024)] = {
            "Pitcher": f"Pitcher{i}",
            "PitcherTeam": f"Team{i}",
            "Date": "2024-07-04",
            "total_pitches": 10,
            "curveball_count": 0,
            "fourseam_count": 10,
            "sinker_count": 0,
            "slider_count": 0,
            "twoseam_count": 0,
            "changeup_count": 0,
            "cutter_count": 0,
            "splitter_count": 0,
            "other_count": 0,
            "games": 1,
            "is_practice": False,
            "unique_games": set(),
        }

    # Mock Supabase
    supabase_mock = MagicMock()
    table_mock = MagicMock()
    supabase_mock.table.return_value = table_mock
    monkeypatch.setattr(mod, "supabase", supabase_mock)

    # Fail first batch, succeed next batches
    call_counter = {"count": 0}

    def upsert_side_effect(batch, on_conflict):
        call_counter["count"] += 1
        if call_counter["count"] == 1:
            raise RuntimeError("Simulated upsert failure")
        return MagicMock(execute=lambda: None)

    table_mock.upsert.side_effect = upsert_side_effect

    # Set batch_size=1 so we get 3 batches
    mod.upload_pitches_to_supabase(fake_pitchers, batch_size=1)

    # We should have attempted 3 upserts
    assert table_mock.upsert.call_count == 3, "Expected 3 upsert calls to hit continue branch"


def test_upload_pitches_supabase_outer_exception(monkeypatch):
    # Create one fake pitcher
    fake_pitchers = {
        ("Pitcher0", "Team0", 2024): {
            "Pitcher": "Pitcher0",
            "PitcherTeam": "Team0",
            "Date": "2024-07-04",
            "total_pitches": 10,
            "curveball_count": 0,
            "fourseam_count": 10,
            "sinker_count": 0,
            "slider_count": 0,
            "twoseam_count": 0,
            "changeup_count": 0,
            "cutter_count": 0,
            "splitter_count": 0,
            "other_count": 0,
            "games": 1,
            "is_practice": False,
            "unique_games": set(),
        }
    }

    # Mock supabase
    supabase_mock = MagicMock()
    table_mock = MagicMock()
    supabase_mock.table.return_value = table_mock
    monkeypatch.setattr(mod, "supabase", supabase_mock)

    # Normal upsert works
    table_mock.upsert.return_value.execute.return_value = None

    # Simulate exception when trying to get final count
    def select_side_effect(*args, **kwargs):
        raise RuntimeError("Simulated final count failure")

    table_mock.select.side_effect = select_side_effect

    # Call the function
    mod.upload_pitches_to_supabase(fake_pitchers)

    # Check that upsert was called for the batch
    assert table_mock.upsert.called, "Expected upsert() to be called for the batch"

    # The final print should have printed the outer exception
    # (Captured automatically by pytest stdout capture)
