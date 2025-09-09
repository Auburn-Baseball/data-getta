import os
import pandas as pd
import torch
import joblib
from supabase import create_client, Client
from pathlib import Path
from datetime import datetime
import numpy as np
from dotenv import load_dotenv

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

# ----------------------------
# Paths to model and scaler
# ----------------------------
MODEL_PATH = Path(__file__).parent.parent / "training_models" / "models" / "xba_model_20250909_040802.pt"
SCALER_PATH = Path(__file__).parent.parent / "training_models" / "models" / "scaler.save"

if not MODEL_PATH.exists() or not SCALER_PATH.exists():
    raise FileNotFoundError("Model or scaler not found. Run training script first.")

# ----------------------------
# Load scaler
# ----------------------------
scaler = joblib.load(SCALER_PATH)

# ----------------------------
# Define PyTorch model (same as training)
# ----------------------------
class HitPredictor(torch.nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.model = torch.nn.Sequential(
            torch.nn.Linear(input_dim, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 1),
            torch.nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

# ----------------------------
# Load trained model
# ----------------------------
features = ['exit_speed', 'launch_angle', 'direction', 'hit_spin_rate', 'distance', 'bearing', 'hang_time']
model = HitPredictor(len(features))
model.load_state_dict(torch.load(MODEL_PATH))
model.eval()

# ----------------------------
# Fetch BattedBalls
# ----------------------------
print("Fetching BattedBalls from Supabase...")
bb_data = supabase.table("BattedBalls").select("*").execute().data
df_bb = pd.DataFrame(bb_data)

if df_bb.empty:
    print("No batted balls found.")
    exit()

# ----------------------------
# Predict xBA probabilities (only where features exist)
# ----------------------------
df_predictable = df_bb.dropna(subset=features)
X_bb = df_predictable[features].astype(float).values
X_scaled = scaler.transform(X_bb)

with torch.no_grad():
    df_predictable['xBA_prob'] = model(torch.tensor(X_scaled, dtype=torch.float32)).numpy().flatten()

# Merge predictions back, default missing to 0
df_bb = df_bb.merge(
    df_predictable[['id', 'xBA_prob']],
    on="id", how="left"
)
df_bb['xBA_prob'] = df_bb['xBA_prob'].fillna(0.0)

# ----------------------------
# Sum expected hits per batter
# ----------------------------
# ----------------------------
# Sum expected hits per batter_id
# ----------------------------
batter_xba = df_bb.groupby('batter_id').agg(
    expected_hits=('xBA_prob', 'sum')
).reset_index()

# ----------------------------
# Pull Players table (for join key)
# ----------------------------
players_data = supabase.table("Players").select(
    "BatterId, Name, TeamTrackmanAbbreviation, Year"
).execute().data
df_players = pd.DataFrame(players_data)

# ----------------------------
# Pull BatterStats (with official at_bats)
# ----------------------------
batter_stats_data = supabase.table("BatterStats").select(
    "Batter, BatterTeam, Year, at_bats"
).execute().data
df_batterstats = pd.DataFrame(batter_stats_data)

# ----------------------------
# Join expected hits -> Players -> BatterStats using correct keys
# ----------------------------
df_join = (
    batter_xba
    .merge(df_players, left_on='batter_id', right_on='BatterId', how='left')
    .merge(df_batterstats, 
           left_on=['Name', 'TeamTrackmanAbbreviation', 'Year'], 
           right_on=['Batter', 'BatterTeam', 'Year'], 
           how='left')
)

df_join['at_bats'] = df_join['at_bats'].fillna(0).astype(int)

# ----------------------------
# Compute expected batting average (xBA)
# ----------------------------
df_join['expected_batting_average'] = (
    (df_join['expected_hits'] / df_join['at_bats'])
    .replace([np.inf, -np.inf], 0)
    .fillna(0)
    .round(3)
)

# ----------------------------
# Prepare data for upsert
# ----------------------------
batter_records = []
for _, row in df_join.iterrows():
    batter_records.append({
        "batter_id": row['batter_id'],
        "expected_hits": float(row['expected_hits']),
        "expected_batting_average": float(row['expected_batting_average']),
        "updated_at": datetime.utcnow().isoformat()
    })

# ----------------------------
# Upsert into AdvancedBatterStats
# ----------------------------
print(f"Upserting {len(batter_records)} records into AdvancedBatterStats...")

try:
    batch_size = 100
    total_upserted = 0
    for i in range(0, len(batter_records), batch_size):
        batch = batter_records[i:i + batch_size]
        supabase.table("AdvancedBatterStats").upsert(batch, on_conflict="batter_id").execute()
        total_upserted += len(batch)
        print(f"Upserted batch {i//batch_size + 1}: {len(batch)} records")
    print(f"Successfully upserted {total_upserted} batter records")
except Exception as e:
    print(f"Error upserting AdvancedBatterStats: {e}")
