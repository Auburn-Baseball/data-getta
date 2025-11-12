"""
Author: Joshua Henley
Created: 31 October 2025

Unit test cases for file_date.py functions.
"""

import re
from datetime import date, datetime

import pytest

from scripts.utils.file_date import CSVFilenameParser


@pytest.fixture
def parser():
    """Fixture providing a CSVFilenameParser instance."""
    return CSVFilenameParser()


@pytest.fixture
def valid_filenames():
    return [
        "20251031-PlainsmanPark-Private-1_unverified.csv",
        "20120101-Name-name_verified.csv",
        "20220101-Something_verified.csv",
        "Batting_2022-01-01T023309_unverified.csv",
        "Batting_2012-01-01T000000_unverified.csv",
    ]


@pytest.fixture
def invalid_filenames():
    return [
        "202413011-Something_verified.csv",
        "2024132-Something_verified.csv",
        "2024132",
    ]


class TestDateFunctions:
    """Test all methods of file_date.py with successful responses"""

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("20251031-PlainsmanPark-Private-1_unverified.csv", 20251031),
            ("20000101-Name-name_verified.csv", 20000101),
            ("20220101-Something_verified.csv", 20220101),
            ("Batting_2022-01-01T023309_unverified.csv", 20220101),
            ("Batting_2000-01-01T000000_unverified.csv", 20000101),
            ("2000-01-01T000000_unverified.csv", 0),
            ("2000-01-01-game-verified.csv", 0),
            ("200001010-game-verified.csv", 0),
        ],
    )
    def test_extract_date_int(self, parser, filename, expected):
        response = parser._extract_date_as_int(filename)
        assert isinstance(response, int)
        assert response == expected

    @pytest.mark.parametrize(
        "date,expected",
        [
            (20000001, False),
            (20000100, False),
            (21001231, True),
            (21001234, False),
            (20220101, True),
            (19990101, False),
            (21111111, False),
            (20221301, False),
            (20220132, False),
        ],
    )
    def test_is_valid_date_int(self, parser, date, expected):
        response = parser._is_valid_date_int(date)
        assert isinstance(response, bool)
        assert response == expected

    @pytest.mark.parametrize(
        "date_range,expected_start,expected_end",
        [
            ("20000101-20240101", 20000101, 20240101),
            ("20220203-20220204", 20220203, 20220204),
            ("20201231-20211231", 20201231, 20211231),
        ],
    )
    def test_parse_date_range(self, parser, date_range, expected_start, expected_end):
        response = parser._parse_date_range(date_range)
        assert isinstance(response[0], int)
        assert isinstance(response[1], int)
        assert response[0] == expected_start
        assert response[1] == expected_end
        assert len(response) == 2

    @pytest.mark.parametrize(
        "filename,date_range,expected",
        [
            (
                "20251031-PlainsmanPark-Private-1_unverified.csv",
                "20240101-20251212",
                True,
            ),
            ("20000101-Name-name_verified.csv", "20221212-20231212", False),
            ("20220101-Something_verified.csv", "20120101-20130101", False),
            ("Batting_2022-01-01T023309_unverified.csv", "20210101-20230101", True),
            ("Batting_2000-01-01T000000_unverified.csv", "20110101-20120101", False),
        ],
    )
    def test_is_in_date_range(self, parser, filename, date_range, expected):
        response = parser.is_in_date_range(filename, date_range)
        assert isinstance(response, bool)
        assert response == expected

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("20251031-PlainsmanPark-Private-1_unverified.csv", datetime(2025, 10, 31)),
            ("20000101-Name-name_verified.csv", datetime(2000, 1, 1)),
            ("20220101-Something_verified.csv", datetime(2022, 1, 1)),
            ("Batting_2022-01-01T023309_unverified.csv", datetime(2022, 1, 1)),
            ("Batting_2000-01-01T000000_unverified.csv", datetime(2000, 1, 1)),
        ],
    )
    def test_parse_filename(self, parser, filename, expected):
        response = parser.parse_filename(filename)
        assert isinstance(response, datetime)
        assert response == expected

    @pytest.mark.parametrize(
        "filename,expected_year,expected_month,expected_day",
        [
            ("20251031-PlainsmanPark-Private-1_unverified.csv", 2025, 10, 31),
            ("20120101-Name-name_verified.csv", 2012, 1, 1),
            ("20220101-Something_verified.csv", 2022, 1, 1),
            ("Batting_2022-01-01T023309_unverified.csv", 2022, 1, 1),
            ("Batting_2012-01-01T000000_unverified.csv", 2012, 1, 1),
        ],
    )
    def test_get_date_components(
        self, parser, filename, expected_year, expected_month, expected_day
    ):
        response = parser.get_date_components(filename)
        assert isinstance(response[0], int)
        assert isinstance(response[1], int)
        assert isinstance(response[2], int)
        assert response[0] == expected_year
        assert response[1] == expected_month
        assert response[2] == expected_day

    @pytest.mark.parametrize(
        "year,month,day,expected_list",
        [
            (2025, 10, 31, ["20251031-PlainsmanPark-Private-1_unverified.csv"]),
            (
                2012,
                1,
                1,
                [
                    "20120101-Name-name_verified.csv",
                    "Batting_2012-01-01T000000_unverified.csv",
                ],
            ),
            (
                2022,
                1,
                1,
                [
                    "20220101-Something_verified.csv",
                    "Batting_2022-01-01T023309_unverified.csv",
                ],
            ),
            (2023, 1, 1, []),
            (2022, 1, 2, []),
            (
                None,
                1,
                1,
                [
                    "20120101-Name-name_verified.csv",
                    "20220101-Something_verified.csv",
                    "Batting_2022-01-01T023309_unverified.csv",
                    "Batting_2012-01-01T000000_unverified.csv",
                ],
            ),
            (
                2022,
                None,
                1,
                [
                    "20220101-Something_verified.csv",
                    "Batting_2022-01-01T023309_unverified.csv",
                ],
            ),
            (
                2022,
                1,
                None,
                [
                    "20220101-Something_verified.csv",
                    "Batting_2022-01-01T023309_unverified.csv",
                ],
            ),
        ],
    )
    def test_filter_files_by_date(self, parser, valid_filenames, year, month, day, expected_list):
        response = parser.filter_files_by_date(valid_filenames, year, month, day)
        assert isinstance(response, list)
        assert response == expected_list

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("20251031-PlainsmanPark-Private-1_unverified.csv", date(2025, 10, 31)),
            ("20120101-Name-name_verified.csv", date(2012, 1, 1)),
            ("20220101-Something_verified.csv", date(2022, 1, 1)),
            ("Batting_2022-01-01T023309_unverified.csv", date(2022, 1, 1)),
            ("Batting_2012-01-01T000000_unverified.csv", date(2012, 1, 1)),
        ],
    )
    def test_get_date_object(self, parser, filename, expected):
        response = parser.get_date_object(filename)
        assert isinstance(response, date)
        assert response == expected


class TestNegatives:
    """Test error handling in file_date.py functions"""

    # def test_extract_date_as_int_invalid(self, parser, filename):

    @pytest.mark.parametrize(
        "date_range",
        [
            "20221212-2022121",
            "2022121-20221212",
            "notnumss-20221212",
            "20221212-notnumss",
            "2022121220221212",
            "20221212",
            "-1",
            "apple",
        ],
    )
    def test_parse_date_range_invalid_range_format(self, parser, date_range):
        with pytest.raises(
            ValueError,
            match=f"Date range must be in format YYYYMMDD-YYYYMMDD, got: {date_range}",
        ):
            parser._parse_date_range(date_range)

    @pytest.mark.parametrize(
        "date_range",
        [
            "99999999-20220101",
            "00000000-20220101",
            "19990101-20230101",
            "20231301-20241212",
            "20231232-20241212",
        ],
    )
    def test_parse_date_range_invalid_start_date(self, parser, date_range):
        with pytest.raises(ValueError, match=f"Invalid start date: {date_range[0:7]}"):
            parser._parse_date_range(date_range)

    @pytest.mark.parametrize(
        "date_range",
        [
            "20230101-99999999",
            "20230101-00000000",
            "20230101-21401212",
            "20231231-20241312",
            "20231231-20241232",
        ],
    )
    def test_parse_date_range_invalid_end_date(self, parser, date_range):
        with pytest.raises(ValueError, match=f"Invalid end date: {date_range[9:-1]}"):
            parser._parse_date_range(date_range)

    @pytest.mark.parametrize(
        "date_range", ["20230101-20220101", "20120201-20120101", "20120102-20120101"]
    )
    def test_parse_date_range_start_date_after_end_date(self, parser, date_range):
        expected_msg = (
            f"Start date ({date_range[0:8]}) cannot be after end date ({date_range[9:17]})"
        )
        with pytest.raises(ValueError, match=re.escape(expected_msg)):
            parser._parse_date_range(date_range)

    @pytest.mark.parametrize(
        "filename",
        ["20241301-Something_verified.csv", "20241232-Something_verified.csv"],
    )
    def test_parse_filename_bad_value(self, parser, filename):
        assert parser.parse_filename(filename) == datetime(2000, 1, 1)

    @pytest.mark.parametrize(
        "filename",
        [
            "202413011-Something_verified.csv",
            "2024132-Something_verified.csv",
            "2024132",
        ],
    )
    def test_parse_filename_mismatched_format(self, parser, filename):
        assert parser.parse_filename(filename) == None

    def test_get_date_components_none(self, parser):
        assert parser.get_date_components("20000101-Something_verified.csv") == None

    @pytest.mark.parametrize(
        "filename",
        [
            "202413011-Something_verified.csv",
            "2024132-Something_verified.csv",
            "2024132",
        ],
    )
    def test_get_date_components_mismatched_format(self, parser, filename):
        assert parser.get_date_components(filename) == None

    @pytest.mark.parametrize(
        "filename",
        [
            "202413011-Something_verified.csv",
            "2024132-Something_verified.csv",
            "2024132",
        ],
    )
    def test_get_date_object_mismatched_format(self, parser, filename):
        assert parser.get_date_object(filename) == None

    def test_filter_files_by_date_mismatched_filename_format(self, parser, invalid_filenames):
        response = parser.filter_files_by_date(invalid_filenames, 2024, 13, 2)
        assert response == []
