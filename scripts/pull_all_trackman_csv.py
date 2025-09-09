import os
import ftplib
from dotenv import load_dotenv
from pathlib import Path
import re
from datetime import datetime

# ----------------------------
# Project setup
# ----------------------------
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

TRACKMAN_URL = os.getenv("TRACKMAN_URL")
TRACKMAN_USERNAME = os.getenv("TRACKMAN_USERNAME")
TRACKMAN_PASSWORD = os.getenv("TRACKMAN_PASSWORD")

if not TRACKMAN_USERNAME or not TRACKMAN_PASSWORD:
    raise ValueError("TRACKMAN_USERNAME and TRACKMAN_PASSWORD must be set in .env file")

download_dir = "csv"
Path(download_dir).mkdir(exist_ok=True)

downloaded_log_path = Path("downloaded_files.txt")
downloaded_files = set()

# Load already downloaded files
if downloaded_log_path.exists():
    with open(downloaded_log_path, "r") as f:
        downloaded_files = set(line.strip() for line in f.readlines())

# ----------------------------
# FTP connection
# ----------------------------
def connect_to_ftp():
    try:
        ftp = ftplib.FTP(TRACKMAN_URL)
        ftp.login(TRACKMAN_USERNAME, TRACKMAN_PASSWORD)
        print(f"Connected to {TRACKMAN_URL} as {TRACKMAN_USERNAME}")
        return ftp
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

def get_directory_list(ftp, path):
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
    try:
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
    return name.isdigit()

def is_csv_file(name):
    return name.lower().endswith(".csv")

# ----------------------------
# Main workflow
# ----------------------------
def main():
    ftp = connect_to_ftp()
    if not ftp:
        return

    try:
        ftp.cwd("/v3")
        years = get_directory_list(ftp, "/v3")
        years = [y for y in years if is_numeric_dir(y)]
        print(f"Found years: {years}")

        for year in years:
            year_path = f"/v3/{year}"
            print(f"\nProcessing year: {year}")

            months = get_directory_list(ftp, year_path)
            months = [m for m in months if is_numeric_dir(m)]

            for month in months:
                month_path = f"{year_path}/{month}"
                print(f"Processing month: {month}")

                days = get_directory_list(ftp, month_path)
                days = [d for d in days if is_numeric_dir(d)]

                for day in days:
                    day_path = f"{month_path}/{day}"
                    csv_path = f"{day_path}/csv"
                    print(f"Processing day: {day}")

                    try:
                        ftp.cwd(csv_path)
                        files = get_directory_list(ftp, csv_path)
                        csv_files = [f for f in files if is_csv_file(f)]
                        print(f"Found {len(csv_files)} CSV files")

                        for csv_file in csv_files[:2]:
                            if csv_file in downloaded_files:
                                print(f"Skipping already downloaded file: {csv_file}")
                                continue

                            file_year = extract_year_from_filename(csv_file)
                            remote_file_path = f"{csv_path}/{csv_file}"
                            local_file_path = os.path.join(download_dir, file_year, csv_file)

                            if download_file(ftp, remote_file_path, local_file_path):
                                downloaded_files.add(csv_file)

                    except ftplib.error_perm as e:
                        if "550" in str(e):
                            print(f"No csv directory found for {day_path}")
                        else:
                            print(f"Error accessing {csv_path}: {e}")
                    except Exception as e:
                        print(f"Error processing {csv_path}: {e}")

        print(f"\nDownload completed! Files saved to: {download_dir}")

        # Update the downloaded files log
        with open(downloaded_log_path, "w") as f:
            for fname in sorted(downloaded_files):
                f.write(fname + "\n")

    except Exception as e:
        print(f"Error during download process: {e}")
    finally:
        ftp.quit()
        print("FTP connection closed")

if __name__ == "__main__":
    main()
