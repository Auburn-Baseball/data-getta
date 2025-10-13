"""
Unit tests for pitcher and batter pitch bin processing.

Run with: pytest test_pitch_bins.py -v
"""

import io
from datetime import date
from unittest.mock import Mock, patch

import pytest

from utils import (
    classify_13,
    get_batter_bins_from_buffer,
    get_pitcher_bins_from_buffer,
    norm_pitch_type,
    norm_side,
    upload_batter_pitch_bins,
    upload_pitcher_pitch_bins,
)


class TestPitchTypeNormalization:
    """Test pitch type canonicalization."""

    def test_four_seam_variations(self):
        """Test all variations of four-seam fastball."""
        assert norm_pitch_type("Four-Seam") == "FourSeam"
        assert norm_pitch_type("four seam") == "FourSeam"
        assert norm_pitch_type("FourSeam") == "FourSeam"
        assert norm_pitch_type("4-seam") == "FourSeam"
        assert norm_pitch_type("FF") == "FourSeam"
        assert norm_pitch_type("Fastball") == "FourSeam"
        assert norm_pitch_type("fb") == "FourSeam"

    def test_sinker_variations(self):
        """Test all variations of sinker/two-seam."""
        assert norm_pitch_type("Sinker") == "Sinker"
        assert norm_pitch_type("two-seam") == "Sinker"
        assert norm_pitch_type("Two Seam") == "Sinker"
        assert norm_pitch_type("SI") == "Sinker"

    def test_slider_variations(self):
        """Test slider variations."""
        assert norm_pitch_type("Slider") == "Slider"
        assert norm_pitch_type("SL") == "Slider"

    def test_curveball_variations(self):
        """Test curveball variations."""
        assert norm_pitch_type("Curveball") == "Curveball"
        assert norm_pitch_type("Curve") == "Curveball"
        assert norm_pitch_type("CU") == "Curveball"
        assert norm_pitch_type("Knuckle Curve") == "Curveball"

    def test_changeup_variations(self):
        """Test changeup variations."""
        assert norm_pitch_type("Changeup") == "Changeup"
        assert norm_pitch_type("Change") == "Changeup"
        assert norm_pitch_type("CH") == "Changeup"

    def test_cutter_variations(self):
        """Test cutter variations."""
        assert norm_pitch_type("Cutter") == "Cutter"
        assert norm_pitch_type("FC") == "Cutter"

    def test_splitter_variations(self):
        """Test splitter variations."""
        assert norm_pitch_type("Splitter") == "Splitter"
        assert norm_pitch_type("Split-Finger") == "Splitter"
        assert norm_pitch_type("FS") == "Splitter"
        assert norm_pitch_type("Forkball") == "Splitter"

    def test_unknown_pitch_type(self):
        """Test unknown pitch types default to 'Other'."""
        assert norm_pitch_type("Knuckleball") == "Other"
        assert norm_pitch_type("Screwball") == "Other"
        assert norm_pitch_type("???") == "Other"

    def test_non_string_input(self):
        """Test non-string input returns 'Other'."""
        assert norm_pitch_type(None) == "Other"
        assert norm_pitch_type(123) == "Other"

    def test_case_insensitivity(self):
        """Test that normalization is case-insensitive."""
        assert norm_pitch_type("SLIDER") == "Slider"
        assert norm_pitch_type("SLiDeR") == "Slider"


class TestBatterSideNormalization:
    """Test batter side normalization."""

    def test_left_handed_variations(self):
        """Test left-handed batter variations."""
        assert norm_side("L") == "L"
        assert norm_side("Left") == "L"
        assert norm_side("left") == "L"

    def test_right_handed_variations(self):
        """Test right-handed batter variations."""
        assert norm_side("R") == "R"
        assert norm_side("Right") == "R"
        assert norm_side("right") == "R"

    def test_unknown_defaults_to_right(self):
        """Test unknown values default to 'R' for DB constraint."""
        assert norm_side("") == "R"
        assert norm_side("unknown") == "R"
        assert norm_side(None) == "R"


class TestZoneClassification:
    """Test 13-zone classification (3x3 inner + 4 outer)."""

    def test_center_of_strike_zone(self):
        """Test center of zone is classified as zone 5 (middle-middle)."""
        result = classify_13(0.0, 2.5)
        assert result["InZone"] is True
        assert result["ZoneId"] == 5
        assert result["ZoneRow"] == 2
        assert result["ZoneCol"] == 2
        assert result["OuterLabel"] == "NA"

    def test_bottom_left_corner(self):
        """Test bottom-left corner (zone 1)."""
        result = classify_13(-0.8, 1.6)
        assert result["InZone"] is True
        assert result["ZoneId"] == 1
        assert result["ZoneRow"] == 1
        assert result["ZoneCol"] == 1

    def test_top_right_corner(self):
        """Test top-right corner (zone 9)."""
        result = classify_13(0.8, 3.4)
        assert result["InZone"] is True
        assert result["ZoneId"] == 9
        assert result["ZoneRow"] == 3
        assert result["ZoneCol"] == 3

    def test_outer_top_left_quadrant(self):
        """Test outer top-left quadrant (OTL = zone 10)."""
        result = classify_13(-1.5, 4.0)
        assert result["InZone"] is False
        assert result["ZoneId"] == 10
        assert result["OuterLabel"] == "OTL"

    def test_outer_top_right_quadrant(self):
        """Test outer top-right quadrant (OTR = zone 11)."""
        result = classify_13(1.5, 4.0)
        assert result["InZone"] is False
        assert result["ZoneId"] == 11
        assert result["OuterLabel"] == "OTR"

    def test_outer_bottom_left_quadrant(self):
        """Test outer bottom-left quadrant (OBL = zone 12)."""
        result = classify_13(-1.5, 1.0)
        assert result["InZone"] is False
        assert result["ZoneId"] == 12
        assert result["OuterLabel"] == "OBL"

    def test_outer_bottom_right_quadrant(self):
        """Test outer bottom-right quadrant (OBR = zone 13)."""
        result = classify_13(1.5, 1.0)
        assert result["InZone"] is False
        assert result["ZoneId"] == 13
        assert result["OuterLabel"] == "OBR"

    def test_all_nine_inner_zones(self):
        """Test that all 9 inner zones are reachable."""
        # Test coordinates for each zone
        test_coords = [
            (-0.5, 1.8, 1),  # Bottom-left
            (0.0, 1.8, 2),  # Bottom-middle
            (0.5, 1.8, 3),  # Bottom-right
            (-0.5, 2.5, 4),  # Middle-left
            (0.0, 2.5, 5),  # Middle-middle
            (0.5, 2.5, 6),  # Middle-right
            (-0.5, 3.2, 7),  # Top-left
            (0.0, 3.2, 8),  # Top-middle
            (0.5, 3.2, 9),  # Top-right
        ]

        for x, y, expected_zone in test_coords:
            result = classify_13(x, y)
            assert (
                result["ZoneId"] == expected_zone
            ), f"Coord ({x}, {y}) should be zone {expected_zone}, got {result['ZoneId']}"


class TestPitcherBinsFromBuffer:
    """Test pitcher pitch bins extraction from CSV buffer."""

    @pytest.fixture
    def mock_date_parser(self):
        """Mock date parser to return a fixed date."""
        with patch("utils.update_pitcher_pitch_bins_table.CSVFilenameParser") as mock:
            mock.return_value.get_date_object.return_value = date(2025, 3, 15)
            yield mock

    @pytest.fixture
    def simple_pitcher_csv(self):
        """Simple CSV with pitcher data."""
        csv_data = """Pitcher,PitcherTeam,BatterSide,AutoPitchType,PlateLocSide,PlateLocHeight
                   Smith,TeamA,R,Four-Seam,0.0,2.5
                   Smith,TeamA,L,Slider,-0.5,2.0
                   Smith,TeamA,R,Changeup,1.5,4.0"""
        return io.StringIO(csv_data)

    def test_basic_pitcher_bin_extraction(self, simple_pitcher_csv, mock_date_parser):
        """Test basic extraction of pitcher bins."""
        result = get_pitcher_bins_from_buffer(simple_pitcher_csv, "20250315-Stadium-1.csv")

        # Should have data for Smith
        assert len(result) > 0

        # Check that bins were created
        # At least one bin should exist
        sample_key = list(result.keys())[0]
        assert sample_key[0] == "TeamA"  # PitcherTeam
        assert sample_key[1] == "2025-03-15"  # Date as string
        assert sample_key[2] == "Smith"  # Pitcher

    def test_pitch_counts_by_type(self, simple_pitcher_csv, mock_date_parser):
        """Test that pitches are counted by type."""
        result = get_pitcher_bins_from_buffer(simple_pitcher_csv, "20250315-Stadium-1.csv")

        # Find the middle-middle zone bin for Smith
        middle_zone_key = None
        for key, data in result.items():
            if data["ZoneId"] == 5:  # Middle-middle zone
                middle_zone_key = key
                break

        if middle_zone_key:
            bin_data = result[middle_zone_key]
            # Should have counted the four-seam in middle
            assert bin_data["Count_FourSeam"] >= 1
            assert bin_data["TotalPitchCount"] >= 1

    def test_batter_side_split_counts(self, simple_pitcher_csv, mock_date_parser):
        """Test that pitches are split by batter side."""
        result = get_pitcher_bins_from_buffer(simple_pitcher_csv, "20250315-Stadium-1.csv")

        # Check that side-specific columns exist
        for bin_data in result.values():
            # Should have both L and R counts
            assert "Count_R_FourSeam" in bin_data
            assert "Count_L_FourSeam" in bin_data

    def test_outer_zone_classification(self, mock_date_parser):
        """Test that pitches outside zone are classified to outer zones."""
        csv_data = """Pitcher,PitcherTeam,BatterSide,AutoPitchType,PlateLocSide,PlateLocHeight
                   Smith,TeamA,R,Four-Seam,2.0,4.5"""
        buffer = io.StringIO(csv_data)

        result = get_pitcher_bins_from_buffer(buffer, "test.csv")

        # Should have an outer zone bin
        outer_zone_found = False
        for key, data in result.items():
            if data["ZoneId"] >= 10:  # Outer zones are 10-13
                outer_zone_found = True
                assert data["InZone"] is False
                break

        assert outer_zone_found, "Should have classified pitch to outer zone"

    def test_missing_columns_returns_empty(self, mock_date_parser):
        """Test that missing required columns returns empty dict."""
        csv_data = """Pitcher,PitcherTeam
                   Smith,TeamA"""
        buffer = io.StringIO(csv_data)

        result = get_pitcher_bins_from_buffer(buffer, "test.csv")
        assert result == {}

    def test_null_plate_location_skipped(self, mock_date_parser):
        """Test that rows with null plate locations are skipped."""
        csv_data = """Pitcher,PitcherTeam,BatterSide,AutoPitchType,PlateLocSide,PlateLocHeight
                   Smith,TeamA,R,Four-Seam,,
                   Smith,TeamA,R,Four-Seam,0.0,2.5"""
        buffer = io.StringIO(csv_data)

        result = get_pitcher_bins_from_buffer(buffer, "test.csv")

        # Should only process the second row
        total_pitches = sum(bin_data["TotalPitchCount"] for bin_data in result.values())
        assert total_pitches == 1


class TestBatterBinsFromBuffer:
    """Test batter pitch bins extraction from CSV buffer."""

    @pytest.fixture
    def mock_date_parser(self):
        """Mock date parser to return a fixed date."""
        with patch("utils.update_batter_pitch_bins_table.CSVFilenameParser") as mock:
            mock.return_value.get_date_object.return_value = date(2025, 3, 15)
            yield mock

    @pytest.fixture
    def simple_batter_csv(self):
        """Simple CSV with batter data."""
        csv_data = """Batter,BatterTeam,AutoPitchType,PlateLocSide,PlateLocHeight,PitchCall,PlayResult
                   Jones,TeamB,Four-Seam,0.0,2.5,StrikeSwinging,Strikeout
                   Jones,TeamB,Slider,-0.5,2.0,FoulBall,Foul
                   Jones,TeamB,Changeup,0.2,2.8,InPlay,Single"""
        return io.StringIO(csv_data)

    def test_basic_batter_bin_extraction(self, simple_batter_csv, mock_date_parser):
        """Test basic extraction of batter bins."""
        result = get_batter_bins_from_buffer(simple_batter_csv, "20250315-Stadium-1.csv")

        # Should have data for Jones
        assert len(result) > 0

        # Check structure
        sample_key = list(result.keys())[0]
        assert sample_key[0] == "TeamB"  # BatterTeam
        assert sample_key[1] == "2025-03-15"  # Date as string
        assert sample_key[2] == "Jones"  # Batter

    def test_swing_detection(self, simple_batter_csv, mock_date_parser):
        """Test that swings are detected correctly."""
        result = get_batter_bins_from_buffer(simple_batter_csv, "20250315-Stadium-1.csv")

        # Sum up all swings across all bins for Jones
        total_swings = sum(bin_data["TotalSwingCount"] for bin_data in result.values())
        # StrikeSwinging, FoulBall, and InPlay = 3 swings
        assert total_swings == 3

    def test_hit_detection(self, simple_batter_csv, mock_date_parser):
        """Test that hits are detected correctly."""
        result = get_batter_bins_from_buffer(simple_batter_csv, "20250315-Stadium-1.csv")

        # Sum up all hits
        total_hits = sum(bin_data["TotalHitCount"] for bin_data in result.values())
        # Only the Single counts as a hit
        assert total_hits == 1

    def test_pitch_type_counting(self, simple_batter_csv, mock_date_parser):
        """Test that pitch types are counted correctly."""
        result = get_batter_bins_from_buffer(simple_batter_csv, "20250315-Stadium-1.csv")

        # Check that pitch type columns exist and have counts
        for bin_data in result.values():
            assert "Count_FourSeam" in bin_data
            assert "Count_Slider" in bin_data
            assert "Count_Changeup" in bin_data

    def test_swing_counts_by_pitch_type(self, simple_batter_csv, mock_date_parser):
        """Test that swings are counted by pitch type."""
        result = get_batter_bins_from_buffer(simple_batter_csv, "20250315-Stadium-1.csv")

        # Check that swing count columns exist
        for bin_data in result.values():
            assert "SwingCount_FourSeam" in bin_data
            assert "SwingCount_Slider" in bin_data

    def test_hit_counts_by_pitch_type(self, simple_batter_csv, mock_date_parser):
        """Test that hits are counted by pitch type."""
        result = get_batter_bins_from_buffer(simple_batter_csv, "20250315-Stadium-1.csv")

        # Check that hit count columns exist
        for bin_data in result.values():
            assert "HitCount_FourSeam" in bin_data
            assert "HitCount_Changeup" in bin_data


class TestUploadFunctions:
    """Test upload functions for both pitcher and batter bins."""

    @pytest.fixture
    def sample_pitcher_bins(self):
        """Sample pitcher bin data."""
        return {
            ("TeamA", "2025-03-15", "Smith", 5): {
                "PitcherTeam": "TeamA",
                "Date": "2025-03-15",
                "Pitcher": "Smith",
                "ZoneId": 5,
                "InZone": True,
                "ZoneRow": 2,
                "ZoneCol": 2,
                "ZoneCell": 5,
                "OuterLabel": "NA",
                "ZoneVersion": "fixed_v3",
                "TotalPitchCount": 10,
                "Count_FourSeam": 8,
                "Count_Slider": 2,
            }
        }

    @pytest.fixture
    def sample_batter_bins(self):
        """Sample batter bin data."""
        return {
            ("TeamB", "2025-03-15", "Jones", 5): {
                "BatterTeam": "TeamB",
                "Date": "2025-03-15",
                "Batter": "Jones",
                "ZoneId": 5,
                "InZone": True,
                "TotalPitchCount": 15,
                "TotalSwingCount": 8,
                "TotalHitCount": 3,
            }
        }

    @patch("utils.update_pitcher_pitch_bins_table.supabase")
    def test_pitcher_upload_correct_table(self, mock_supabase, sample_pitcher_bins):
        """Test that pitcher bins upload to correct table."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitcher_pitch_bins(sample_pitcher_bins)

        # Verify correct table name
        mock_supabase.table.assert_called_with("PitcherPitchBins")

    @patch("utils.update_pitcher_pitch_bins_table.supabase")
    def test_pitcher_upload_correct_conflict_key(self, mock_supabase, sample_pitcher_bins):
        """Test that pitcher bins use correct conflict resolution."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitcher_pitch_bins(sample_pitcher_bins)

        # Verify conflict key
        call_kwargs = mock_table.upsert.call_args[1]
        assert call_kwargs["on_conflict"] == "PitcherTeam,Date,Pitcher,ZoneId"

    @patch("utils.update_batter_pitch_bins_table.supabase")
    def test_batter_upload_correct_table(self, mock_supabase, sample_batter_bins):
        """Test that batter bins upload to correct table."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_batter_pitch_bins(sample_batter_bins)

        # Verify correct table name
        mock_supabase.table.assert_called_with("BatterPitchBins")

    @patch("utils.update_batter_pitch_bins_table.supabase")
    def test_batter_upload_correct_conflict_key(self, mock_supabase, sample_batter_bins):
        """Test that batter bins use correct conflict resolution."""
        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_batter_pitch_bins(sample_batter_bins)

        # Verify conflict key
        call_kwargs = mock_table.upsert.call_args[1]
        assert call_kwargs["on_conflict"] == "BatterTeam,Date,Batter,ZoneId"

    @patch("utils.update_pitcher_pitch_bins_table.supabase")
    def test_upload_handles_empty_dict(self, mock_supabase):
        """Test that empty dictionary doesn't cause errors."""
        upload_pitcher_pitch_bins({})

        # Should not attempt to upload
        mock_supabase.table.assert_not_called()

    @patch("utils.update_pitcher_pitch_bins_table.supabase")
    def test_upload_batching_large_dataset(self, mock_supabase):
        """Test that large datasets are batched correctly."""
        # Create 2500 bins (should be 3 batches: 1000 + 1000 + 500)
        large_bins = {}
        for i in range(2500):
            large_bins[("Team", "2025-03-15", "Pitcher", i)] = {
                "PitcherTeam": "Team",
                "Date": "2025-03-15",
                "Pitcher": "Pitcher",
                "ZoneId": i % 13 + 1,
                "TotalPitchCount": 10,
            }

        mock_table = Mock()
        mock_upsert = Mock()

        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = Mock()

        upload_pitcher_pitch_bins(large_bins)

        # Should be called 3 times (1000 + 1000 + 500)
        assert mock_table.upsert.call_count == 3


class TestIntegration:
    """Integration tests combining multiple components."""

    @pytest.fixture
    def mock_date_parser(self):
        """Mock date parser."""
        with patch("utils.update_pitcher_pitch_bins_table.CSVFilenameParser") as mock:
            mock.return_value.get_date_object.return_value = date(2025, 3, 15)
            yield mock

    def test_full_pitcher_pipeline(self, mock_date_parser):
        """Test complete pipeline from CSV to upload-ready data."""
        csv_data = """Pitcher,PitcherTeam,BatterSide,AutoPitchType,PlateLocSide,PlateLocHeight
                   Smith,TeamA,R,Four-Seam,0.0,2.5
                   Smith,TeamA,R,Four-Seam,0.1,2.6
                   Smith,TeamA,L,Slider,-0.5,2.0
                   Jones,TeamA,R,Changeup,1.5,4.0"""
        buffer = io.StringIO(csv_data)

        result = get_pitcher_bins_from_buffer(buffer, "20250315-Stadium-1.csv")

        # Should have bins for both pitchers
        pitchers = set(key[2] for key in result.keys())
        assert "Smith" in pitchers
        assert "Jones" in pitchers

        # Verify data structure is upload-ready
        for bin_data in result.values():
            assert "PitcherTeam" in bin_data
            assert "Date" in bin_data
            assert "Pitcher" in bin_data
            assert "ZoneId" in bin_data
            assert "TotalPitchCount" in bin_data

            # Verify date is string
            assert isinstance(bin_data["Date"], str)

    def test_multiple_zones_same_pitcher(self, mock_date_parser):
        """Test that same pitcher can have multiple zone bins."""
        csv_data = """Pitcher,PitcherTeam,BatterSide,AutoPitchType,PlateLocSide,PlateLocHeight
                   Smith,TeamA,R,Four-Seam,0.0,2.5
                   Smith,TeamA,R,Slider,-0.7,2.0
                   Smith,TeamA,R,Changeup,2.0,4.5"""
        buffer = io.StringIO(csv_data)

        result = get_pitcher_bins_from_buffer(buffer, "test.csv")

        # Should have multiple bins for Smith (different zones)
        smith_bins = [key for key in result.keys() if key[2] == "Smith"]
        assert len(smith_bins) >= 2  # At least 2 different zones


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
