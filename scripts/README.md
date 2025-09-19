## Overview

The scripts directory contains an orchestrator python script (process_all_data.py) that pulls files from a remote ftp Trackman server and uses helper upload files to process the data received from csv files on the ftp server and upload them to a Supabase database.

## Setup

- Use poetry to install all of the project's python dependencies:
```bash
poetry install
```

- Ensure at least one of the following .env files are created: .env.production, .env.development

*The .env.production file should reference the production supabase project, while the .env.development should reference the dev supabase project. Both files should lie in the base directory of this repository*

- Set the environment variable ENV to either "production" or "development" to specify which .env file to reference for uploading data

**Reference .env file**
```bash
TRACKMAN_URL=string
TRACKMAN_USERNAME=string
TRACKMAN_PASSWORD=string
VITE_SUPABASE_PROJECT_URL=string
VITE_SUPABASE_API_KEY=string
```

## Script usage

Once the dependencies are installed and the .env file(s) are prepared, the main script is ready to run!

```bash
poetry run python3 process_all_data.py
```
