"""
Author: Joshua Henley
Created: 03 November 2025

Unit test cases for pitcher_stats_upload.py functions.
"""

import json
from datetime import date
from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from scripts.utils.pitcher_stats_upload import (
    calculate_innings_pitched,
    get_pitcher_stats_from_buffer,
    upload_pitchers_to_supabase,
)


@pytest.fixture
def mock_supabase():
    """Fixture providing a mocked Supabase client."""
    with patch("scripts.utils.pitcher_stats_upload.supabase") as mock:
        yield mock


@pytest.fixture
def sample_csv_data():
    """Fixture providing sample CSV data as a string."""
    return """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult,GameUID,League
              John Doe,Team A,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Batter1,Strikeout,GAME001,College
              John Doe,Team A,,StrikeCalled,2.0,0.5,1,1,1,1,2,0,Batter2,,GAME001,College
              John Doe,Team A,Walk,BallCalled,4.0,2.0,1,1,3,1,2,0,Batter2,,GAME001,College
              John Doe,Team A,,InPlay,3.0,0.0,1,1,0,0,3,1,Batter3,Single,GAME001,College
              Jane Smith,Team B,Strikeout,StrikeSwinging,2.5,0.0,2,0,0,2,1,0,Batter4,Strikeout,GAME002,College
              Jane Smith,Team B,,FoulBallNotFieldable,1.0,3.0,2,1,0,0,2,0,Batter5,,GAME002,College"""


@pytest.fixture
def practice_csv_data():
    """Fixture providing practice data (League = TEAM)."""
    return """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult,GameUID,League
              John Doe,Team A,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Batter1,Strikeout,GAME001,TEAM
              John Doe,Team A,,StrikeCalled,2.0,0.5,1,1,1,1,2,0,Batter2,,GAME001,team"""


@pytest.fixture
def minimal_csv_data():
    """Fixture providing minimal required columns."""
    return """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult
              John Doe,Team A,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Batter1,Strikeout"""


@pytest.fixture
def homeruns_csv_data():
    """Fixture with home runs."""
    return """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult,GameUID
              John Doe,Team A,,InPlay,2.5,0.0,1,0,0,0,1,0,Batter1,HomeRun,GAME001
              John Doe,Team A,,InPlay,2.0,0.5,1,0,1,0,2,0,Batter2,Double,GAME001
              John Doe,Team A,,InPlay,2.0,0.5,1,0,2,0,3,0,Batter3,Triple,GAME001"""


@pytest.fixture
def games_started_csv_data():
    """Fixture for testing games started calculation."""
    return """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult,GameUID
              John Doe,Team A,,StrikeCalled,2.5,0.0,1,0,0,0,1,0,Batter1,,GAME001
              Jane Smith,Team B,,BallCalled,2.0,0.5,1,0,0,0,1,0,Batter2,,GAME002
              John Doe,Team A,,StrikeCalled,2.5,0.0,2,0,1,0,1,0,Batter3,,GAME001"""


@pytest.fixture
def invalid_location_csv_data():
    """Fixture with invalid PlateLocHeight and PlateLocSide values."""
    return """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult
              John Doe,Team A,Strikeout,StrikeSwinging,invalid,0.0,1,0,0,0,1,0,Batter1,Strikeout
              John Doe,Team A,,StrikeCalled,2.0,invalid,1,1,1,1,2,0,Batter2,
              John Doe,Team A,,InPlay,,,1,1,0,0,3,1,Batter3,Single"""


@pytest.fixture
def empty_pitcher_csv_data():
    """Fixture with empty/null pitcher data."""
    return """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult
              ,Team A,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Batter1,Strikeout
              John Doe,,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Batter1,Strikeout
              ,,,StrikeCalled,2.0,0.5,1,1,1,1,2,0,Batter2,"""


@pytest.fixture
def nan_pitcher_csv_data():
    """Fixture with actual pandas NaN values in pitcher/team columns."""
    return """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult,GameUID
              John Doe,Team A,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Batter1,Strikeout,GAME001
              ,Team B,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Batter2,Strikeout,GAME002
              Jane Smith,,Walk,BallCalled,4.0,2.0,1,1,3,1,2,0,Batter3,,GAME003"""


class TestCalculateInningsPitched:
    """Test calculate_innings_pitched function."""

    @pytest.mark.parametrize(
        "strikeouts,outs_on_play,expected",
        [
            (3, 0, 1.0),  # Exactly 1 inning
            (0, 3, 1.0),  # Exactly 1 inning from outs
            (6, 0, 2.0),  # Exactly 2 innings
            (1, 0, 0.1),  # 1 out = 0.1 innings
            (2, 0, 0.2),  # 2 outs = 0.2 innings
            (4, 0, 1.1),  # 1 full inning + 1 out
            (5, 0, 1.2),  # 1 full inning + 2 outs
            (2, 2, 1.1),  # Mixed strikeouts and outs
            (0, 0, 0.0),  # No outs
            (10, 5, 5.0),  # Large numbers
        ],
    )
    def test_calculate_innings_pitched(self, strikeouts, outs_on_play, expected):
        result = calculate_innings_pitched(strikeouts, outs_on_play)
        assert isinstance(result, float)
        assert result == expected


class TestGetPitcherStatsFromBuffer:
    """Test get_pitcher_stats_from_buffer function."""

    def test_basic_stats_calculation(self, sample_csv_data):
        buffer = StringIO(sample_csv_data)
        filename = "20241101-Game-Test_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            assert len(result) == 2  # Two pitchers

            # Check John Doe stats
            john_key = ("John Doe", "Team A", 2024)
            assert john_key in result
            john_stats = result[john_key]

            assert john_stats["Pitcher"] == "John Doe"
            assert john_stats["PitcherTeam"] == "Team A"
            assert john_stats["total_strikeouts_pitcher"] == 1
            assert john_stats["total_walks_pitcher"] == 1
            assert john_stats["pitches"] == 4
            assert john_stats["hits"] == 1
            assert john_stats["is_practice"] == False

    def test_practice_data_detection(self, practice_csv_data):
        buffer = StringIO(practice_csv_data)
        filename = "20241101-Practice_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            john_key = ("John Doe", "Team A", 2024)
            assert result[john_key]["is_practice"] == True

    def test_homeruns_calculation(self, homeruns_csv_data):
        buffer = StringIO(homeruns_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            john_key = ("John Doe", "Team A", 2024)
            assert result[john_key]["homeruns"] == 1
            assert result[john_key]["hits"] == 3  # HR + Double + Triple

    def test_games_started_calculation(self, games_started_csv_data):
        buffer = StringIO(games_started_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            john_key = ("John Doe", "Team A", 2024)
            jane_key = ("Jane Smith", "Team B", 2024)

            assert result[john_key]["games_started"] == 1
            assert result[jane_key]["games_started"] == 1

    def test_zone_statistics(self, sample_csv_data):
        buffer = StringIO(sample_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            john_key = ("John Doe", "Team A", 2024)
            john_stats = result[john_key]

            assert john_stats["total_in_zone_pitches"] > 0
            assert john_stats["total_out_of_zone_pitches"] >= 0
            assert john_stats["misses_in_zone"] >= 0

    def test_invalid_location_handling(self, invalid_location_csv_data):
        buffer = StringIO(invalid_location_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            # Should not raise exception, just skip invalid locations
            result = get_pitcher_stats_from_buffer(buffer, filename)

            assert len(result) == 1
            john_key = ("John Doe", "Team A", 2024)
            assert john_key in result

    def test_empty_pitcher_data_filtered(self, empty_pitcher_csv_data):
        buffer = StringIO(empty_pitcher_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            # Empty/whitespace pitcher names should be filtered out
            assert len(result) == 0

    def test_nan_pitcher_or_team_filtered(self, nan_pitcher_csv_data):
        """Test that rows with NaN pitcher or team names are skipped in groupby."""
        buffer = StringIO(nan_pitcher_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            # Only John Doe with Team A should be in results
            # Rows with NaN pitcher or team should be filtered by pd.isna() check
            assert len(result) == 1
            john_key = ("John Doe", "Team A", 2024)
            assert john_key in result
            assert result[john_key]["total_strikeouts_pitcher"] == 1

    def test_missing_required_columns(self):
        csv_data = """Pitcher,PitcherTeam
                      John Doe,Team A"""
        buffer = StringIO(csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            assert result == {}

    def test_no_game_uid_column(self, minimal_csv_data):
        buffer = StringIO(minimal_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            assert len(result) == 1
            john_key = ("John Doe", "Team A", 2024)
            assert result[john_key]["games"] == 0  # No GameUID column
            assert len(result[john_key]["unique_games"]) == 0

    def test_null_date_from_filename(self, sample_csv_data):
        buffer = StringIO(sample_csv_data)
        filename = "InvalidFilename.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = None

            result = get_pitcher_stats_from_buffer(buffer, filename)

            assert result == {}

    def test_csv_read_exception(self):
        buffer = StringIO("Invalid CSV Content\nNo proper structure")
        filename = "20241101-Game_verified.csv"

        # This should handle the exception and return empty dict
        result = get_pitcher_stats_from_buffer(buffer, filename)

        # Note: Depending on pandas behavior, this might not actually raise
        # an exception, but the function should handle it gracefully
        assert isinstance(result, dict)

    def test_k_per_9_calculation(self, sample_csv_data):
        buffer = StringIO(sample_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            john_key = ("John Doe", "Team A", 2024)
            john_stats = result[john_key]

            # With strikeouts and innings pitched, k_per_9 should be calculated
            if john_stats["total_innings_pitched"] > 0:
                assert john_stats["k_per_9"] is not None
                assert isinstance(john_stats["k_per_9"], float)

    def test_whip_calculation(self, sample_csv_data):
        buffer = StringIO(sample_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            john_key = ("John Doe", "Team A", 2024)
            john_stats = result[john_key]

            if john_stats["total_innings_pitched"] > 0:
                assert john_stats["whip"] is not None
                assert isinstance(john_stats["whip"], float)

    def test_zero_innings_pitched_stats(self):
        """Test that derived stats are None when innings pitched is 0."""
        csv_data = """Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult
                      John Doe,Team A,,BallCalled,2.5,0.0,1,0,1,0,1,0,Batter1,Strikeout"""
        buffer = StringIO(csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            john_key = ("John Doe", "Team A", 2024)
            john_stats = result[john_key]

            assert john_stats["total_innings_pitched"] == 0.0
            assert john_stats["k_per_9"] is None
            assert john_stats["bb_per_9"] is None
            assert john_stats["whip"] is None

    def test_batters_faced_with_game_uid(self, sample_csv_data):
        buffer = StringIO(sample_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            john_key = ("John Doe", "Team A", 2024)
            assert result[john_key]["total_batters_faced"] > 0

    def test_chase_percentage_calculation(self, sample_csv_data):
        buffer = StringIO(sample_csv_data)
        filename = "20241101-Game_verified.csv"

        with patch("scripts.utils.pitcher_stats_upload.CSVFilenameParser") as mock_parser:
            mock_instance = mock_parser.return_value
            mock_instance.get_date_object.return_value = date(2024, 11, 1)

            result = get_pitcher_stats_from_buffer(buffer, filename)

            # Check that chase_percentage is calculated when applicable
            for stats in result.values():
                if stats["total_out_of_zone_pitches"] > 0:
                    if stats["chase_percentage"] is not None:
                        assert 0 <= stats["chase_percentage"] <= 1


class TestUploadPitchersToSupabase:
    """Test upload_pitchers_to_supabase function."""

    def test_upload_empty_dict(self, mock_supabase, capsys):
        upload_pitchers_to_supabase({})

        captured = capsys.readouterr()
        assert "No pitchers to upload" in captured.out

    def test_successful_upload(self, mock_supabase):
        pitchers_dict = {
            ("John Doe", "Team A", 2024): {
                "Pitcher": "John Doe",
                "PitcherTeam": "Team A",
                "Date": "2024-11-01",
                "total_strikeouts_pitcher": 5,
                "total_walks_pitcher": 2,
                "pitches": 50,
                "unique_games": {"GAME001", "GAME002"},
                "games": 2,
            }
        }

        # Mock successful upsert
        mock_result = Mock()
        mock_result.data = [{"Pitcher": "John Doe"}]
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = mock_result

        # Mock count query
        mock_count_result = Mock()
        mock_count_result.count = 1
        mock_supabase.table.return_value.select.return_value.execute.return_value = (
            mock_count_result
        )

        upload_pitchers_to_supabase(pitchers_dict)

        # Verify upsert was called
        mock_supabase.table.assert_called_with("PitcherStats")

    def test_batch_upload(self, mock_supabase):
        # Create more than 1000 pitchers to test batching
        pitchers_dict = {}
        for i in range(1500):
            pitchers_dict[(f"Pitcher{i}", f"Team{i}", 2024)] = {
                "Pitcher": f"Pitcher{i}",
                "PitcherTeam": f"Team{i}",
                "Date": "2024-11-01",
                "total_strikeouts_pitcher": i,
                "unique_games": set(),
                "games": 0,
            }

        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.count = 1500
        mock_supabase.table.return_value.select.return_value.execute.return_value = (
            mock_count_result
        )

        upload_pitchers_to_supabase(pitchers_dict)

        # Should be called twice (1000 + 500)
        assert mock_supabase.table.return_value.upsert.return_value.execute.call_count >= 2

    def test_batch_error_handling(self, mock_supabase, capsys):
        pitchers_dict = {
            ("John Doe", "Team A", 2024): {
                "Pitcher": "John Doe",
                "PitcherTeam": "Team A",
                "Date": "2024-11-01",
                "total_strikeouts_pitcher": 5,
                "unique_games": set(),
                "games": 0,
            }
        }

        # Mock batch error
        mock_supabase.table.return_value.upsert.return_value.execute.side_effect = Exception(
            "Database error"
        )

        upload_pitchers_to_supabase(pitchers_dict)

        captured = capsys.readouterr()
        assert "Error uploading batch" in captured.out

    def test_batch_error_with_sample_record(self, mock_supabase, capsys):
        """Test that batch error prints sample record and continues processing."""
        pitchers_dict = {
            ("John Doe", "Team A", 2024): {
                "Pitcher": "John Doe",
                "PitcherTeam": "Team A",
                "Date": "2024-11-01",
                "total_strikeouts_pitcher": 5,
                "unique_games": set(),
                "games": 0,
            },
            ("Jane Smith", "Team B", 2024): {
                "Pitcher": "Jane Smith",
                "PitcherTeam": "Team B",
                "Date": "2024-11-01",
                "total_strikeouts_pitcher": 3,
                "unique_games": set(),
                "games": 0,
            },
        }

        # Mock the result object that would be referenced in the except block
        mock_result = Mock()
        mock_result.data = ["some_data"]

        # Create a mock that raises exception but also sets result in scope
        def side_effect_with_result(*args, **kwargs):
            # This simulates having 'result' variable in scope when exception occurs
            raise Exception("Database connection failed")

        mock_supabase.table.return_value.upsert.return_value.execute.side_effect = (
            side_effect_with_result
        )

        upload_pitchers_to_supabase(pitchers_dict)

        captured = capsys.readouterr()
        # Verify that error handling code was executed
        assert "Error uploading batch 1" in captured.out
        assert "Sample record from failed batch" in captured.out
        # Verify continue statement allowed function to complete
        assert "Successfully processed 0 pitcher records" in captured.out

    def test_general_exception_handling(self, mock_supabase, capsys):
        pitchers_dict = {
            ("John Doe", "Team A", 2024): {
                "Pitcher": "John Doe",
                "PitcherTeam": "Team A",
                "Date": "2024-11-01",
                "total_strikeouts_pitcher": 5,
                "unique_games": set(),
                "games": 0,
            }
        }

        # Mock exception during table access
        mock_supabase.table.side_effect = Exception("Connection error")

        upload_pitchers_to_supabase(pitchers_dict)

        captured = capsys.readouterr()
        assert "Supabase error" in captured.out

    def test_unique_games_removed_before_upload(self, mock_supabase):
        pitchers_dict = {
            ("John Doe", "Team A", 2024): {
                "Pitcher": "John Doe",
                "PitcherTeam": "Team A",
                "Date": "2024-11-01",
                "unique_games": {"GAME001", "GAME002"},
                "games": 2,
            }
        }

        mock_result = Mock()
        mock_result.data = []
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.count = 1
        mock_supabase.table.return_value.select.return_value.execute.return_value = (
            mock_count_result
        )

        upload_pitchers_to_supabase(pitchers_dict)

        # Get the actual data that was attempted to be uploaded
        call_args = mock_supabase.table.return_value.upsert.call_args
        uploaded_data = call_args[0][0]

        # Verify unique_games was removed
        assert "unique_games" not in uploaded_data[0]
