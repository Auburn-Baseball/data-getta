import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from collections import defaultdict

# ----------------------------
# Supabase configuration
# ----------------------------
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "VITE_SUPABASE_PROJECT_URL and VITE_SUPABASE_API_KEY must be set in .env file"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------
# Fetch BattedBalls data
# ----------------------------
response = supabase.table("BattedBalls").select("batter_id, exit_speed").execute()
data = response.data

if not data:
    print("No batted ball data found.")
    exit()

# ----------------------------
# Compute average exit velocity per batter (skip exit_speed == 0)
# ----------------------------
batter_speeds = defaultdict(list)

for row in data:
    batter_id = row.get("batter_id")
    exit_speed = row.get("exit_speed")
    # Only include valid exit speeds
    if batter_id and exit_speed and exit_speed != 0:
        batter_speeds[batter_id].append(exit_speed)

# Compute averages
average_ev = [
    {"batter_id": batter_id, "average_EV": sum(speeds) / len(speeds)}
    for batter_id, speeds in batter_speeds.items()
]

print(f"Computed average exit velocity for {len(average_ev)} batters (ignoring exit_speed=0).")

# ----------------------------
# Insert/Upsert into AdvancedBatterStats
# ----------------------------
try:
    for i in range(0, len(average_ev), 100):  # batch insert in 100s
        batch = average_ev[i:i+100]
        supabase.table("AdvancedBatterStats").upsert(batch, on_conflict="batter_id").execute()
    print("Successfully uploaded average exit velocities to AdvancedBatterStats.")
except Exception as e:
    print(f"Error uploading to Supabase: {e}")
