"""
Author: Joshua Henley
Created: 31 October 2025

Unit test cases for file_date.py functions.
"""
import pytest

from utils.file_date import
(
CSVFilenameParser
)

@pytest.fixture
def parser():
    """Fixture providing a CSVFilenameParser instance."""
    return CSVFilenamParser()
