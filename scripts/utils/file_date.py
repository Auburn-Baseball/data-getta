"""
Author: Joshua Henley
Created: 21 September 2025
Updated: 21 September 2025

FTP filename processor:
    This file is designed to provide
    the ability to pull the game data's
    date by processing the filename.

    There are two filename formats that are
    considered here when processing:

    YYYYMMDD-Description-Number.csv
    Prefix_YYYY-MM-DDTHHMMSS_suffix.csv

    The first format is used in the 'v3' directory
    of the FTP server, while the second format is
    used in the 'practice' directory.
"""

import re
from datetime import date, datetime
from typing import Optional, Tuple


class CSVFilenameParser:
    def __init__(self):
        # Pattern for format: YYYYMMDD-Description-Number.csv
        self.v3 = re.compile(r"^(\d{8})-.*\.csv$")

        # Pattern for format: Prefix_YYYY-MM-DDTHHMMSS_suffix.csv
        self.practice = re.compile(r"^.*_(\d{4}-\d{2}-\d{2})T\d{6}_.*\.csv$")

    def _extract_date_as_int(self, filename: str) -> int:
        """------------------------------------------------------
        Extract the date from a filename and return in the format YYYYMMDD

        Args:
            filename: The CSV filename to parse
        Returns:
            int of the file's date
        ------------------------------------------------------"""

        match_v3 = self.v3.match(filename)
        if match_v3:
            date_str = match_v3.group(1)
            try:
                date_int = int(date_str)
                # Validate the date value makes sense
                if self._is_valid_date_int(date_int):
                    return date_int
            except ValueError:
                pass

        match_practice = self.practice.match(filename)
        if match_practice:
            date_str = match_practice.group(1)
            try:
                # Convert "YYYY-MM-DD" into "YYYYMMDD"
                year, month, day = date_str.split("-")
                date_int = int(year + month + day)
                if self._is_valid_date_int(date_int):
                    return date_int
            except ValueError:
                pass

        return 0

    def _is_valid_date_int(self, date_int: int) -> bool:
        """----------------------------------------------------------
        Basic validation that the integer represents a reasonable date

        Args:
            date_int: int representing the file's date
        Returns:
            bool showing if the date makes sense or not
        ----------------------------------------------------------"""

        if date_int < 20000000 or date_int > 21001234:
            return False

        date_str = str(date_int).zfill(8)
        month = int(date_str[4:6])
        day = int(date_str[6:8])

        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False

        return True

    def _parse_date_range(self, date_range_str: str) -> Tuple[int, int]:
        """-----------------------------------------------------------------
        Parse YYYYMMDD-YYYYMMDD format into start and end integers

        Args:
            date_range_str: The date range received from the user
        Returns:
            tuple of the start and end date as integers formatted as YYYYMMDD
        -----------------------------------------------------------------"""

        if not re.match(r"^\d{8}-\d{8}$", date_range_str):
            raise ValueError(
                f"""Date range must be in format YYYYMMDD-YYYYMMDD,
                got: {date_range_str}"""
            )

        start_str, end_str = date_range_str.split("-")
        start_date = int(start_str)
        end_date = int(end_str)

        # Validate both dates
        if not self._is_valid_date_int(start_date):
            raise ValueError(f"Invalid start date: {start_str}")
        if not self._is_valid_date_int(end_date):
            raise ValueError(f"Invalid end date: {end_str}")
        if start_date > end_date:
            raise ValueError(
                f"""Start date ({start_str})
            cannot be after end date ({end_str})"""
            )

        return start_date, end_date

    def is_in_date_range(self, filename: str, date_range: str) -> bool:
        """----------------------------------------------------------
        Checks if date is in range

        Args:
            filename: filename with the date that needs to be checked
            date_range: date range provided by user
        Returns:
            bool showing if file date is within user-specified range
        ----------------------------------------------------------"""

        file_date = self._extract_date_as_int(filename)
        start_date, end_date = self._parse_date_range(date_range)

        return start_date <= file_date <= end_date

    def parse_filename(self, filename: str) -> Optional[datetime]:
        """------------------------------------------------------
        Parse filename and extract date.

        Args:
            filename: The CSV filename to parse
        Returns:
            datetime object if date found, None otherwise
        ------------------------------------------------------"""

        try:
            # Try format 1: YYYYMMDD-Description-Number.csv
            match1 = self.v3.match(filename)
            if match1:
                date_str = match1.group(1)
                try:
                    return datetime.strptime(date_str, "%Y%m%d")
                except ValueError:
                    pass

            # Try format 2: Prefix_YYYY-MM-DDTHHMMSS_suffix.csv
            match2 = self.practice.match(filename)
            if match2:
                date_str = match2.group(1)
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    pass
        except Exception as e:
            print(f"Error while parsing the filename: {e}")
            return datetime(2000, 1, 1)

    def get_date_components(self, filename: str) -> Tuple[int, int, int]:
        """-------------------------------------------------------------
        Get year, month, day components from filename.

        Args:
            filename: The CSV filename to parse
        Returns:
            Tuple of (year, month, day) if date found, None otherwise
        -------------------------------------------------------------"""

        try:
            date_obj = self.parse_filename(filename)
            if date_obj == datetime(2000, 1, 1):
                raise
            elif date_obj:
                return (date_obj.year, date_obj.month, date_obj.day)
        except Exception as e:
            print(f"Error while getting date components: {e}")
            return tuple(2000, 1, 1)

    def get_date_object(self, filename: str):
        """----------------------------------------------------------------
        Get the date of the file's game and return as a python date object.

        Args:
            filename: The CSV filename to parse
        Returns:
            Python date object (compatible with Supabase date object)
        ----------------------------------------------------------------"""

        date_obj = self.parse_filename(filename)
        try:
            return date(date_obj.year, date_obj.month, date_obj.day)
        except Exception as e:
            print(f"Error while getting the date as a date object: {e}")
        return None

    def filter_files_by_date(
        self,
        filenames: list,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
    ) -> list:
        """--------------------------------------------------
        Filter filenames by date criteria.

        Args:
            filenames: List of filenames to filter
            year: Year to filter by (optional)
            month: Month to filter by (optional)
            day: Day to filter by (optional)
        Returns:
            List of filenames matching the date criteria
        --------------------------------------------------"""

        filtered = []

        try:
            for filename in filenames:
                date_components = self.get_date_components(filename)
                if not date_components:
                    continue
                elif date_components == tuple(2000, 1, 1):
                    raise

                file_year, file_month, file_day = date_components

                # Check if file matches criteria
                if year is not None and file_year != year:
                    continue
                if month is not None and file_month != month:
                    continue
                if day is not None and file_day != day:
                    continue

                filtered.append(filename)

            return filtered
        except Exception as e:
            print(f"Error while filtering files by date: {e}")
