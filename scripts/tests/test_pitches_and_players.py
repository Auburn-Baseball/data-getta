"""
Unit tests for pitch counts and players table processing.

Run with: pytest tests/test_pitches_and_players.py -v
"""

import io
from datetime import date
from unittest.mock import Mock, patch

import pytest

from utils import (
    get_pitch_counts_from_buffer,
    get_players_from_buffer,
    upload_pitches_to_supabase,
    upload_players_to_supabase,
)

# ============================================================================
# PITCH COUNTS TESTS
# ============================================================================


class TestPitchCountsExtraction:
    """Test extraction of pitch count statistics."""

    @pytest.fixture
    def mock_date_parser(self):
        """Mock date parser to return fixed date."""
        with patch("utils.update_pitches_table.CSVFilenameParser") as mock:
            mock.return_value.get_date_object.return_value = date(2025, 3, 15)
            yield mock

    @pytest.fixture
    def simple_pitch_csv(self):
        """Simple CSV with pitch data."""
        csv_data = """Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType,GameUID
                   Smith,TeamA,Four-Seam,Fastball,game1
                   Smith,TeamA,Four-Seam,Fastball,game1
                   Smith,TeamA,Slider,Breaking,game1
                   Smith,TeamA,Curveball,Breaking,game1"""
        return io.StringIO(csv_data)

    @pytest.fixture
    def complex_pitch_csv(self):
        """Complex CSV with various pitch types."""
        csv_data = """Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType,GameUID
                   Smith,TeamA,Four-Seam,Fastball,game1
                   Smith,TeamA,Four-Seam,Fastball,game1
                   Smith,TeamA,Sinker,Fastball,game1
                   Smith,TeamA,Slider,Breaking,game1
                   Smith,TeamA,Curveball,Breaking,game1
                   Smith,TeamA,Changeup,Offspeed,game1
                   Smith,TeamA,Cutter,Fastball,game1
                   Smith,TeamA,Splitter,Offspeed,game1
                   Smith,TeamA,Other,Other,game1
                   Smith,TeamA,NaN,Fastball,game1
                   Smith,TeamA,,Fastball,game1
                   Jones,TeamB,Four-Seam,Fastball,game1"""
        return io.StringIO(csv_data)

    def test_basic_pitch_counting(self, simple_pitch_csv, mock_date_parser):
        """Test basic pitch counting."""
        result = get_pitch_counts_from_buffer(simple_pitch_csv, "20250315-Stadium-1.csv")

        key = ("Smith", "TeamA", 2025)
        assert key in result

        stats = result[key]
        assert stats["total_pitches"] == 4
        assert stats["fourseam_count"] == 2
        assert stats["slider_count"] == 1
        assert stats["curveball_count"] == 1

    def test_all_pitch_types_counted(self, complex_pitch_csv, mock_date_parser):
        """Test that all pitch types are counted correctly."""
        result = get_pitch_counts_from_buffer(complex_pitch_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        assert smith_stats["fourseam_count"] == 2
        assert smith_stats["sinker_count"] == 1
        assert smith_stats["slider_count"] == 1
        assert smith_stats["curveball_count"] == 1
        assert smith_stats["changeup_count"] == 1
        assert smith_stats["cutter_count"] == 1
        assert smith_stats["splitter_count"] == 1
        assert smith_stats["other_count"] == 3  # "Other", "NaN", and empty

    def test_twoseam_detection(self, mock_date_parser):
        """Test two-seam detection (Tagged=Fastball but Auto!=Four-Seam)."""
        csv_data = """Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType
                   Smith,TeamA,Sinker,Fastball
                   Smith,TeamA,Four-Seam,Fastball
                   Smith,TeamA,Cutter,Fastball"""
        buffer = io.StringIO(csv_data)

        result = get_pitch_counts_from_buffer(buffer, "test.csv")
        stats = result[("Smith", "TeamA", 2025)]

        # Two-seam: Sinker and Cutter when Tagged=Fastball but Auto!=Four-Seam
        assert stats["twoseam_count"] == 2

    def test_multiple_pitchers_separated(self, complex_pitch_csv, mock_date_parser):
        """Test that different pitchers are separated."""
        result = get_pitch_counts_from_buffer(complex_pitch_csv, "test.csv")

        assert len(result) == 2
        assert ("Smith", "TeamA", 2025) in result
        assert ("Jones", "TeamB", 2025) in result

    def test_total_pitches_matches_rows(self, complex_pitch_csv, mock_date_parser):
        """Test that total pitches equals number of rows per pitcher."""
        result = get_pitch_counts_from_buffer(complex_pitch_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        jones_stats = result[("Jones", "TeamB", 2025)]

        assert smith_stats["total_pitches"] == 11
        assert jones_stats["total_pitches"] == 1

    def test_missing_columns_returns_empty(self, mock_date_parser):
        """Test that missing required columns returns empty dict."""
        csv_data = """Pitcher,PitcherTeam
                   Smith,TeamA"""
        buffer = io.StringIO(csv_data)

        result = get_pitch_counts_from_buffer(buffer, "test.csv")
        assert result == {}

    def test_null_pitcher_name_skipped(self, mock_date_parser):
        """Test that rows with null pitcher names are skipped."""
        csv_data = """Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType
                   ,TeamA,Four-Seam,Fastball
                   Smith,TeamA,Four-Seam,Fastball"""
        buffer = io.StringIO(csv_data)

        result = get_pitch_counts_from_buffer(buffer, "test.csv")
        assert len(result) == 1
        assert ("Smith", "TeamA", 2025) in result

    def test_date_extraction_from_filename(self, mock_date_parser):
        """Test that date is extracted from filename."""
        csv_data = """Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType
                   Smith,TeamA,Four-Seam,Fastball"""
        buffer = io.StringIO(csv_data)

        result = get_pitch_counts_from_buffer(buffer, "20250315-Stadium-1.csv")
        stats = result[("Smith", "TeamA", 2025)]

        assert stats["Date"] == "2025-03-15"


class TestPitchCountsUpload:
    """Test Supabase upload for pitch counts."""

    @pytest.fixture
    def sample_pitch_dict(self):
        """Sample pitch counts dictionary."""
        return {
            ("Smith", "TeamA", 2025): {
                "Pitcher": "Smith",
                "PitcherTeam": "TeamA",
                "Date": "2025-03-15",
                "total_pitches": 100,
                "fourseam_count": 45,
                "sinker_count": 10,
                "slider_count": 20,
                "curveball_count": 10,
                "changeup_count": 10,
                "cutter_count": 3,
                "splitter_count": 0,
                "twoseam_count": 2,
                "other_count": 0,
                "unique_games": {"game1"},
                "games": 1,
            }
        }

    @patch("utils.update_pitches_table.supabase")
    def test_upload_removes_unique_games_field(self, mock_supabase, sample_pitch_dict):
        """Test that unique_games set is removed before upload."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitches_to_supabase(sample_pitch_dict)

        # Get the data that was passed to upsert
        call_args = mock_table.upsert.call_args[0][0]
        uploaded_record = call_args[0]

        # Verify unique_games was removed
        assert "unique_games" not in uploaded_record
        assert "Pitcher" in uploaded_record
        assert uploaded_record["Pitcher"] == "Smith"

    @patch("utils.update_pitches_table.supabase")
    def test_upload_uses_correct_conflict_key(self, mock_supabase, sample_pitch_dict):
        """Test that upsert uses correct conflict resolution."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitches_to_supabase(sample_pitch_dict)

        # Verify the conflict key
        call_kwargs = mock_table.upsert.call_args[1]
        assert call_kwargs["on_conflict"] == "Pitcher,PitcherTeam,Date"

    @patch("utils.update_pitches_table.supabase")
    def test_upload_correct_table_name(self, mock_supabase, sample_pitch_dict):
        """Test that upload uses correct table name."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitches_to_supabase(sample_pitch_dict)

        # Verify correct table
        mock_supabase.table.assert_called_with("PitchCounts")

    @patch("utils.update_pitches_table.supabase")
    def test_upload_batches_large_datasets(self, mock_supabase):
        """Test that large datasets are uploaded in batches."""
        large_dict = {}
        for i in range(2500):
            large_dict[(f"Pitcher{i}", "Team", 2025)] = {
                "Pitcher": f"Pitcher{i}",
                "PitcherTeam": "Team",
                "Date": "2025-03-15",
                "total_pitches": 100,
            }

        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitches_to_supabase(large_dict)

        # Should be called 3 times (1000 + 1000 + 500)
        assert mock_table.upsert.call_count == 3

    @patch("utils.update_pitches_table.supabase")
    def test_upload_handles_empty_dict(self, mock_supabase):
        """Test that empty dictionary doesn't cause errors."""
        upload_pitches_to_supabase({})

        # Should not attempt to upload
        mock_supabase.table.assert_not_called()


# ============================================================================
# PLAYERS TABLE TESTS
# ============================================================================


class TestPlayersExtraction:
    """Test extraction of players from CSV data."""

    @pytest.fixture
    def simple_player_csv(self):
        """Simple CSV with player data."""
        csv_data = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
                   Smith,12345,TeamA,Jones,67890,TeamB
                   Smith,12345,TeamA,Brown,11111,TeamB"""
        return io.StringIO(csv_data)

    @pytest.fixture
    def complex_player_csv(self):
        """Complex CSV with various scenarios."""
        csv_data = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
                   Smith,12345,TeamA,Jones,67890,TeamB
                   Johnson,22222,TeamA,Jones,67890,TeamB
                   Smith,12345,TeamA,Davis,33333,TeamC
                   Wilson,44444,TeamB,,,"""
        return io.StringIO(csv_data)

    @pytest.fixture
    def two_way_player_csv(self):
        """CSV where same person is both pitcher and batter."""
        csv_data = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
                   Smith,12345,TeamA,Jones,67890,TeamA
                   Jones,67890,TeamA,Smith,12345,TeamA"""
        return io.StringIO(csv_data)

    def test_basic_player_extraction(self, simple_player_csv):
        """Test basic player extraction."""
        result = get_players_from_buffer(simple_player_csv, "test.csv")

        # Should have 3 unique players
        assert len(result) == 3
        assert ("Smith", "TeamA", 2025) in result
        assert ("Jones", "TeamB", 2025) in result
        assert ("Brown", "TeamB", 2025) in result

    def test_pitcher_data_extracted(self, simple_player_csv):
        """Test that pitcher data is extracted correctly."""
        result = get_players_from_buffer(simple_player_csv, "test.csv")

        smith = result[("Smith", "TeamA", 2025)]
        assert smith["Name"] == "Smith"
        assert smith["PitcherId"] == "12345"
        assert smith["TeamTrackmanAbbreviation"] == "TeamA"
        assert smith["Year"] == 2025
        assert smith["BatterId"] is None  # Smith only pitches in this data

    def test_batter_data_extracted(self, simple_player_csv):
        """Test that batter data is extracted correctly."""
        result = get_players_from_buffer(simple_player_csv, "test.csv")

        jones = result[("Jones", "TeamB", 2025)]
        assert jones["Name"] == "Jones"
        assert jones["BatterId"] == "67890"
        assert jones["TeamTrackmanAbbreviation"] == "TeamB"
        assert jones["Year"] == 2025
        assert jones["PitcherId"] is None  # Jones only bats in this data

    def test_two_way_player_both_ids(self, two_way_player_csv):
        """Test that two-way players get both IDs."""
        result = get_players_from_buffer(two_way_player_csv, "test.csv")

        smith = result[("Smith", "TeamA", 2025)]
        assert smith["PitcherId"] == "12345"
        assert smith["BatterId"] == "12345"

        jones = result[("Jones", "TeamA", 2025)]
        assert jones["PitcherId"] == "67890"
        assert jones["BatterId"] == "67890"

    def test_duplicate_entries_merged(self, simple_player_csv):
        """Test that duplicate player entries are merged."""
        result = get_players_from_buffer(simple_player_csv, "test.csv")

        # Jones appears twice in the data but should only have one entry
        jones_entries = [k for k in result.keys() if k[0] == "Jones"]
        assert len(jones_entries) == 1

    def test_multiple_teams_treated_separately(self):
        """Test that same name on different teams creates separate entries."""
        csv_data = """Pitcher,PitcherId,PitcherTeam
                   Smith,12345,TeamA
                   Smith,67890,TeamB"""
        buffer = io.StringIO(csv_data)

        result = get_players_from_buffer(buffer, "test.csv")

        assert len(result) == 2
        assert ("Smith", "TeamA", 2025) in result
        assert ("Smith", "TeamB", 2025) in result

    def test_missing_pitcher_columns(self):
        """Test handling when pitcher columns are missing."""
        csv_data = """Batter,BatterId,BatterTeam
                   Jones,67890,TeamB"""
        buffer = io.StringIO(csv_data)

        result = get_players_from_buffer(buffer, "test.csv")

        # Should still extract batters
        assert len(result) == 1
        assert ("Jones", "TeamB", 2025) in result

    def test_missing_batter_columns(self):
        """Test handling when batter columns are missing."""
        csv_data = """Pitcher,PitcherId,PitcherTeam
                   Smith,12345,TeamA"""
        buffer = io.StringIO(csv_data)

        result = get_players_from_buffer(buffer, "test.csv")

        # Should still extract pitchers
        assert len(result) == 1
        assert ("Smith", "TeamA", 2025) in result

    def test_missing_both_columns_returns_empty(self):
        """Test that missing both pitcher and batter columns returns empty."""
        csv_data = """Date,Inning
                   2025-03-15,1"""
        buffer = io.StringIO(csv_data)

        result = get_players_from_buffer(buffer, "test.csv")
        assert result == {}

    def test_null_values_skipped(self):
        """Test that rows with null values are skipped."""
        csv_data = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
                   Smith,12345,TeamA,Jones,67890,TeamB
                   ,,,Jones,67890,TeamB
                   Smith,12345,TeamA,,,"""
        buffer = io.StringIO(csv_data)

        result = get_players_from_buffer(buffer, "test.csv")

        # Should only get valid entries
        assert ("Smith", "TeamA", 2025) in result
        assert ("Jones", "TeamB", 2025) in result

    def test_empty_string_values_skipped(self):
        """Test that empty strings are treated as invalid."""
        csv_data = """Pitcher,PitcherId,PitcherTeam
                   Smith,12345,TeamA
                   ,12345,TeamA
                   Smith,,TeamA
                   Smith,12345,"""
        buffer = io.StringIO(csv_data)

        result = get_players_from_buffer(buffer, "test.csv")

        # Only the first row is valid
        assert len(result) == 1
        assert ("Smith", "TeamA", 2025) in result

    def test_whitespace_stripped(self):
        """Test that whitespace is stripped from values."""
        csv_data = """Pitcher,PitcherId,PitcherTeam
                   Smith  ,  12345  ,  TeamA  """
        buffer = io.StringIO(csv_data)

        result = get_players_from_buffer(buffer, "test.csv")

        player = result[("Smith", "TeamA", 2025)]
        assert player["Name"] == "Smith"
        assert player["PitcherId"] == "12345"
        assert player["TeamTrackmanAbbreviation"] == "TeamA"


class TestPlayersUpload:
    """Test Supabase upload for players."""

    @pytest.fixture
    def sample_players_dict(self):
        """Sample players dictionary."""
        return {
            ("Smith", "TeamA", 2025): {
                "Name": "Smith",
                "PitcherId": "12345",
                "BatterId": None,
                "TeamTrackmanAbbreviation": "TeamA",
                "Year": 2025,
            },
            ("Jones", "TeamB", 2025): {
                "Name": "Jones",
                "PitcherId": None,
                "BatterId": "67890",
                "TeamTrackmanAbbreviation": "TeamB",
                "Year": 2025,
            },
        }

    @patch("utils.update_players_table.supabase")
    def test_upload_correct_table_name(self, mock_supabase, sample_players_dict):
        """Test that upload uses correct table name."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_players_to_supabase(sample_players_dict)

        mock_supabase.table.assert_called_with("Players")

    @patch("utils.update_players_table.supabase")
    def test_upload_uses_correct_conflict_key(self, mock_supabase, sample_players_dict):
        """Test that upsert uses correct conflict resolution."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_players_to_supabase(sample_players_dict)

        # Verify the conflict key
        call_kwargs = mock_table.upsert.call_args[1]
        assert call_kwargs["on_conflict"] == "Name,TeamTrackmanAbbreviation,Year"

    @patch("utils.update_players_table.supabase")
    def test_upload_includes_both_ids(self, mock_supabase, sample_players_dict):
        """Test that both PitcherId and BatterId are included."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_players_to_supabase(sample_players_dict)

        # Get the data that was passed to upsert
        call_args = mock_table.upsert.call_args[0][0]

        # Verify structure
        assert len(call_args) == 2
        assert all("PitcherId" in player for player in call_args)
        assert all("BatterId" in player for player in call_args)

    @patch("utils.update_players_table.supabase")
    def test_upload_batches_large_datasets(self, mock_supabase):
        """Test that large datasets are uploaded in batches."""
        large_dict = {}
        for i in range(2500):
            large_dict[(f"Player{i}", "Team", 2025)] = {
                "Name": f"Player{i}",
                "PitcherId": str(i),
                "BatterId": None,
                "TeamTrackmanAbbreviation": "Team",
                "Year": 2025,
            }

        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_players_to_supabase(large_dict)

        # Should be called 3 times (1000 + 1000 + 500)
        assert mock_table.upsert.call_count == 3

    @patch("utils.update_players_table.supabase")
    def test_upload_handles_empty_dict(self, mock_supabase):
        """Test that empty dictionary doesn't cause errors."""
        upload_players_to_supabase({})

        # Should not attempt to upload
        mock_supabase.table.assert_not_called()

    @patch("utils.update_players_table.supabase")
    def test_upload_handles_none_ids(self, mock_supabase):
        """Test that None IDs are handled correctly."""
        player_dict = {
            ("Smith", "TeamA", 2025): {
                "Name": "Smith",
                "PitcherId": None,
                "BatterId": None,
                "TeamTrackmanAbbreviation": "TeamA",
                "Year": 2025,
            }
        }

        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        # Should not crash
        upload_players_to_supabase(player_dict)

        # Verify upload was attempted
        mock_table.upsert.assert_called_once()


class TestIntegration:
    """Integration tests for pitch counts and players."""

    def test_full_pitch_pipeline(self):
        """Test complete pipeline from CSV to upload-ready data."""
        with patch("utils.update_pitches_table.CSVFilenameParser") as mock_parser:
            mock_parser.return_value.get_date_object.return_value = date(2025, 3, 15)

            csv_data = """Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType
                   Smith,TeamA,Four-Seam,Fastball
                   Smith,TeamA,Slider,Breaking
                   Jones,TeamB,Curveball,Breaking"""
            buffer = io.StringIO(csv_data)

            result = get_pitch_counts_from_buffer(buffer, "20250315-Stadium-1.csv")

            # Should have data for both pitchers
            assert len(result) == 2

            # Verify data structure
            for stats in result.values():
                assert "Pitcher" in stats
                assert "PitcherTeam" in stats
                assert "Date" in stats
                assert "total_pitches" in stats
                assert isinstance(stats["Date"], str)

    def test_full_players_pipeline(self):
        """Test complete pipeline for players extraction."""
        csv_data = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
                   Smith,12345,TeamA,Jones,67890,TeamB
                   Johnson,22222,TeamA,Davis,33333,TeamC"""
        buffer = io.StringIO(csv_data)

        result = get_players_from_buffer(buffer, "test.csv")

        # Should have 4 unique players
        assert len(result) == 4

        # Verify data structure
        for player in result.values():
            assert "Name" in player
            assert "TeamTrackmanAbbreviation" in player
            assert "Year" in player
            assert player["Year"] == 2025
            # Must have at least one ID
            assert player["PitcherId"] is not None or player["BatterId"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
