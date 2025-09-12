#!/usr/bin/env python3
"""
Author: Joshua Henley
Created: 07 September 2025
Updated: 07 September 2025

Unified TrackMan CSV Processor
- Downloads CSV files from FTP concurrently
- Processes each file once through all update modules
- Tracks processed files to avoid duplicates
- Lets existing update modules handle all data processing and database operations
"""

import os
import ftplib
from dotenv import load_dotenv
from pathlib import Path
import re
from datetime import datetime
import concurrent.futures
import threading
from io import BytesIO
import time
import json
import hashlib
import sys

# Import your existing processing functions
from update_batters_table import get_batter_stats_from_buffer, upload_batters_to_supabase
from update_pitchers_table import get_pitcher_stats_from_buffer, upload_pitchers_to_supabase
from update_pitches_table import get_pitch_counts_from_buffer, upload_pitches_to_supabase
from update_players_table import get_players_from_buffer, upload_players_to_supabase

project_root = Path(__file__).parent.parent
env = os.getenv('ENV', 'development')
load_dotenv(project_root / f'.env.{env}')

TRACKMAN_URL = os.getenv("TRACKMAN_URL")
TRACKMAN_USERNAME = os.getenv("TRACKMAN_USERNAME")
TRACKMAN_PASSWORD = os.getenv("TRACKMAN_PASSWORD")


if not TRACKMAN_USERNAME or not TRACKMAN_PASSWORD:
    raise ValueError("TRACKMAN_USERNAME and TRACKMAN_PASSWORD must be set in .env file")

# File to track processed files
PROCESSED_FILES_LOG = "processed_files.json"

# Thread-local storage for FTP connections
thread_local = threading.local()

class ProcessedFilesTracker:
    """Tracks which files have been processed to avoid duplicates"""

    def __init__(self, log_file=PROCESSED_FILES_LOG):
        self.log_file = log_file
        self.processed_files = self._load_processed_files()
        self.lock = threading.Lock()

    def _load_processed_files(self):
        """Load processed files from JSON log"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load processed files log: {e}")
                return {}
        return {}

    def _save_processed_files(self):
        """Save processed files to JSON log"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.processed_files, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save processed files log: {e}")

    def _get_file_hash(self, remote_path: str, file_size: int = None, last_modified: str = None) -> str:
        """Generate a unique hash for file identification"""
        identifier = f"{remote_path}|{file_size}|{last_modified}"
        return hashlib.md5(identifier.encode()).hexdigest()

    def is_processed(self, remote_path: str, file_size: int = None, last_modified: str = None) -> bool:
        """Check if file has been processed before"""
        file_hash = self._get_file_hash(remote_path, file_size, last_modified)
        return file_hash in self.processed_files

    def mark_processed(self, remote_path: str, file_size: int = None, last_modified: str = None,
                      stats_summary: dict = None):
        """Mark file as processed"""
        with self.lock:
            file_hash = self._get_file_hash(remote_path, file_size, last_modified)
            self.processed_files[file_hash] = {
                'remote_path': remote_path,
                'file_size': file_size,
                'last_modified': last_modified,
                'processed_at': datetime.now().isoformat(),
                'stats_summary': stats_summary or {}
            }
            self._save_processed_files()

    def get_processed_count(self) -> int:
        """Get total number of processed files"""
        return len(self.processed_files)

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
    """Get list of directories/files with metadata"""
    try:
        items = []
        ftp.cwd(path)
        ftp.retrlines("LIST", items.append)

        files_info = []
        for item in items:
            parts = item.split()
            if len(parts) >= 9:
                filename = ' '.join(parts[8:])
                try:
                    size = int(parts[4]) if parts[4].isdigit() else None
                    date_info = ' '.join(parts[5:8])
                except:
                    size = None
                    date_info = None

                files_info.append({
                    'name': filename,
                    'size': size,
                    'date': date_info,
                    'is_dir': item.startswith('d')
                })

        return files_info
    except Exception as e:
        print(f"Error listing directory {path}: {e}")
        return []

def is_numeric_dir(name):
    """Check if directory name is numeric (year/month/day)"""
    return name.isdigit()

def is_csv_file(name):
    """Check if file is a CSV file and not excluded"""
    if not name.lower().endswith(".csv"):
        return False

    exclude_patterns = ["playerpositioning", "fhc", "unverified"]
    filename_lower = name.lower()
    return not any(pattern in filename_lower for pattern in exclude_patterns)

def extract_year_from_filename(filename):
    """Extract year from CSV filename"""
    try:
        date_match = re.match(r"^(\d{8})", filename)
        if date_match:
            date_str = date_match.group(1)
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            return str(date_obj.year)
        return "unknown"
    except Exception:
        return "unknown"

def collect_csv_file_info(ftp, tracker, base_path="/v3"):
    """Collect all CSV file information, filtering out already processed files"""
    csv_files = []
    skipped_files = 0

    try:
        years = [item['name'] for item in get_directory_list(ftp, base_path) 
                if item['is_dir'] and is_numeric_dir(item['name'])]
        print(f"Found years: {years}")

        for year in years:
            year_path = f"{base_path}/{year}"
            print(f"Scanning year: {year}")

            months = [item['name'] for item in get_directory_list(ftp, year_path)
                     if item['is_dir'] and is_numeric_dir(item['name'])]

            for month in months:
                month_path = f"{year_path}/{month}"

                days = [item['name'] for item in get_directory_list(ftp, month_path)
                       if item['is_dir'] and is_numeric_dir(item['name'])]

                for day in days:
                    day_path = f"{month_path}/{day}"
                    csv_path = f"{day_path}/csv"

                    try:
                        files_info = get_directory_list(ftp, csv_path)
                        day_csv_files = [f for f in files_info 
                                       if not f['is_dir'] and is_csv_file(f['name'])]

                        for file_info in day_csv_files:
                            csv_file = file_info['name']
                            remote_file_path = f"{csv_path}/{csv_file}"

                            # Check if already processed
                            if tracker.is_processed(remote_file_path, file_info['size'], file_info['date']):
                                skipped_files += 1
                                continue

                            file_entry = {
                                'remote_path': remote_file_path,
                                'filename': csv_file,
                                'size': file_info['size'],
                                'date': file_info['date']
                            }

                            csv_files.append(file_entry)

                        if day_csv_files:
                            new_count = len([f for f in day_csv_files
                                           if not tracker.is_processed(f'{csv_path}/{f["name"]}')])
                            print(f"Found {len(day_csv_files)} CSV files in {csv_path} ({new_count} new)")

                    except ftplib.error_perm as e:
                        if "550" not in str(e):
                            print(f"Error accessing {csv_path}: {e}")
                    except Exception as e:
                        print(f"Error processing {csv_path}: {e}")

    except Exception as e:
        print(f"Error collecting CSV files: {e}")

    print(f"\nFile Summary:")
    print(f"  New files to process: {len(csv_files)}")
    print(f"  Previously processed (skipped): {skipped_files}")

    return csv_files

def process_csv_worker(file_info, all_stats, tracker):
    """Download and process a single CSV file through all update modules"""
    ftp = get_ftp_connection()
    if not ftp:
        return False, f"Could not establish FTP connection for {file_info['filename']}"

    try:
        # Download to memory
        directory = os.path.dirname(file_info['remote_path'])
        filename = os.path.basename(file_info['remote_path'])

        ftp.cwd(directory)

        buffer = BytesIO()
        ftp.retrbinary(f"RETR {filename}", buffer.write)

        # Process through each module
        stats_summary = {}

        # Batters
        buffer.seek(0)
        try:
            batter_stats = get_batter_stats_from_buffer(buffer, file_info['filename'])
            all_stats['batters'].update(batter_stats)
            stats_summary['batters'] = len(batter_stats)
        except Exception as e:
            print(f"Error processing batter stats for {file_info['filename']}: {e}")
            stats_summary['batters'] = 0

        # Pitchers
        buffer.seek(0)
        try:
            pitcher_stats = get_pitcher_stats_from_buffer(buffer, file_info['filename'])
            all_stats['pitchers'].update(pitcher_stats)
            stats_summary['pitchers'] = len(pitcher_stats)
        except Exception as e:
            print(f"Error processing pitcher stats for {file_info['filename']}: {e}")
            stats_summary['pitchers'] = 0

        # Pitches
        buffer.seek(0)
        try:
            pitch_stats = get_pitch_counts_from_buffer(buffer, file_info['filename'])
            all_stats['pitches'].update(pitch_stats)
            stats_summary['pitches'] = len(pitch_stats)
        except Exception as e:
            print(f"Error processing pitch stats for {file_info['filename']}: {e}")
            stats_summary['pitches'] = 0

        # Players
        buffer.seek(0)
        try:
            player_stats = get_players_from_buffer(buffer, file_info['filename'])
            all_stats['players'].update(player_stats)
            stats_summary['players'] = len(player_stats)
        except Exception as e:
            print(f"Error processing player stats for {file_info['filename']}: {e}")
            stats_summary['players'] = 0

        # Mark as processed
        tracker.mark_processed(
            file_info['remote_path'],
            file_info['size'],
            file_info['date'],
            stats_summary
        )

        return True, f"Processed: {file_info['filename']} ({stats_summary})"

    except Exception as e:
        return False, f"Error processing {file_info['filename']}: {e}"

def process_with_progress(csv_files, tracker, max_workers=4):
    """Process files with concurrent workers and progress tracking"""
    if not csv_files:
        print("No new files to process!")
        return {}

    total_files = len(csv_files)
    completed = 0
    failed = 0

    # Initialize stats containers - just accumulate, don't merge
    all_stats = {
        'batters': {},
        'pitchers': {},
        'pitches': {},
        'players': {}
    }

    print(f"\nStarting processing of {total_files} files with {max_workers} concurrent workers...")
    start_time = time.time()

    # Using threads for concurrent processing to be more efficient
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all processing tasks
        future_to_file = {
            executor.submit(process_csv_worker, file_info, all_stats, tracker): file_info
            for file_info in csv_files
        }

        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_file):
            file_info = future_to_file[future]
            try:
                success, message = future.result()
                if success:
                    completed += 1
                    if completed % 10 == 0:
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
                print(f"FAILED: Exception for {file_info['filename']}: {e}")

    # Clean up connections
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(close_ftp_connection) for _ in range(max_workers)]
        concurrent.futures.wait(futures)

    elapsed = time.time() - start_time
    print(f"\nProcessing completed!")
    print(f"Successfully processed: {completed} files")
    print(f"Failed: {failed} files")
    print(f"Total time: {elapsed:.1f} seconds")
    if completed > 0:
        print(f"Average rate: {completed/elapsed:.1f} files/second")

    return all_stats

def upload_all_stats(all_stats):
    """Call each module's upload function with accumulated stats"""
    print("\n" + "="*50)
    print("UPLOADING TO DATABASE")
    print("="*50)

    if all_stats['batters']:
        print(f"\nUploading {len(all_stats['batters'])} batter records...")
        upload_batters_to_supabase(all_stats['batters'])

    if all_stats['pitchers']:
        print(f"\nUploading {len(all_stats['pitchers'])} pitcher records...")
        upload_pitchers_to_supabase(all_stats['pitchers'])

    if all_stats['pitches']:
        print(f"\nUploading {len(all_stats['pitches'])} pitch records...")
        upload_pitches_to_supabase(all_stats['pitches'])

    if all_stats['players']:
        print(f"\nUploading {len(all_stats['players'])} player records...")
        upload_players_to_supabase(all_stats['players'])

def main():
    """Main orchestrator function"""

    # Test mode to allow processing only 1 file
    test_mode = "--test" in sys.argv or os.getenv('TEST_MODE', 'false').lower() == 'true'

    print("="*60)
    print("UNIFIED TRACKMAN CSV PROCESSOR")
    if test_mode:
        print("*** TEST MODE - Processing only 1 file ***")
    print("="*60)


    # Initialize processed files tracker
    tracker = ProcessedFilesTracker()
    print(f"Previously processed files: {tracker.get_processed_count()}")

    # Connect to FTP and scan for files
    print("\nConnecting to FTP server and scanning for files...")
    ftp = connect_to_ftp()
    if not ftp:
        print("Failed to connect to FTP server")
        return

    try:
        # Collect new CSV files (filters out already processed)
        csv_files = collect_csv_file_info(ftp, tracker, "/v3")
        ftp.quit()

        if not csv_files:
            print("\nNo new files to process!")
            return

        if test_mode:
            csv_files = csv_files[:1]
            print(f"TEST MODE: Processing only the first file: {csv_files[0]['filename']}")

        # Process files concurrently
        all_stats = process_with_progress(csv_files, tracker, max_workers=6)

        # Upload to database
        upload_all_stats(all_stats)

        print(f"\n" + "="*60)
        print("PROCESSING COMPLETE")
        print(f"Total processed files: {tracker.get_processed_count()}")
        print("="*60)

    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        try:
            ftp.quit()
        except:
            pass

if __name__ == "__main__":
    main()
