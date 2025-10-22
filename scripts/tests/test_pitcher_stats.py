"""
Unit tests for update_pitchers_table.py

Tests pitcher statistics extraction and upload functionality.
Run with: pytest tests/test_pitchers_table.py -v
"""

import io
from datetime import date
from unittest.mock import Mock, patch

import pytest

from utils import (
    calculate_innings_pitched,
    get_pitcher_stats_from_buffer,
    is_in_strike_zone,
    upload_pitchers_to_supabase,
)


class TestStrikeZoneDetection:
    """Test strike zone boundary detection."""

    def test_center_of_zone_is_strike(self):
        """Pitch in dead center should be a strike."""
        assert is_in_strike_zone(2.66, 0.0) is True

    def test_top_corner_is_strike(self):
        """Top corner of zone should be a strike."""
        assert is_in_strike_zone(3.55, 0.86) is True

    def test_bottom_corner_is_strike(self):
        """Bottom corner of zone should be a strike."""
        assert is_in_strike_zone(1.77, -0.86) is True

    def test_pitch_above_zone_is_ball(self):
        """Pitch above zone should be a ball."""
        assert is_in_strike_zone(4.0, 0.0) is False

    def test_pitch_below_zone_is_ball(self):
        """Pitch below zone should be a ball."""
        assert is_in_strike_zone(1.0, 0.0) is False

    def test_pitch_left_of_zone_is_ball(self):
        """Pitch outside left edge should be a ball."""
        assert is_in_strike_zone(2.5, -1.5) is False

    def test_pitch_right_of_zone_is_ball(self):
        """Pitch outside right edge should be a ball."""
        assert is_in_strike_zone(2.5, 1.5) is False

    def test_none_height_returns_false(self):
        """None value for height should return False, not crash."""
        assert is_in_strike_zone(None, 0.0) is False

    def test_none_side_returns_false(self):
        """None value for side should return False, not crash."""
        assert is_in_strike_zone(2.5, None) is False

    def test_string_values_return_false(self):
        """String values should return False, not crash."""
        assert is_in_strike_zone("high", "outside") is False


class TestInningsPitchedCalculation:
    """Test innings pitched calculation (3 outs = 1 inning, displayed as X.Y)."""

    def test_zero_outs(self):
        """Zero outs should be 0.0 innings."""
        assert calculate_innings_pitched(0, 0) == 0.0

    def test_one_out(self):
        """One out should be 0.1 innings."""
        assert calculate_innings_pitched(1, 0) == 0.1

    def test_two_outs(self):
        """Two outs should be 0.2 innings."""
        assert calculate_innings_pitched(0, 2) == 0.2

    def test_three_outs_full_inning(self):
        """Three outs should be 1.0 innings."""
        assert calculate_innings_pitched(3, 0) == 1.0

    def test_four_outs(self):
        """Four outs should be 1.1 innings."""
        assert calculate_innings_pitched(2, 2) == 1.1

    def test_five_outs(self):
        """Five outs should be 1.2 innings."""
        assert calculate_innings_pitched(3, 2) == 1.2

    def test_nine_outs_complete_game(self):
        """Nine outs (complete game) should be 3.0 innings."""
        assert calculate_innings_pitched(6, 3) == 3.0

    def test_ten_outs(self):
        """Ten outs should be 3.1 innings."""
        assert calculate_innings_pitched(7, 3) == 3.1

    def test_mix_strikeouts_and_play_outs(self):
        """Should handle combination of strikeout and play outs."""
        # 5 strikeouts + 4 play outs = 9 outs = 3.0 innings
        assert calculate_innings_pitched(5, 4) == 3.0


class TestPitcherStatsExtraction:
    """Test extraction of pitcher statistics from CSV data."""

    @pytest.fixture
    def mock_date_parser(self):
        """Mock date parser to return fixed date."""
        with patch("utils.file_date.CSVFilenameParser") as mock:
            mock.return_value.get_date_object.return_value = date(2025, 3, 15)
            yield mock

    @pytest.fixture
    def minimal_csv(self):
        """Minimal valid CSV data."""
        csv_data = (
            "Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide"
            ",Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult,GameUID\n"
            """Smith,TeamA,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,2,1,0,Jones,Strikeout,game1
                Smith,TeamA,Walk,BallCalled,1.0,-1.5,1,1,3,2,2,0,Brown,Walk,game1
                Smith,TeamA,,InPlay,2.8,0.2,1,1,1,1,3,1,Davis,Single,game1"""
        )
        return io.StringIO(csv_data)

    @pytest.fixture
    def complex_csv(self):
        """More complex CSV with multiple pitchers and scenarios."""
        csv_data = (
            "Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning,Outs"
            ",Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult,GameUID\n"
            """Smith,TeamA,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Jones,Strikeout,game1
                Smith,TeamA,Strikeout,StrikeSwinging,3.0,0.5,1,1,2,2,2,0,Brown,Strikeout,game1
                Smith,TeamA,Strikeout,StrikeSwinging,2.2,-0.3,1,2,1,2,3,0,Davis,Strikeout,game1
                Johnson,TeamB,Walk,BallCalled,4.0,1.0,1,0,3,1,1,0,Miller,Walk,game1
                Johnson,TeamB,,StrikeSwinging,2.5,0.0,1,0,3,1,1,0,Miller,Out,game1
                Johnson,TeamB,,InPlay,2.8,0.5,1,0,3,2,1,0,Miller,HomeRun,game1"""
        )
        return io.StringIO(csv_data)

    def test_basic_stats_extraction(self, minimal_csv, mock_date_parser):
        """Test basic counting stats are extracted correctly."""
        result = get_pitcher_stats_from_buffer(minimal_csv, "test.csv")

        key = ("Smith", "TeamA", 2025)
        assert key in result

        stats = result[key]
        assert stats["total_strikeouts_pitcher"] == 1
        assert stats["total_walks_pitcher"] == 1
        assert stats["hits"] == 1
        assert stats["pitches"] == 3

    def test_multiple_pitchers_separated(self, complex_csv, mock_date_parser):
        """Test that stats for different pitchers are kept separate."""
        result = get_pitcher_stats_from_buffer(complex_csv, "test.csv")

        assert len(result) == 2
        assert ("Smith", "TeamA", 2025) in result
        assert ("Johnson", "TeamB", 2025) in result

    def test_strikeout_count(self, complex_csv, mock_date_parser):
        """Test strikeout counting."""
        result = get_pitcher_stats_from_buffer(complex_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        assert smith_stats["total_strikeouts_pitcher"] == 3

    def test_walk_count(self, complex_csv, mock_date_parser):
        """Test walk counting."""
        result = get_pitcher_stats_from_buffer(complex_csv, "test.csv")

        johnson_stats = result[("Johnson", "TeamB", 2025)]
        assert johnson_stats["total_walks_pitcher"] == 1

    def test_homerun_count(self, complex_csv, mock_date_parser):
        """Test home run counting."""
        result = get_pitcher_stats_from_buffer(complex_csv, "test.csv")

        johnson_stats = result[("Johnson", "TeamB", 2025)]
        assert johnson_stats["homeruns"] == 1

    def test_innings_pitched_calculation(self, complex_csv, mock_date_parser):
        """Test that innings pitched is calculated correctly."""
        result = get_pitcher_stats_from_buffer(complex_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # 3 strikeouts = 3 outs = 1.0 inning
        assert smith_stats["total_innings_pitched"] == 1.0

    def test_k_per_9_calculation(self, complex_csv, mock_date_parser):
        """Test K/9 rate calculation."""
        result = get_pitcher_stats_from_buffer(complex_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # 3 K in 1.0 inning = (3 * 9) / 1.0 = 27.0
        assert smith_stats["k_per_9"] == 27.0

    def test_whip_calculation(self, minimal_csv, mock_date_parser):
        """Test WHIP calculation."""
        result = get_pitcher_stats_from_buffer(minimal_csv, "test.csv")

        stats = result[("Smith", "TeamA", 2025)]
        # (1 walk + 1 hit) / innings_pitched
        # 1 K + 1 out on play = 2 outs = 0.2 innings (decimal) = 2/3 innings
        # WHIP = 2 / (2/3) = 3.0
        assert stats["whip"] == 3.0

    def test_zone_statistics(self, complex_csv, mock_date_parser):
        """Test in-zone and out-of-zone pitch counting."""
        result = get_pitcher_stats_from_buffer(complex_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        assert smith_stats["total_in_zone_pitches"] > 0
        assert smith_stats["misses_in_zone"] >= 0

    def test_missing_columns_returns_empty(self, mock_date_parser):
        """Test that missing required columns returns empty dict."""
        csv_data = """Pitcher,PitcherTeam
Smith,TeamA"""
        buffer = io.StringIO(csv_data)

        result = get_pitcher_stats_from_buffer(buffer, "test.csv")
        assert result == {}

    def test_null_pitcher_name_skipped(self, mock_date_parser):
        """Test that rows with null pitcher names are skipped."""
        csv_data = (
            "Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide"
            ",Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult\n"
            """TeamA,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,2,1,0,Jones,Strikeout
            Smith,TeamA,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,2,1,0,Jones,Strikeout"""
        )
        buffer = io.StringIO(csv_data)

        result = get_pitcher_stats_from_buffer(buffer, "test.csv")
        # Should only have 1 pitcher (Smith), not the null one
        assert len(result) == 1
        assert ("Smith", "TeamA", 2025) in result

    def test_games_started_detection(self, mock_date_parser):
        """Test detection of games started (first PA of first inning)."""
        csv_data = (
            "Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide"
            ",Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult\n"
            "Smith,TeamA,Strikeout,StrikeSwinging,2.5,0.0,1,0,0,0,1,0,Jones,Strikeout"
        )
        buffer = io.StringIO(csv_data)

        result = get_pitcher_stats_from_buffer(buffer, "test.csv")
        stats = result[("Smith", "TeamA", 2025)]
        assert stats["games_started"] == 1


class TestSupabaseUpload:
    """Test Supabase upload functionality."""

    @pytest.fixture
    def sample_pitcher_dict(self):
        """Sample pitcher statistics dictionary."""
        return {
            ("Smith", "TeamA", 2025): {
                "Pitcher": "Smith",
                "PitcherTeam": "TeamA",
                "Year": 2025,
                "total_strikeouts_pitcher": 10,
                "total_walks_pitcher": 3,
                "pitches": 100,
                "hits": 8,
                "homeruns": 2,
                "games_started": 1,
                "total_innings_pitched": 6.0,
                "k_per_9": 15.0,
                "bb_per_9": 4.5,
                "whip": 1.83,
                "total_batters_faced": 25,
                "k_percentage": 0.400,
                "base_on_ball_percentage": 0.120,
                "unique_games": {"game1"},
                "games": 1,
                "total_in_zone_pitches": 60,
                "total_out_of_zone_pitches": 40,
                "misses_in_zone": 5,
                "swings_in_zone": 0,
                "total_num_chases": 8,
                "in_zone_whiff_percentage": 0.083,
                "chase_percentage": 0.200,
            }
        }

    @patch("utils.update_pitchers_table.supabase")
    def test_upload_removes_unique_games_field(self, mock_supabase, sample_pitcher_dict):
        """Test that unique_games set is removed before upload."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitchers_to_supabase(sample_pitcher_dict)

        # Get the data that was passed to upsert
        call_args = mock_table.upsert.call_args[0][0]
        uploaded_record = call_args[0]

        # Verify unique_games was removed
        assert "unique_games" not in uploaded_record
        assert "Pitcher" in uploaded_record
        assert uploaded_record["Pitcher"] == "Smith"

    @patch("utils.update_pitchers_table.supabase")
    def test_upload_uses_correct_conflict_key(self, mock_supabase, sample_pitcher_dict):
        """Test that upsert uses correct conflict resolution."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitchers_to_supabase(sample_pitcher_dict)

        # Verify the conflict key
        call_kwargs = mock_table.upsert.call_args[1]
        assert call_kwargs["on_conflict"] == "Pitcher,PitcherTeam,Date"

    @patch("utils.update_pitchers_table.supabase")
    def test_upload_batches_large_datasets(self, mock_supabase):
        """Test that large datasets are uploaded in batches."""
        # Create 2500 pitchers (should be 3 batches)
        large_dict = {}
        for i in range(2500):
            large_dict[(f"Pitcher{i}", "Team", 2025)] = {
                "Pitcher": f"Pitcher{i}",
                "PitcherTeam": "Team",
                "Year": 2025,
                "total_strikeouts_pitcher": 10,
                "total_walks_pitcher": 3,
                "pitches": 100,
                "hits": 8,
                "homeruns": 2,
                "games_started": 1,
                "total_innings_pitched": 6.0,
                "k_per_9": 15.0,
                "bb_per_9": 4.5,
                "whip": 1.83,
                "total_batters_faced": 25,
                "k_percentage": 0.400,
                "base_on_ball_percentage": 0.120,
                "games": 1,
            }

        mock_table = Mock()
        mock_upsert = Mock()
        mock_execute = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = mock_execute

        upload_pitchers_to_supabase(large_dict)

        # Should be called 3 times (1000 + 1000 + 500)
        assert mock_table.upsert.call_count == 3

    @patch("utils.update_pitchers_table.supabase")
    def test_upload_handles_empty_dict(self, mock_supabase):
        """Test that empty dictionary doesn't cause errors."""
        upload_pitchers_to_supabase({})

        # Should not attempt to upload
        mock_supabase.table.assert_not_called()


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def mock_date_parser(self):
        """Mock date parser."""
        with patch("utils.file_date.CSVFilenameParser") as mock:
            mock.return_value.get_date_object.return_value = date(2025, 3, 15)
            yield mock

    def test_divide_by_zero_in_percentages(self, mock_date_parser):
        """Test that zero batters faced doesn't cause divide by zero."""
        csv_data = (
            "Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide"
            ",Inning,Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult"
        )
        buffer = io.StringIO(csv_data)

        # Should not crash, even with no actual data rows
        result = get_pitcher_stats_from_buffer(buffer, "test.csv")
        # Empty result is acceptable
        assert isinstance(result, dict)

    def test_invalid_numeric_values(self, mock_date_parser):
        """Test that invalid numeric values are handled gracefully."""
        csv_data = (
            "Pitcher,PitcherTeam,KorBB,PitchCall,PlateLocHeight,PlateLocSide,Inning"
            ",Outs,Balls,Strikes,PAofInning,OutsOnPlay,Batter,PlayResult\n"
            "Smith,TeamA,Strikeout,StrikeSwinging,invalid,notanumber,1,0,0,2,1,0,Jones,Strikeout"
        )
        buffer = io.StringIO(csv_data)

        result = get_pitcher_stats_from_buffer(buffer, "test.csv")
        # Should process without crashing
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
