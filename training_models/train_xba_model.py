import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
import joblib
from supabase import create_client, Client
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

# ----------------------------
# Supabase configuration
# ----------------------------
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

# Supabase configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_PROJECT_URL and SUPABASE_API_KEY must be set in .env file"
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------
# Load batted ball data
# ----------------------------
data = supabase.table("BattedBalls").select("*").execute().data
df = pd.DataFrame(data)

if df.empty:
    print("No batted ball data found in Supabase.")
    exit()

# ----------------------------
# Define target variable
# ----------------------------
df['is_hit'] = df['play_result'].isin(
    ['Single', 'Double', 'Triple', 'HomeRun']
).astype(int)

# ----------------------------
# Select features
# ----------------------------
features = [
    'exit_speed',
    'launch_angle',
    'direction',
    'hit_spin_rate',
    'distance',
    'bearing',
    'hang_time'
]

# Drop rows with missing features or target
df = df.dropna(subset=features + ['is_hit'])

X = df[features].astype(float).values
y = df['is_hit'].values

# ----------------------------
# Standardize features
# ----------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Save scaler for later use
joblib.dump(scaler, project_root / "training_models/models/scaler.save")

# ----------------------------
# Convert to PyTorch tensors
# ----------------------------
X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32).unsqueeze(1)  # shape (N,1)

dataset = TensorDataset(X_tensor, y_tensor)
dataloader = DataLoader(dataset, batch_size=64, shuffle=True)

# ----------------------------
# Define PyTorch model
# ----------------------------
class HitPredictor(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

model = HitPredictor(X_tensor.shape[1])

# ----------------------------
# Training setup
# ----------------------------
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
epochs = 20

# ----------------------------
# Train model
# ----------------------------
for epoch in range(epochs):
    epoch_loss = 0
    for batch_X, batch_y in dataloader:
        optimizer.zero_grad()
        preds = model(batch_X)
        loss = criterion(preds, batch_y)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()

    print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss/len(dataloader):.4f}")

# ----------------------------
# Save trained model
# ----------------------------
timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
model_dir = project_root / "training_models" / "models"
model_dir.mkdir(parents=True, exist_ok=True)  # Create folder if it doesn't exist

model_filename = model_dir / f"xba_model_{timestamp}.pt"
torch.save(model.state_dict(), model_filename)

print(f"Trained model saved as {model_filename}")
