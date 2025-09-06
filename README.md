# Data Getta - Auburn Baseball

Baseball analytics platform that processes TrackMan CSV data for Auburn University teams and players.

## Project Structure

```
data-getta/
├── scripts/       # Python data processing (Poetry)
├── ui/            # React TypeScript frontend (Vite)
└── csv/           # TrackMan CSV data by year
```

## Tech Stack

- **Backend**: Python + Poetry, pandas, Supabase
- **Frontend**: React + TypeScript + Vite, Material-UI

## Quick Start

### Scripts (Python)
```bash
cd scripts
poetry install
poetry run python my_script.py
```

### UI (React)
```bash
cd ui
npm install
npm run dev
```

## Setup Requirements

- Python 3.10+
- Node.js 22.12+
- Poetry
- Environment variables for TrackMan FTP and Supabase

## Documentation

- `scripts/README.md` - Python processing details
- `ui/README.md` - React development guide

War Eagle! ⚾