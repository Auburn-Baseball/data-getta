#!/usr/bin/env python3
"""
Author: Joshua Henley
Created: 07 September 2025
Updated: 14 October 2025

Unified TrackMan CSV Processor - Database Tracking Version
- Downloads CSV files from FTP server concurrently
- Processes each file once through all update modules
- Tracks processed files in database to avoid duplicates
- Works in containerized environments (Docker/GitLab Actions)
- Supports test mode and date range filteringSupports test mode and date range filteringSupports test mode and date range filteringSupports test mode and date range filteringSupports test mode and date range filteringSupports test mode and date range filteringSupports test mode and date range filteringSupports test mode and date range filtering
"""

import concurrent.futures
import ftplib
import hashlib
import os
import sys
import threading
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

# Import your existing processing functions
from utils import (
    CSVFilenameParser,
    combine_advanced_batting_stats,
    get_advanced_batting_stats_from_buffer,
    get_batter_bins_from_buffer,
    get_batter_stats_from_buffer,
    get_pitch_counts_from_buffer,
    get_pitcher_bins_from_buffer,
    get_pitcher_stats_from_buffer,
    get_players_from_buffer,
    upload_advanced_batting_to_supabase,
    upload_batter_pitch_bins,
    upload_batters_to_supabase,
    upload_pitcher_pitch_bins,
    upload_pitchers_to_supabase,
    upload_pitches_to_supabase,
    upload_players_to_supabase,
)

project_root = Path(__file__).parent.parent
env = os.getenv("ENV", "development")
load_dotenv(project_root / f".env.{env}")

# FTP Configuration
TRACKMAN_URL = os.getenv("TRACKMAN_URL")
TRACKMAN_USERNAME = os.getenv("TRACKMAN_USERNAME")
TRACKMAN_PASSWORD = os.getenv("TRACKMAN_PASSWORD")

# Supabase Configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")

if not TRACKMAN_USERNAME or not TRACKMAN_PASSWORD:
    raise ValueError("TRACKMAN_USERNAME and TRACKMAN_PASSWORD must be set in .env file")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_PROJECT_URL and SUPABASE_API_KEY must be set in .env file")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Thread-local storage for FTP connections
thread_local = threading.local()


class DatabaseProcessedFilesTracker:
    """---------------------------------------------------------------
    Loads the ProcessedFiles table into memory in order to efficiently
    check for new files that need to be processed.
    Prints all csv files found in the ftp server as well as whether or
    not they have already been processed.
    -------------------------------------------------------------------"""

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.lock = threading.Lock()
        self._processed_hashes_cache = None
        self._cache_loaded = False

    def _get_file_hash(
        self, remote_path: str, file_size: int = None, last_modified: str = None
    ) -> str:
        """---------------------------------------------------------------
        Generate a unique hash for file identification using the file size,
        remote path, and last time modified.
        -------------------------------------------------------------------"""
        identifier = f"{remote_path}|{file_size}|{last_modified}"
        return hashlib.md5(identifier.encode()).hexdigest()

    def _load_all_processed_hashes(self, batch_size=1000):
        """
        ---------------------------------------------------------------
        Load all processed file hashes into memory cache for fast lookups.
        Handles Supabase row limits by fetching in batches.
        -------------------------------------------------------------------
        """
        if self._cache_loaded:
            return

        self._processed_hashes_cache = set()
        try:
            print("Loading processed files cache from database...")

            offset = 0
            while True:
                # Fetch a batch of rows
                result = (
                    self.supabase.table("ProcessedFiles")
                    .select("file_hash")
                    .range(offset, offset + batch_size - 1)  # Supabase uses inclusive range
                    .execute()
                )

                data = result.data
                if not data:
                    break  # No more rows to fetch

                # Add hashes to cache
                self._processed_hashes_cache.update(row["file_hash"] for row in data)

                print(
                    f"Loaded batch of {len(data)} rows"
                    f"(total so far: {len(self._processed_hashes_cache)})"
                )

                # Increment offset
                offset += batch_size

            self._cache_loaded = True
            print(
                f"Finished loading {len(self._processed_hashes_cache)} processed files into cache"
            )

        except Exception as e:
            print(f"Error loading processed files cache: {e}")
            self._processed_hashes_cache = set()
            self._cache_loaded = True

    def is_processed(
        self, remote_path: str, file_size: int = None, last_modified: str = None
    ) -> bool:
        """---------------------------------------------------------------
        Check if file has been processed using in-memory cache.
        -------------------------------------------------------------------"""
        if not self._cache_loaded:
            self._load_all_processed_hashes()

        file_hash = self._get_file_hash(remote_path, file_size, last_modified)
        return file_hash in self._processed_hashes_cache

    def mark_processed(
        self,
        remote_path: str,
        file_size: int = None,
        last_modified: str = None,
        stats_summary: dict = None,
    ):
        """---------------------------------------------------------------
        Mark file as processed in database and update cache.
        -------------------------------------------------------------------"""
        with self.lock:
            file_hash = self._get_file_hash(remote_path, file_size, last_modified)

            try:
                data = {
                    "file_hash": file_hash,
                    "remote_path": remote_path,
                    "file_size": file_size,
                    "last_modified": last_modified,
                    "processed_at": datetime.now().isoformat(),
                    "stats_summary": stats_summary or {},
                }

                # Use upsert in case of duplicates
                result = (
                    self.supabase.table("ProcessedFiles")
                    .upsert(data, on_conflict="file_hash")
                    .execute()
                )

                data = result.data
                if not data:
                    print(
                        "Error while uploading processed file to database:" "No result from upsert"
                    )

                # Update cache
                if self._processed_hashes_cache is not None:
                    self._processed_hashes_cache.add(file_hash)

                return True

            except Exception as e:
                print(f"Error marking file as processed: {e}")
                return False

    def get_processed_count(self) -> int:
        """---------------------------------------------------------------
        Get total number of processed files.
        -------------------------------------------------------------------"""
        if not self._cache_loaded:
            self._load_all_processed_hashes()
        return len(self._processed_hashes_cache) if self._processed_hashes_cache else 0

    def invalidate_cache(self):
        """---------------------------------------------------------------
        Force reload of cache on next access.
        -------------------------------------------------------------------"""
        self._cache_loaded = False
        self._processed_hashes_cache = None

    def get_processed_files_info(self) -> list:
        """---------------------------------------------------------------
        Get info about all processed files.
        -------------------------------------------------------------------"""
        try:
            result = (
                self.supabase.table("ProcessedFiles")
                .select("*")
                .order("processed_at", desc=True)
                .execute()
            )
            return result.data
        except Exception as e:
            print(f"Error getting processed files info: {e}")
            return []

    def get_recent_files(self, limit: int = 10) -> list:
        """---------------------------------------------------------------
        Get most recently processed files.
        -------------------------------------------------------------------"""
        try:
            result = (
                self.supabase.table("ProcessedFiles")
                .select("remote_path, processed_at, stats_summary")
                .order("processed_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        except Exception as e:
            print(f"Error getting recent files: {e}")
            return []


def get_ftp_connection():
    """---------------------------------------------------------------
    Get thread-local FTP connection.
    -------------------------------------------------------------------"""
    if not hasattr(thread_local, "ftp"):
        try:
            thread_local.ftp = ftplib.FTP(TRACKMAN_URL)
            thread_local.ftp.login(TRACKMAN_USERNAME, TRACKMAN_PASSWORD)
        except Exception as e:
            print(f"Failed to connect in thread: {e}")
            thread_local.ftp = None
    return thread_local.ftp


def close_ftp_connection():
    """---------------------------------------------------------------
    Close thread-local FTP connection.
    -------------------------------------------------------------------"""
    if hasattr(thread_local, "ftp") and thread_local.ftp:
        try:
            thread_local.ftp.quit()
        except Exception:
            pass
        thread_local.ftp = None


def connect_to_ftp():
    """---------------------------------------------------------------
    Connect to TrackMan FTP server (main thread).
    -------------------------------------------------------------------"""
    try:
        ftp = ftplib.FTP(TRACKMAN_URL)
        ftp.login(TRACKMAN_USERNAME, TRACKMAN_PASSWORD)
        print(f"Connected to {TRACKMAN_URL} as {TRACKMAN_USERNAME}")
        return ftp
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None


def get_directory_list(ftp, path):
    """---------------------------------------------------------------
    Get list of directories/files with metadata.
    -------------------------------------------------------------------"""
    try:
        items = []
        ftp.cwd(path)
        ftp.retrlines("LIST", items.append)

        files_info = []
        for item in items:
            parts = item.split()
            if len(parts) >= 9:
                filename = " ".join(parts[8:])
                try:
                    size = int(parts[4]) if parts[4].isdigit() else None
                    date_info = " ".join(parts[5:8])
                except Exception:
                    size = None
                    date_info = None

                files_info.append(
                    {
                        "name": filename,
                        "size": size,
                        "date": date_info,
                        "is_dir": item.startswith("d"),
                    }
                )

        return files_info
    except Exception as e:
        print(f"Error listing directory {path}: {e}")
        return []


def is_numeric_dir(name):
    """---------------------------------------------------------------
    Check if directory name is numeric (year/month/day).
    -------------------------------------------------------------------"""
    return name.isdigit()


def is_csv_file(name):
    """---------------------------------------------------------------
    Check if file is a CSV file and not excluded.
    -------------------------------------------------------------------"""
    if not name.lower().endswith(".csv"):
        return False

    exclude_patterns = ["playerpositioning", "fhc"]
    filename_lower = name.lower()
    return not any(pattern in filename_lower for pattern in exclude_patterns)


def collect_csv_file_info(ftp, tracker, date_range="20200101-20990101", base_path="/v3"):
    """---------------------------------------------------------------
    Collect all CSV file information, filtering out already processed
    files using database.
    -------------------------------------------------------------------"""
    csv_files = []
    skipped_files = 0
    in_date_range = 0
    out_date_range = 0

    try:
        years = [
            item["name"]
            for item in get_directory_list(ftp, base_path)
            if item["is_dir"] and is_numeric_dir(item["name"])
        ]
        print(f"Found years: {years}")

        for year in years:
            year_path = f"{base_path}/{year}"
            print(f"Scanning year: {year}")

            months = [
                item["name"]
                for item in get_directory_list(ftp, year_path)
                if item["is_dir"] and is_numeric_dir(item["name"])
            ]

            for month in months:
                month_path = f"{year_path}/{month}"

                days = [
                    item["name"]
                    for item in get_directory_list(ftp, month_path)
                    if item["is_dir"] and is_numeric_dir(item["name"])
                ]

                for day in days:
                    day_path = f"{month_path}/{day}"
                    csv_path = f"{day_path}/csv"

                    try:
                        files_info = get_directory_list(ftp, csv_path)
                        day_csv_files = [
                            f for f in files_info if not f["is_dir"] and is_csv_file(f["name"])
                        ]
                        file_date_parser = CSVFilenameParser()

                        for file_info in day_csv_files:
                            csv_file = file_info["name"]
                            remote_file_path = f"{csv_path}/{csv_file}"

                            # Check if the file is in the user-specified date range
                            if date_range:
                                if not file_date_parser.is_in_date_range(csv_file, date_range):
                                    out_date_range += 1
                                    continue
                            in_date_range += 1

                            # Check database if the file has already been processed
                            if tracker.is_processed(
                                remote_file_path, file_info["size"], file_info["date"]
                            ):
                                skipped_files += 1
                                continue

                            file_entry = {
                                "remote_path": remote_file_path,
                                "filename": csv_file,
                                "size": file_info["size"],
                                "date": file_info["date"],
                            }

                            csv_files.append(file_entry)

                        if day_csv_files:
                            new_count = len(
                                [
                                    f
                                    for f in day_csv_files
                                    if not tracker.is_processed(f'{csv_path}/{f["name"]}')
                                ]
                            )
                            if new_count > 0:
                                print(
                                    f"Found {len(day_csv_files)}"
                                    f"CSV files in {csv_path} ({new_count} new)"
                                )

                    except ftplib.error_perm as e:
                        if "550" not in str(e):
                            print(f"Error accessing {csv_path}: {e}")
                    except Exception as e:
                        print(f"Error processing {csv_path}: {e}")

    except Exception as e:
        print(f"Error collecting CSV files: {e}")

    print("\nFile Summary:")
    print(f"  Files found inside date range: {in_date_range}")
    print(f"  New files to process: {len(csv_files)}")
    print(f"  Previously processed (skipped): {skipped_files}")
    print(f"  # of files outside of date range (skipped): {out_date_range}")

    return csv_files


def process_csv_worker(file_info, all_stats, tracker):
    """---------------------------------------------------------------
    Download and process a single CSV file through all update modules.
    -------------------------------------------------------------------"""
    ftp = get_ftp_connection()
    if not ftp:
        return False, f"Could not establish FTP connection for {file_info['filename']}"

    try:
        # Download to memory
        directory = os.path.dirname(file_info["remote_path"])
        filename = os.path.basename(file_info["remote_path"])

        ftp.cwd(directory)

        buffer = BytesIO()
        ftp.retrbinary(f"RETR {filename}", buffer.write)

        # If file is unverified, check if it's practice before skipping/processing it
        if "unverified" in filename.lower():
            buffer.seek(0)
            try:
                df = pd.read_csv(buffer)
                is_practice = False
                if "League" in df.columns:
                    league_values = df["League"].dropna().astype(str).str.strip().str.upper()
                    is_practice = (league_values == "TEAM").any()

                # If it's not practice, skip this file and mark as processed
                if not is_practice:
                    tracker.mark_processed(
                        file_info["remote_path"],
                        file_info["size"],
                        file_info["date"],
                        {"skipped": "unverified_non_practice"},
                    )
                    return True, f"Skipped (unverified non-practice): {filename}"
            except Exception as e:
                return False, f"Error checking unverified file {filename}: {e}"

            # Reset buffer for processing
            buffer.seek(0)

        # Process through each module
        stats_summary = {}

        # Batters
        buffer.seek(0)
        try:
            batter_stats = get_batter_stats_from_buffer(buffer, file_info["filename"])
            all_stats.setdefault("batter_stats", {})

            # Add new stats into all_stats['batter_stats']
            for key, row in batter_stats.items():
                # key = (BatterTeam, Date, Batter)
                team, date, batter = key
                key_out = (batter, team, date)
                all_stats["batter_stats"][key_out] = row

            stats_summary["batter_stats"] = len(all_stats["batter_stats"])

        except Exception as e:
            print(f"Error processing batter stats for {file_info['filename']}: {e}")
            stats_summary["batter_stats"] = 0

        # Pitchers
        buffer.seek(0)
        try:
            pitcher_stats = get_pitcher_stats_from_buffer(buffer, file_info["filename"])
            all_stats.setdefault("pitcher_stats", {})

            # Add new stats into all_stats['pitcher_stats']
            for key, row in pitcher_stats.items():
                # key = (PitcherTeam, Date, Pitcher)
                team, date, pitcher = key
                key_out = (pitcher, team, date)
                all_stats["pitcher_stats"][key_out] = row

            stats_summary["pitcher_stats"] = len(all_stats["pitcher_stats"])

        except Exception as e:
            print(f"Error processing pitcher stats for {file_info['filename']}: {e}")
            stats_summary["pitcher_stats"] = 0

        # Pitches
        buffer.seek(0)
        try:
            pitch_counts = get_pitch_counts_from_buffer(buffer, file_info["filename"])
            all_stats.setdefault("pitch_counts", {})

            # Add new stats into all_stats['pitch_counts']
            for key, row in pitch_counts.items():
                # key = (PitcherTeam, Date, Pitcher)
                team, date, pitcher = key
                key_out = (pitcher, team, date)
                all_stats["pitch_counts"][key_out] = row

            stats_summary["pitch_counts"] = len(all_stats["pitch_counts"])

        except Exception as e:
            print(f"Error processing pitch counts for {file_info['filename']}: {e}")
            stats_summary["pitch_counts"] = 0

        # Players
        buffer.seek(0)
        try:
            players = get_players_from_buffer(buffer, file_info["filename"])
            all_stats.setdefault("players", {})

            # Add new stats into all_stats['players']
            for key, row in players.items():
                # key = (TeamTrackmanAbbreviation, Year, Name)
                team, year, name = key
                key_out = (name, team, year)
                all_stats["players"][key_out] = row

            stats_summary["players"] = len(all_stats["players"])

        except Exception as e:
            print(f"Error processing player stats for {file_info['filename']}: {e}")
            stats_summary["players"] = 0

        # Advanced Batting
        buffer.seek(0)
        try:
            advanced_batting_stats = get_advanced_batting_stats_from_buffer(
                buffer, file_info["filename"]
            )

            # Merge new stats into existing ones
            for key, new_stat in advanced_batting_stats.items():
                if key in all_stats["advanced_batting"]:
                    combined = combine_advanced_batting_stats(
                        all_stats["advanced_batting"][key], new_stat
                    )
                    all_stats["advanced_batting"][key] = combined
                else:
                    all_stats["advanced_batting"][key] = new_stat

            stats_summary["advanced_batting"] = len(all_stats["advanced_batting"])

        except Exception as e:
            print(f"Error processing advanced batting stats for {file_info['filename']}: {e}")
            stats_summary["advanced_batting"] = 0

        # Batter pitch bins (heatmaps)
        buffer.seek(0)
        try:
            batter_pitch_bins = get_batter_bins_from_buffer(buffer, file_info["filename"])
            all_stats.setdefault("batter_pitch_bins", {})

            # Add new stats into all_stats['batter_pitch_bins']
            for key, row in batter_pitch_bins.items():
                # key = (BatterTeam, Date, Batter, ZoneId)
                team, date, batter, zone_id = key
                key_out = (batter, team, date, zone_id)
                all_stats["batter_pitch_bins"][key_out] = row

            stats_summary["batter_pitch_bins"] = len(all_stats["batter_pitch_bins"])

        except Exception as e:
            print(f"Error processing batter pitch bin stats for {file_info['filename']}: {e}")
            stats_summary["batter_pitch_bins"] = 0

        # Pitcher pitch bins (heatmaps)
        buffer.seek(0)
        try:
            pitcher_pitch_bins = get_pitcher_bins_from_buffer(buffer, file_info["filename"])
            all_stats.setdefault("pitcher_pitch_bins", {})

            # Add new stats into all_stats['pitcher_pitch_bins']
            for key, row in pitcher_pitch_bins.items():
                # key = (PitcherTeam, Date, Pitcher, ZoneId)
                team, date, pitcher, zone_id = key
                key_out = (pitcher, team, date, zone_id)
                all_stats["pitcher_pitch_bins"][key_out] = row

            stats_summary["pitcher_pitch_bins"] = len(all_stats["pitcher_pitch_bins"])

        except Exception as e:
            print(f"Error processing pitcher pitch bin stats for {file_info['filename']}: {e}")
            stats_summary["pitcher_pitch_bins"] = 0

        # Mark as processed in database
        tracker.mark_processed(
            file_info["remote_path"], file_info["size"], file_info["date"], stats_summary
        )

        return True, f"Processed: {file_info['filename']} ({stats_summary})"

    except Exception as e:
        return False, f"Error processing {file_info['filename']}: {e}"


def process_with_progress(csv_files, tracker, max_workers=4):
    """---------------------------------------------------------------
    Process files with concurrent workers and progress tracking.
    -------------------------------------------------------------------"""
    if not csv_files:
        print("No new files to process!")
        return {}

    total_files = len(csv_files)
    completed = 0
    failed = 0

    # Initialize stats containers - just accumulate, don't merge
    all_stats = {
        "batter_stats": {},
        "pitcher_stats": {},
        "pitch_counts": {},
        "players": {},
        "advanced_batting": {},
        "batter_pitch_bins": {},
        "pitcher_pitch_bins": {},
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
                        print(
                            f"Progress: {completed}/{total_files}"
                            f"({completed/total_files*100:.1f}%) "
                            f"- Rate: {rate:.1f} files/sec - ETA: {eta:.0f}s"
                        )
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
    print("\nProcessing completed!")
    print(f"Successfully processed: {completed} files")
    print(f"Failed: {failed} files")
    print(f"Total time: {elapsed:.1f} seconds")
    if completed > 0:
        print(f"Average rate: {completed/elapsed:.1f} files/second")

    return all_stats


def upload_all_stats(all_stats):
    """---------------------------------------------------------------
    Call each module's upload function with accumulated stats.
    -------------------------------------------------------------------"""
    print("\n" + "=" * 50)
    print("UPLOADING TO DATABASE")
    print("=" * 50)

    if all_stats["batter_stats"]:
        print(f"\nUploading {len(all_stats['batter_stats'])} batter stat records...")
        upload_batters_to_supabase(all_stats["batter_stats"])
    else:
        print("No new batter stats to upload.")

    if all_stats["pitcher_stats"]:
        print(f"\nUploading {len(all_stats['pitcher_stats'])} pitcher stat records...")
        upload_pitchers_to_supabase(all_stats["pitcher_stats"])
    else:
        print("No new pitcher stats to upload.")

    if all_stats["pitch_counts"]:
        print(f"\nUploading {len(all_stats['pitch_counts'])} pitch count records...")
        upload_pitches_to_supabase(all_stats["pitch_counts"])
    else:
        print("No new pitch count stats to upload.")

    if all_stats["players"]:
        print(f"\nUploading {len(all_stats['players'])} player records...")
        upload_players_to_supabase(all_stats["players"])
    else:
        print("No new player stats to upload.")

    if all_stats["advanced_batting"]:
        print(f"\nUploading {len(all_stats['advanced_batting'])} advanced batting records...")
        upload_advanced_batting_to_supabase(all_stats["advanced_batting"])
    else:
        print("No new advanced batting stats to upload.")

    if all_stats["batter_pitch_bins"]:
        print(f"\nUploading {len(all_stats['batter_pitch_bins'])} batter pitch bin records...")
        upload_batter_pitch_bins(all_stats["batter_pitch_bins"])
    else:
        print("No new batter pitch bin stats to upload.")

    if all_stats["pitcher_pitch_bins"]:
        print(f"\nUploading {len(all_stats['pitcher_pitch_bins'])} pitcher pitch bin records...")
        upload_pitcher_pitch_bins(all_stats["pitcher_pitch_bins"])
    else:
        print("No new pitcher pitch bin stats to upload.")


def main():
    # Get test flag
    test_mode = "--test" in sys.argv or os.getenv("TEST_MODE", "false").lower() == "true"
    # Get date range if set
    date_range = None
    for i, arg in enumerate(sys.argv):
        if arg == "--date-range" and i + 1 < len(sys.argv):
            date_range = sys.argv[i + 1]
            break

    print("=" * 60)
    print("UNIFIED TRACKMAN CSV PROCESSOR - DATABASE TRACKING")
    if test_mode:
        print("*** TEST MODE - Processing only 1 file ***")
    if date_range:
        print(
            "*** Processing only files in the following"
            f"range (YYYYMMDD - YYYYMMDD): {date_range} ***"
        )
    print("=" * 60)
    print("")

    # Initialize database-based processed files tracker
    tracker = DatabaseProcessedFilesTracker(supabase)
    processed_count = tracker.get_processed_count()
    print(f"Previously processed files: {processed_count}")

    # Show some recent files for debugging
    if processed_count > 0:
        recent_files = tracker.get_recent_files(limit=5)
        print("Most recent processed files:")
        for file_info in recent_files:
            print(f"  - {file_info['remote_path']} at {file_info['processed_at']}")

    # Connect to FTP and scan for files
    print("\nConnecting to FTP server and scanning for files...")
    ftp = connect_to_ftp()
    if not ftp:
        print("Failed to connect to FTP server")
        return

    try:
        # Collect new CSV files (filters out already processed)
        csv_files = collect_csv_file_info(ftp, tracker, date_range, "/v3")
        ftp.quit()

        if not csv_files:
            print("\nNo new files to process!")
            return

        if test_mode:
            file_number = int(sys.argv[2])
            print(f"File being pulled: {file_number}")
            csv_files = csv_files[:file_number]
            print(csv_files)
            print(f"TEST MODE: Processing only the first file: {csv_files[0]['filename']}")

        # Process files concurrently
        all_stats = process_with_progress(csv_files, tracker, max_workers=6)

        # Upload to database
        upload_all_stats(all_stats)

        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print(f"Total processed files: {tracker.get_processed_count()}")
        print("=" * 60)

    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        try:
            ftp.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
