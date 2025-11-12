#!/usr/bin/env python3
"""
Author: Joshua Henley
Created: 19 September 2025

Local QA TrackMan CSV Processor
- Processes a single local CSV file for quality assurance testing
- Uses the same data processing functions as the main script
"""

import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# Import your existing processing functions
from utils import (
    get_batter_stats_from_buffer,
    get_pitch_counts_from_buffer,
    get_pitcher_stats_from_buffer,
    get_players_from_buffer,
    upload_batters_to_supabase,
    upload_pitchers_to_supabase,
    upload_pitches_to_supabase,
    upload_players_to_supabase,
)

# Import advanced batting stats
from utils.update_advanced_batting_table import (
    get_advanced_batting_stats_from_buffer,
    upload_advanced_batting_to_supabase,
)

# Add parent directory to path so that the utils module can be imported
sys.path.append(str(Path(__file__).parent.parent))

# Setup environment
project_root = Path(__file__).parent.parent
env = os.getenv("ENV", "development")
load_dotenv(project_root / f".env.{env}")

# Supabase Configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_PROJECT_URL and SUPABASE_API_KEY must be set in .env file"
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# csv file directory path
QA_DIR = Path(__file__).parent / "test_csv_files"


def get_file_info(file_path: Path):
    """-------------------------------------
    Get file metadata similar to FTP version.
    -------------------------------------"""
    try:
        stat = file_path.stat()
        return {
            "size": stat.st_size,
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    except Exception as e:
        print(f"Error getting file info for {file_path}: {e}")
        return {"size": None, "last_modified": None}


def process_local_csv_file(file_path: Path):
    """-------------------------------------------------------
    Process a single local CSV file through all update modules.
    -------------------------------------------------------"""
    print(f"Processing: {file_path.name}")

    if not file_path.exists():
        print(f"ERROR: File {file_path} does not exist!")
        return False

    if not file_path.name.lower().endswith(".csv"):
        print(f"ERROR: File {file_path} is not a CSV file!")
        return False

    try:
        # Read file into buffer
        with open(file_path, "rb") as f:
            file_content = f.read()

        buffer = BytesIO(file_content)
        filename = file_path.name

        # Initialize stats containers
        all_stats: dict = {
            "batters": {},
            "pitchers": {},
            "pitches": {},
            "players": {},
            "advanced_batting": {},
        }

        stats_summary = {}

        print(f"File size: {len(file_content):,} bytes")
        print("Processing through all modules...")

        # Process Batters
        buffer.seek(0)
        try:
            print("  - Processing batter stats...")
            batter_stats = get_batter_stats_from_buffer(buffer, filename)
            all_stats["batters"].update(batter_stats)
            stats_summary["batters"] = len(batter_stats)
            print(f"    Found {len(batter_stats)} batter records")
        except Exception as e:
            print(f"    ERROR processing batter stats: {e}")
            stats_summary["batters"] = 0

        # Process Pitchers
        buffer.seek(0)
        try:
            print("  - Processing pitcher stats...")
            pitcher_stats = get_pitcher_stats_from_buffer(buffer, filename)
            all_stats["pitchers"].update(pitcher_stats)
            stats_summary["pitchers"] = len(pitcher_stats)
            print(f"    Found {len(pitcher_stats)} pitcher records")
        except Exception as e:
            print(f"    ERROR processing pitcher stats: {e}")
            stats_summary["pitchers"] = 0

        # Process Pitches
        buffer.seek(0)
        try:
            print("  - Processing pitch stats...")
            pitch_stats = get_pitch_counts_from_buffer(buffer, filename)
            all_stats["pitches"].update(pitch_stats)
            stats_summary["pitches"] = len(pitch_stats)
            print(f"    Found {len(pitch_stats)} pitch records")
        except Exception as e:
            print(f"    ERROR processing pitch stats: {e}")
            stats_summary["pitches"] = 0

        # Process Players
        buffer.seek(0)
        try:
            print("  - Processing player stats...")
            player_stats = get_players_from_buffer(buffer, filename)
            all_stats["players"].update(player_stats)
            stats_summary["players"] = len(player_stats)
            print(f"    Found {len(player_stats)} player records")
        except Exception as e:
            print(f"    ERROR processing player stats: {e}")
            stats_summary["players"] = 0

        # Process Advanced Batting Stats
        buffer.seek(0)
        try:
            print("  - Processing advanced batting stats...")
            advanced_batting_stats = get_advanced_batting_stats_from_buffer(
                buffer, filename
            )
            all_stats["advanced_batting"].update(advanced_batting_stats)
            stats_summary["advanced_batting"] = len(advanced_batting_stats)
            print(f"    Found {len(advanced_batting_stats)} advanced batting records")
        except Exception as e:
            print(f"    ERROR processing advanced batting stats: {e}")
            stats_summary["advanced_batting"] = 0

        # Upload to database
        print("\nUploading to database...")
        upload_success = upload_all_stats(all_stats)

        if upload_success:
            print(f"\n✓ Successfully processed {filename}")
            print(f"Stats summary: {stats_summary}")
            return True
        else:
            print(f"\n✗ Failed to upload data for {filename}")
            return False

    except Exception as e:
        print(f"ERROR processing {file_path.name}: {e}")
        return False


def upload_all_stats(all_stats):
    """------------------------------------------------------
    Call each module's upload function with accumulated stats.
    Returns True if all uploads successful, False otherwise.
    ------------------------------------------------------"""
    success = True

    try:
        if all_stats["batters"]:
            print(f"  - Uploading {len(all_stats['batters'])} batter records...")
            upload_batters_to_supabase(all_stats["batters"])

        if all_stats["pitchers"]:
            print(f"  - Uploading {len(all_stats['pitchers'])} pitcher records...")
            upload_pitchers_to_supabase(all_stats["pitchers"])

        if all_stats["pitches"]:
            print(f"  - Uploading {len(all_stats['pitches'])} pitch records...")
            upload_pitches_to_supabase(all_stats["pitches"])

        if all_stats["players"]:
            print(f"  - Uploading {len(all_stats['players'])} player records...")
            upload_players_to_supabase(all_stats["players"])

        if all_stats["advanced_batting"]:
            print(
                f"  - Uploading {len(all_stats['advanced_batting'])} advanced batting records..."
            )
            upload_advanced_batting_to_supabase(all_stats["advanced_batting"])

    except Exception as e:
        print(f"ERROR during upload: {e}")
        success = False

    return success


def list_qa_files():
    """------------------------------------
    List all CSV files in the QA directory.
    ------------------------------------"""
    if not QA_DIR.exists():
        print(f"QA directory does not exist: {QA_DIR}")
        return []

    csv_files = list(QA_DIR.glob("*.csv"))
    return sorted(csv_files)


def main():
    print("=" * 60)
    print("LOCAL QA TRACKMAN CSV PROCESSOR")
    print("=" * 60)

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print(
            f"  {sys.argv[0]} <filename>     - Process specific file in test_csv_files/ directory"
        )
        return

    filename = sys.argv[1]

    # Ensure QA directory exists
    QA_DIR.mkdir(exist_ok=True)

    # Construct file path
    file_path = QA_DIR / filename

    print(f"QA Directory: {QA_DIR}")
    print(f"Target file: {file_path}")

    # Process the file
    success = process_local_csv_file(file_path)

    if success:
        print(f"\n{'='*60}")
        print("QA PROCESSING COMPLETE - SUCCESS")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("QA PROCESSING FAILED")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
