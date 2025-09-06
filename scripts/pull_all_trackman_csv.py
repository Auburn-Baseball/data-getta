import os
import ftplib
from dotenv import load_dotenv
from pathlib import Path
import re
from datetime import datetime

project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

TRACKMAN_URL = os.getenv("TRACKMAN_URL")
TRACKMAN_USERNAME = os.getenv("TRACKMAN_USERNAME")
TRACKMAN_PASSWORD = os.getenv("TRACKMAN_PASSWORD")

if not TRACKMAN_USERNAME or not TRACKMAN_PASSWORD:
    raise ValueError("TRACKMAN_USERNAME and TRACKMAN_PASSWORD must be set in .env file")


def connect_to_ftp():
    """Connect to TrackMan FTP server"""
    try:
        ftp = ftplib.FTP(TRACKMAN_URL)
        ftp.login(TRACKMAN_USERNAME, TRACKMAN_PASSWORD)
        print(f"Connected to {TRACKMAN_URL} as {TRACKMAN_USERNAME}")
        return ftp
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None


def get_directory_list(ftp, path):
    """Get list of directories/files in the given path"""
    try:
        items = []
        ftp.cwd(path)
        ftp.retrlines("LIST", items.append)
        names = []
        for item in items:
            parts = item.split()
            if len(parts) > 0:
                names.append(parts[-1])
        return names
    except Exception as e:
        print(f"Error listing directory {path}: {e}")
        return []


def extract_year_from_filename(filename):
    """Extract year from CSV filename like 20240426-FalconField-4.csv"""
    try:
        # Extract date part (first 8 characters should be YYYYMMDD)
        date_match = re.match(r"^(\d{8})", filename)
        if date_match:
            date_str = date_match.group(1)
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            return str(date_obj.year)
        return "unknown"
    except Exception as e:
        print(f"Error extracting year from filename {filename}: {e}")
        return "unknown"


def download_file(ftp, remote_path, local_path):
    """Download a file from FTP server"""
    try:
        local_dir = os.path.dirname(local_path)
        Path(local_dir).mkdir(parents=True, exist_ok=True)

        with open(local_path, "wb") as local_file:
            ftp.retrbinary(f"RETR {remote_path}", local_file.write)
        print(f"Downloaded: {remote_path} -> {local_path}")
        return True
    except Exception as e:
        print(f"Error downloading {remote_path}: {e}")
        return False


def is_numeric_dir(name):
    """Check if directory name is numeric (year/month/day)"""
    return name.isdigit()


def is_csv_file(name):
    """Check if file is a CSV file"""
    return name.lower().endswith(".csv")


def main():
    ftp = connect_to_ftp()
    if not ftp:
        return

    download_dir = "csv"
    Path(download_dir).mkdir(exist_ok=True)

    try:
        ftp.cwd("/v3")

        years = get_directory_list(ftp, "/v3")
        years = [year for year in years if is_numeric_dir(year)]
        print(f"Found years: {years}")

        for year in years:
            year_path = f"/v3/{year}"
            print(f"\nProcessing year: {year}")

            months = get_directory_list(ftp, year_path)
            months = [month for month in months if is_numeric_dir(month)]

            for month in months:
                month_path = f"{year_path}/{month}"
                print(f"Processing month: {month}")

                days = get_directory_list(ftp, month_path)
                days = [day for day in days if is_numeric_dir(day)]

                for day in days:
                    day_path = f"{month_path}/{day}"
                    csv_path = f"{day_path}/csv"

                    print(f"Processing day: {day}")

                    try:
                        ftp.cwd(csv_path)

                        files = get_directory_list(ftp, csv_path)
                        csv_files = [f for f in files if is_csv_file(f)]

                        print(f"Found {len(csv_files)} CSV files")

                        for csv_file in csv_files:
                            file_year = extract_year_from_filename(csv_file)

                            remote_file_path = f"{csv_path}/{csv_file}"
                            local_file_path = os.path.join(
                                download_dir, file_year, csv_file
                            )

                            download_file(ftp, remote_file_path, local_file_path)

                    except ftplib.error_perm as e:
                        if "550" in str(e):
                            print(f"No csv directory found for {day_path}")
                        else:
                            print(f"Error accessing {csv_path}: {e}")
                    except Exception as e:
                        print(f"Error processing {csv_path}: {e}")

        print(f"\nDownload completed! Files saved to: {download_dir}")

    except Exception as e:
        print(f"Error during download process: {e}")
    finally:
        ftp.quit()
        print("FTP connection closed")


if __name__ == "__main__":
    main()
