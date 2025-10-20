from utils.file_date import CSVFilenameParser


def test_parse_v3_filename():
    parser = CSVFilenameParser()
    filename = "20240216-Game-1.csv"
    date_obj = parser.parse_filename(filename)
    assert date_obj.year == 2024
    assert date_obj.month == 2
    assert date_obj.day == 16


def test_parse_practice_filename():
    parser = CSVFilenameParser()
    filename = "practice_2025-03-21T120000_summary.csv"
    date_obj = parser.parse_filename(filename)
    assert date_obj.year == 2025
    assert date_obj.month == 3
    assert date_obj.day == 21


def test_is_in_date_range_true():
    parser = CSVFilenameParser()
    filename = "20240216-Game-1.csv"
    assert parser.is_in_date_range(filename, "20240201-20240220")


def test_is_in_date_range_false():
    parser = CSVFilenameParser()
    filename = "20240216-Game-1.csv"
    assert not parser.is_in_date_range(filename, "20240101-20240131")
