import os
import pandas as pd
import torch
import joblib
from supabase import create_client, Client
from pathlib import Path
from datetime import datetime
import numpy as np

# ----------------------------
# Supabase configuration
# ----------------------------
SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_PROJECT_URL and SUPABASE_API_KEY must be set in .env file")

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
# Pull batted balls from Supabase
# ----------------------------
print("Fetching batted balls from Supabase...")
batted_balls_data = supabase.table("BattedBalls").select("*").execute().data
df_bb = pd.DataFrame(batted_balls_data)

if df_bb.empty:
    print("No batted balls found.")
    exit()

# ----------------------------
# Drop rows with missing features
# ----------------------------
df_bb = df_bb.dropna(subset=features + ['batter_id'])
X_bb = df_bb[features].astype(float).values
X_scaled = scaler.transform(X_bb)

# ----------------------------
# Predict xBA per batted ball
# ----------------------------
with torch.no_grad():
    df_bb['xBA_prob'] = model(torch.tensor(X_scaled, dtype=torch.float32)).numpy().flatten()

# ----------------------------
# Aggregate xBA by batter
# ----------------------------
batter_stats = df_bb.groupby('batter_id').agg(
    total_batted_balls=pd.NamedAgg(column='xBA_prob', aggfunc='count'),
    expected_hits=pd.NamedAgg(column='xBA_prob', aggfunc='sum')
).reset_index()

batter_stats['expected_batting_average'] = (
    batter_stats['expected_hits'] / batter_stats['total_batted_balls']
).round(3)

# ----------------------------
# Prepare data for upsert
# ----------------------------
batter_records = []
for _, row in batter_stats.iterrows():
    batter_records.append({
        "batter_id": row['batter_id'],
        "total_batted_balls": int(row['total_batted_balls']),
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
        result = (
            supabase.table("AdvancedBatterStats")
            .upsert(batch, on_conflict="batter_id")
            .execute()
        )
        total_upserted += len(batch)
        print(f"Upserted batch {i//batch_size + 1}: {len(batch)} records")
    print(f"Successfully upserted {total_upserted} batter records")
except Exception as e:
    print(f"Error upserting AdvancedBatterStats: {e}")
