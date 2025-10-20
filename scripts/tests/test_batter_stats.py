"""
Unit tests for batter statistics processing.

Run with: pytest tests/test_batters.py -v
"""

import io
from datetime import date
from unittest.mock import Mock, patch

import pytest

from utils import (
    calculate_total_bases,
    get_batter_stats_from_buffer,
    is_in_strike_zone,
    upload_batters_to_supabase,
)


class TestStrikeZoneDetection:
    """Test strike zone detection (same as pitcher tests)."""

    def test_center_of_zone_is_strike(self):
        """Pitch in dead center should be a strike."""
        assert is_in_strike_zone(2.66, 0.0) is True

    def test_boundaries_are_strikes(self):
        """Pitches on boundaries should be strikes."""
        assert is_in_strike_zone(3.55, 0.86) is True
        assert is_in_strike_zone(1.77, -0.86) is True

    def test_outside_zone_is_ball(self):
        """Pitches outside zone should be balls."""
        assert is_in_strike_zone(4.0, 0.0) is False
        assert is_in_strike_zone(1.0, 0.0) is False
        assert is_in_strike_zone(2.5, 1.5) is False

    def test_none_values_return_false(self):
        """None values should return False safely."""
        assert is_in_strike_zone(None, 0.0) is False
        assert is_in_strike_zone(2.5, None) is False


class TestTotalBasesCalculation:
    """Test total bases calculation for different hit types."""

    def test_single_is_one_base(self):
        """Single should be 1 base."""
        assert calculate_total_bases("Single") == 1

    def test_double_is_two_bases(self):
        """Double should be 2 bases."""
        assert calculate_total_bases("Double") == 2

    def test_triple_is_three_bases(self):
        """Triple should be 3 bases."""
        assert calculate_total_bases("Triple") == 3

    def test_homerun_is_four_bases(self):
        """Home run should be 4 bases."""
        assert calculate_total_bases("HomeRun") == 4

    def test_non_hit_is_zero_bases(self):
        """Non-hits should be 0 bases."""
        assert calculate_total_bases("Out") == 0
        assert calculate_total_bases("Error") == 0
        assert calculate_total_bases("FieldersChoice") == 0
        assert calculate_total_bases("") == 0
        assert calculate_total_bases(None) == 0


class TestBatterStatsExtraction:
    """Test extraction of batter statistics from CSV data."""

    @pytest.fixture
    def mock_date_parser(self):
        """Mock date parser to return fixed date."""
        with patch("utils.update_batters_table.CSVFilenameParser") as mock:
            mock.return_value.get_date_object.return_value = date(2025, 3, 15)
            yield mock

    @pytest.fixture
    def minimal_batter_csv(self):
        """Minimal valid CSV data."""
        csv_data = (
            "Batter,BatterTeam,PlayResult,KorBB,PitchCall,"
            "PlateLocHeight,PlateLocSide,TaggedHitType,GameUID\n"
            """Smith,TeamA,Single,,InPlay,2.5,0.0,LineDrive,game1
                   Smith,TeamA,Out,,InPlay,2.8,0.2,GroundBall,game1
                   Smith,TeamA,Strikeout,Strikeout,StrikeSwinging,2.0,-0.5,,game1"""
        )
        return io.StringIO(csv_data)

    @pytest.fixture
    def complex_batter_csv(self):
        """More complex CSV with various scenarios."""
        csv_data = (
            "Batter,BatterTeam,PlayResult,KorBB,PitchCall,PlateLocHeight"
            ",PlateLocSide,TaggedHitType,ExitSpeed,GameUID\n"
            """Smith,TeamA,Single,,InPlay,2.5,0.0,LineDrive,95.5,game1
                   Smith,TeamA,Double,,InPlay,2.8,0.2,LineDrive,102.3,game1
                   Smith,TeamA,HomeRun,,InPlay,2.2,-0.3,FlyBall,110.2,game1
                   Smith,TeamA,Out,,InPlay,3.0,0.5,GroundBall,85.0,game1
                   Smith,TeamA,Strikeout,Strikeout,StrikeSwinging,2.0,-0.5,,0.0,game1
                   Smith,TeamA,,Walk,BallCalled,4.0,1.0,,,game1
                   Jones,TeamB,Out,,InPlay,2.5,0.0,FlyBall,88.5,game1"""
        )
        return io.StringIO(csv_data)

    def test_basic_stats_extraction(self, minimal_batter_csv, mock_date_parser):
        """Test basic counting stats are extracted correctly."""
        result = get_batter_stats_from_buffer(minimal_batter_csv, "20250315-Stadium-1.csv")

        key = ("Smith", "TeamA", 2025)
        assert key in result

        stats = result[key]
        assert stats["hits"] == 1
        assert stats["at_bats"] == 3  # Single, Out, Strikeout
        assert stats["strikeouts"] == 1
        assert stats["singles"] == 1

    def test_multiple_batters_separated(self, complex_batter_csv, mock_date_parser):
        """Test that stats for different batters are kept separate."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        assert len(result) == 2
        assert ("Smith", "TeamA", 2025) in result
        assert ("Jones", "TeamB", 2025) in result

    def test_hit_counting(self, complex_batter_csv, mock_date_parser):
        """Test accurate hit counting."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        assert smith_stats["hits"] == 3  # Single, Double, HomeRun
        assert smith_stats["singles"] == 1
        assert smith_stats["doubles"] == 1
        assert smith_stats["homeruns"] == 1
        assert smith_stats["extra_base_hits"] == 2  # Double + HR

    def test_at_bat_counting(self, complex_batter_csv, mock_date_parser):
        """Test at-bat calculation."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # At-bats: Single, Double, HomeRun, Out, Strikeout = 5
        # Walk is NOT an at-bat
        assert smith_stats["at_bats"] == 5

    def test_walk_counting(self, complex_batter_csv, mock_date_parser):
        """Test walk counting."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        assert smith_stats["walks"] == 1

    def test_strikeout_counting(self, complex_batter_csv, mock_date_parser):
        """Test strikeout counting."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        assert smith_stats["strikeouts"] == 1

    def test_total_bases_calculation(self, complex_batter_csv, mock_date_parser):
        """Test total bases calculation."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # Single(1) + Double(2) + HomeRun(4) = 7 total bases
        assert smith_stats["total_bases"] == 7

    def test_batting_average_calculation(self, complex_batter_csv, mock_date_parser):
        """Test batting average calculation."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # 3 hits / 5 at-bats = 0.600
        assert smith_stats["batting_average"] == 0.600

    def test_on_base_percentage_calculation(self, complex_batter_csv, mock_date_parser):
        """Test OBP calculation."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # (3 hits + 1 walk + 0 HBP) / (5 AB + 1 BB + 0 HBP + 0 SF) = 4/6 = 0.667
        assert smith_stats["on_base_percentage"] == 0.667

    def test_slugging_percentage_calculation(self, complex_batter_csv, mock_date_parser):
        """Test slugging percentage calculation."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # 7 total bases / 5 at-bats = 1.400
        assert smith_stats["slugging_percentage"] == 1.400

    def test_ops_calculation(self, complex_batter_csv, mock_date_parser):
        """Test OPS calculation."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # OBP (0.667) + SLG (1.400) = 2.067
        assert smith_stats["onbase_plus_slugging"] == 2.067

    def test_isolated_power_calculation(self, complex_batter_csv, mock_date_parser):
        """Test ISO calculation."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # SLG (1.400) - AVG (0.600) = 0.800
        assert smith_stats["isolated_power"] == 0.800

    def test_exit_velocity_tracking(self, complex_batter_csv, mock_date_parser):
        """Test exit velocity is summed correctly."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # 95.5 + 102.3 + 110.2 + 85.0 = 393.0 (excluding 0.0 from strikeout)
        assert smith_stats["total_exit_velo"] == 393.0

    def test_plate_appearances_counting(self, complex_batter_csv, mock_date_parser):
        """Test plate appearance counting."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # All plate appearances including walks
        assert smith_stats["plate_appearances"] >= 5

    def test_k_percentage_calculation(self, complex_batter_csv, mock_date_parser):
        """Test K% calculation."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        # 1 strikeout / plate appearances
        assert smith_stats["k_percentage"] is not None
        assert 0 <= smith_stats["k_percentage"] <= 1

    def test_zone_statistics(self, complex_batter_csv, mock_date_parser):
        """Test in-zone and chase statistics."""
        result = get_batter_stats_from_buffer(complex_batter_csv, "test.csv")

        smith_stats = result[("Smith", "TeamA", 2025)]
        assert smith_stats["chase_percentage"] is not None
        assert smith_stats["in_zone_whiff_percentage"] is not None

    def test_missing_columns_returns_empty(self, mock_date_parser):
        """Test that missing required columns returns empty dict."""
        csv_data = """Batter,BatterTeam
                   Smith,TeamA"""
        buffer = io.StringIO(csv_data)

        result = get_batter_stats_from_buffer(buffer, "test.csv")
        assert result == {}

    def test_null_batter_name_skipped(self, mock_date_parser):
        """Test that rows with null batter names are skipped."""
        csv_data = (
            "Batter,BatterTeam,PlayResult,KorBB,PitchCall,"
            "PlateLocHeight,PlateLocSide,TaggedHitType\n"
            """,TeamA,Single,,InPlay,2.5,0.0,LineDrive
                   Smith,TeamA,Single,,InPlay,2.5,0.0,LineDrive"""
        )
        buffer = io.StringIO(csv_data)

        result = get_batter_stats_from_buffer(buffer, "test.csv")
        assert len(result) == 1
        assert ("Smith", "TeamA", 2025) in result

    def test_zero_at_bats_no_crash(self, mock_date_parser):
        """Test that zero at-bats doesn't cause divide by zero."""
        csv_data = (
            "Batter,BatterTeam,PlayResult,KorBB,"
            "PitchCall,PlateLocHeight,PlateLocSide,TaggedHitType\n"
            "Smith,TeamA,,Walk,BallCalled,4.0,1.0,"
        )
        buffer = io.StringIO(csv_data)

        result = get_batter_stats_from_buffer(buffer, "test.csv")
        stats = result[("Smith", "TeamA", 2025)]
        # Should have None for percentage stats, not crash
        assert stats["batting_average"] is None
        assert stats["slugging_percentage"] is None

    def test_date_extraction_from_filename(self, mock_date_parser):
        """Test that date is extracted from filename correctly."""
        csv_data = (
            "Batter,BatterTeam,PlayResult,KorBB,PitchCall,"
            "PlateLocHeight,PlateLocSide,TaggedHitType\n"
            """Smith,TeamA,Single,,InPlay,2.5,0.0,LineDrive"""
        )
        buffer = io.StringIO(csv_data)

        result = get_batter_stats_from_buffer(buffer, "20250315-Stadium-1.csv")
        stats = result[("Smith", "TeamA", 2025)]

        # Verify date was set
        assert stats["Date"] == "2025-03-15"


class TestSupabaseUpload:
    """Test Supabase upload functionality."""

    @pytest.fixture
    def sample_batter_dict(self):
        """Sample batter statistics dictionary."""
        return {
            ("Smith", "TeamA", 2025): {
                "Batter": "Smith",
                "BatterTeam": "TeamA",
                "Date": "2025-03-15",
                "hits": 3,
                "at_bats": 5,
                "strikes": 8,
                "walks": 1,
                "strikeouts": 1,
                "singles": 1,
                "doubles": 1,
                "triples": 0,
                "homeruns": 1,
                "extra_base_hits": 2,
                "plate_appearances": 6,
                "hit_by_pitch": 0,
                "sacrifice": 0,
                "total_bases": 7,
                "total_exit_velo": 350.5,
                "batting_average": 0.600,
                "on_base_percentage": 0.667,
                "slugging_percentage": 1.400,
                "onbase_plus_slugging": 2.067,
                "isolated_power": 0.800,
                "k_percentage": 0.167,
                "base_on_ball_percentage": 0.167,
                "chase_percentage": 0.250,
                "in_zone_whiff_percentage": 0.125,
                "unique_games": {"game1"},
                "games": 1,
            }
        }

    @patch("utils.update_batters_table.supabase")
    def test_upload_removes_unique_games_field(self, mock_supabase, sample_batter_dict):
        """Test that unique_games set is removed before upload."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_batters_to_supabase(sample_batter_dict)

        # Get the data that was passed to upsert
        call_args = mock_table.upsert.call_args[0][0]
        uploaded_record = call_args[0]

        # Verify unique_games was removed
        assert "unique_games" not in uploaded_record
        assert "Batter" in uploaded_record
        assert uploaded_record["Batter"] == "Smith"

    @patch("utils.update_batters_table.supabase")
    def test_upload_uses_correct_conflict_key(self, mock_supabase, sample_batter_dict):
        """Test that upsert uses correct conflict resolution."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_batters_to_supabase(sample_batter_dict)

        # Verify the conflict key
        call_kwargs = mock_table.upsert.call_args[1]
        assert call_kwargs["on_conflict"] == "Batter,BatterTeam,Date"

    @patch("utils.update_batters_table.supabase")
    def test_upload_batches_large_datasets(self, mock_supabase):
        """Test that large datasets are uploaded in batches."""
        # Create 2500 batters (should be 3 batches)
        large_dict = {}
        for i in range(2500):
            large_dict[(f"Batter{i}", "Team", 2025)] = {
                "Batter": f"Batter{i}",
                "BatterTeam": "Team",
                "Date": "2025-03-15",
                "hits": 3,
                "at_bats": 5,
                "batting_average": 0.600,
            }

        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_batters_to_supabase(large_dict)

        # Should be called 3 times (1000 + 1000 + 500)
        assert mock_table.upsert.call_count == 3

    @patch("utils.update_batters_table.supabase")
    def test_upload_handles_empty_dict(self, mock_supabase):
        """Test that empty dictionary doesn't cause errors."""
        upload_batters_to_supabase({})

        # Should not attempt to upload
        mock_supabase.table.assert_not_called()


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def mock_date_parser(self):
        """Mock date parser."""
        with patch("utils.update_batters_table.CSVFilenameParser") as mock:
            mock.return_value.get_date_object.return_value = date(2025, 3, 15)
            yield mock

    def test_exit_speed_missing_column(self, mock_date_parser):
        """Test handling when ExitSpeed column doesn't exist."""
        csv_data = (
            "Batter,BatterTeam,PlayResult,KorBB,PitchCall"
            ",PlateLocHeight,PlateLocSide,TaggedHitType\n"
            "Smith,TeamA,Single,,InPlay,2.5,0.0,LineDrive"
        )
        buffer = io.StringIO(csv_data)

        result = get_batter_stats_from_buffer(buffer, "test.csv")
        stats = result[("Smith", "TeamA", 2025)]

        # Should have 0.0 exit velo, not crash
        assert stats["total_exit_velo"] == 0.0

    def test_invalid_exit_speed_values(self, mock_date_parser):
        """Test handling of invalid exit speed values."""
        csv_data = (
            "Batter,BatterTeam,PlayResult,KorBB,PitchCall"
            ",PlateLocHeight,PlateLocSide,TaggedHitType,ExitSpeed\n"
            """Smith,TeamA,Single,,InPlay,2.5,0.0,LineDrive,invalid
                   Smith,TeamA,Double,,InPlay,2.5,0.0,LineDrive,95.5"""
        )
        buffer = io.StringIO(csv_data)

        result = get_batter_stats_from_buffer(buffer, "test.csv")
        stats = result[("Smith", "TeamA", 2025)]

        # Should only count valid exit speed
        assert stats["total_exit_velo"] == 95.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
