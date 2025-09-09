import os
import csv
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# ------------------------------
# Load environment variables
# ------------------------------
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("VITE_SUPABASE_PROJECT_URL and VITE_SUPABASE_API_KEY must be set in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------
# Helper Functions
# ------------------------------
def should_exclude_file(filename: str) -> bool:
    exclude_patterns = ["playerpositioning", "fhc", "unverified"]
    filename_lower = filename.lower()
    return any(pattern in filename_lower for pattern in exclude_patterns)


def extract_batted_balls_from_csv(file_path: str):
    batted_balls = []

    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get("PitchCall") == "InPlay" and row.get("PlayID"):
                try:
                    batted_balls.append({
                        "play_id": row.get("PlayID"),  # store actual UUID from CSV
                        "game_year": row.get("GameDate", "")[:4],
                        "pitcher_id": row.get("PitcherId"),
                        "batter_id": row.get("BatterId"),
                        "pitch_call": row.get("PitchCall"),
                        "tagged_hit_type": row.get("TaggedHitType"),
                        "play_result": row.get("PlayResult"),
                        "exit_speed": float(row.get("ExitSpeed") or 0),
                        "launch_angle": float(row.get("Angle") or 0),
                        "direction": float(row.get("Direction") or 0),
                        "hit_spin_rate": float(row.get("HitSpinRate") or 0),
                        "distance": float(row.get("Distance") or 0),
                        "bearing": float(row.get("Bearing") or 0),
                        "hang_time": float(row.get("HangTime") or 0),
                        "created_at": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    print(f"Skipping malformed row in {file_path}: {e}")

    return batted_balls


def process_batted_balls(csv_folder_path: str):
    all_batted_balls = []

    year_folder = os.path.join(csv_folder_path, "2025")
    if not os.path.exists(year_folder):
        print(f"2025 CSV folder not found: {year_folder}")
        return all_batted_balls

    csv_files = [f for f in os.listdir(year_folder) if f.endswith(".csv")]
    filtered_files = [f for f in csv_files if not should_exclude_file(f)]

    print(f"Found {len(filtered_files)} 2025 CSV files to process")

    for filename in filtered_files:
        file_path = os.path.join(year_folder, filename)
        print(f"Processing: {filename}")

        batted_balls_from_file = extract_batted_balls_from_csv(file_path)
        all_batted_balls.extend(batted_balls_from_file)

        print(f"   + Found {len(batted_balls_from_file)} batted balls in this file")
        print(f"   + Total batted balls so far: {len(all_batted_balls)}")

    return all_batted_balls


def upload_batted_balls_to_supabase(batted_balls):
    if not batted_balls:
        print("No batted balls to upload")
        return

    try:
        print(f"Preparing to upload {len(batted_balls)} batted balls...")

        batch_size = 100
        total_inserted = 0

        for i in range(0, len(batted_balls), batch_size):
            batch = batted_balls[i : i + batch_size]

            try:
                # Use play_id for conflict to prevent duplicate rows
                supabase.table("BattedBalls").upsert(batch, on_conflict="play_id").execute()
                total_inserted += len(batch)
                print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as batch_error:
                print(f"Error uploading batch {i//batch_size + 1}: {batch_error}")
                if batch:
                    print(f"Sample failed record: {batch[0]}")

        print(f"Successfully processed {total_inserted} batted ball records")

    except Exception as e:
        print(f"Supabase upload error: {e}")


def main():
    print("=== Starting batted balls CSV processing ===")

    csv_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv")
    print(f"Looking for CSV files in: {csv_folder_path}")

    all_batted_balls = process_batted_balls(csv_folder_path)

    print(f"\nTotal batted balls found: {len(all_batted_balls)}")

    if all_batted_balls:
        print("\nUploading to Supabase...")
        upload_batted_balls_to_supabase(all_batted_balls)
    else:
        print("No batted balls found to upload")


if __name__ == "__main__":
    main()
