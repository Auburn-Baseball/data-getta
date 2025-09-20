import os
import ftplib
from dotenv import load_dotenv
from pathlib import Path
import re
from datetime import datetime
import concurrent.futures
import threading
from queue import Queue
import time

project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

TRACKMAN_URL = os.getenv("TRACKMAN_URL")
TRACKMAN_USERNAME = os.getenv("TRACKMAN_USERNAME")
TRACKMAN_PASSWORD = os.getenv("TRACKMAN_PASSWORD")

if not TRACKMAN_USERNAME or not TRACKMAN_PASSWORD:
    raise ValueError("TRACKMAN_USERNAME and TRACKMAN_PASSWORD must be set in .env file")

# Thread-local storage for FTP connections
thread_local = threading.local()

def get_ftp_connection():
    """Get thread-local FTP connection"""
    if not hasattr(thread_local, 'ftp'):
        try:
            thread_local.ftp = ftplib.FTP(TRACKMAN_URL)
            thread_local.ftp.login(TRACKMAN_USERNAME, TRACKMAN_PASSWORD)
        except Exception as e:
            print(f"Failed to connect in thread: {e}")
            thread_local.ftp = None
    return thread_local.ftp

def close_ftp_connection():
    """Close thread-local FTP connection"""
    if hasattr(thread_local, 'ftp') and thread_local.ftp:
        try:
            thread_local.ftp.quit()
        except:
            pass
        thread_local.ftp = None

def connect_to_ftp():
    """Connect to TrackMan FTP server (main thread)"""
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
        date_match = re.match(r"^(\d{8})", filename)
        if date_match:
            date_str = date_match.group(1)
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            return str(date_obj.year)
        return "unknown"
    except Exception as e:
        print(f"Error extracting year from filename {filename}: {e}")
        return "unknown"

def download_file_worker(file_info):
    """Worker function to download a single file"""
    remote_path, local_path, csv_file = file_info

    ftp = get_ftp_connection()
    if not ftp:
        return False, f"Could not establish FTP connection for {csv_file}"

    try:
        local_dir = os.path.dirname(local_path)
        Path(local_dir).mkdir(parents=True, exist_ok=True)

        # Navigate to the correct directory
        directory = os.path.dirname(remote_path)
        filename = os.path.basename(remote_path)

        ftp.cwd(directory)

        with open(local_path, "wb") as local_file:
            ftp.retrbinary(f"RETR {filename}", local_file.write)

        return True, f"Downloaded: {csv_file}"
    except Exception as e:
        return False, f"Error downloading {csv_file}: {e}"

def is_numeric_dir(name):
    """Check if directory name is numeric (year/month/day)"""
    return name.isdigit()

def is_csv_file(name):
    """Check if file is a CSV file"""
    return name.lower().endswith(".csv")

def collect_all_csv_files(ftp, base_path="/v3"):
    """Collect all CSV file information before downloading"""
    csv_files = []

    try:
        ftp.cwd(base_path)
        years = get_directory_list(ftp, base_path)
        years = [year for year in years if is_numeric_dir(year)]
        print(f"Found years: {years}")

        for year in years:
            year_path = f"{base_path}/{year}"
            print(f"Scanning year: {year}")

            months = get_directory_list(ftp, year_path)
            months = [month for month in months if is_numeric_dir(month)]

            for month in months:
                month_path = f"{year_path}/{month}"

                days = get_directory_list(ftp, month_path)
                days = [day for day in days if is_numeric_dir(day)]

                for day in days:
                    day_path = f"{month_path}/{day}"
                    csv_path = f"{day_path}/csv"

                    try:
                        ftp.cwd(csv_path)
                        files = get_directory_list(ftp, csv_path)
                        day_csv_files = [f for f in files if is_csv_file(f)]

                        for csv_file in day_csv_files:
                            file_year = extract_year_from_filename(csv_file)
                            remote_file_path = f"{csv_path}/{csv_file}"
                            local_file_path = os.path.join("csv", file_year, csv_file)

                            csv_files.append((remote_file_path, local_file_path, csv_file))

                        if day_csv_files:
                            print(f"Found {len(day_csv_files)} CSV files in {csv_path}")

                    except ftplib.error_perm as e:
                        if "550" in str(e):
                            continue  # No csv directory
                        else:
                            print(f"Error accessing {csv_path}: {e}")
                    except Exception as e:
                        print(f"Error processing {csv_path}: {e}")

    except Exception as e:
        print(f"Error collecting CSV files: {e}")

    return csv_files

def download_with_progress(csv_files, max_workers=5):
    """Download files with concurrent workers and progress tracking"""
    total_files = len(csv_files)
    completed = 0
    failed = 0

    print(f"\nStarting download of {total_files} files with {max_workers} concurrent workers...")

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all processing tasks
        future_to_file = {executor.submit(process_file_worker, file_info): file_info 
                         for file_info in csv_files}

        # Process completed downloads
        for future in concurrent.futures.as_completed(future_to_file):
            file_info = future_to_file[future]
            try:
                success, message = future.result()
                if success:
                    completed += 1
                    if completed % 10 == 0:  # Progress every 10 files
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        eta = (total_files - completed) / rate if rate > 0 else 0
                        print(f"Progress: {completed}/{total_files} ({completed/total_files*100:.1f}%) "
                              f"- Rate: {rate:.1f} files/sec - ETA: {eta:.0f}s")
                else:
                    failed += 1
                    print(f"FAILED: {message}")

            except Exception as e:
                failed += 1
                print(f"FAILED: Exception for {file_info[2]}: {e}")

    # Clean up thread-local connections
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(close_ftp_connection) for _ in range(max_workers)]
        concurrent.futures.wait(futures)

    elapsed = time.time() - start_time
    print(f"\nDownload completed!")
    print(f"Successfully downloaded: {completed} files")
    print(f"Failed downloads: {failed} files")
    print(f"Total time: {elapsed:.1f} seconds")
    print(f"Average rate: {completed/elapsed:.1f} files/second")

def main():
    # Create download directory
    download_dir = "csv"
    Path(download_dir).mkdir(exist_ok=True)

    # Connect and collect file list
    print("Connecting to FTP server and scanning for files...")
    ftp = connect_to_ftp()
    if not ftp:
        return

    try:
        # Collect all CSV files first
        csv_files = collect_all_csv_files(ftp, "/v3")
        print(f"\nFound {len(csv_files)} total CSV files to download")

        if not csv_files:
            print("No CSV files found!")
            return

        # Close main FTP connection before starting concurrent downloads
        ftp.quit()

        # Download with concurrent workers
        # Adjust max_workers based on your FTP server's limitations
        # Start conservative with 3-5 workers
        download_with_progress(csv_files, max_workers=4)

        print(f"\nAll files saved to: {download_dir}")

    except Exception as e:
        print(f"Error during download process: {e}")
    finally:
        try:
            ftp.quit()
        except:
            pass

if __name__ == "__main__":
    main()
