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

There are two flags supported when running the script: test and date-range

```bash
poetry run python3 process_all_data.py --test
poetry run python3 process_all_data.py --date-range {range}
```

The test flag will be deprecated soon, but limits the file processing to only 1-2 files in order to test the data that is being uploaded into the database.

The date-range flag is used to specify which date range of files should be processed during the run. The dates of the files are determined from the filename, which contains the exact day of the game that the csv file contains data for. This is useful to avoid processing unnecessary files and to provide the freedom of pulling only the desired game data.

## QA

The QA directory contains files that should be used for future quality assurance testing, automated or manual. This contains a python script 'process_local_csv.py' which can be used to process a single, local csv file that should be stored in the 'test_csv_files' subdirectory. This permits fully controllable input data which can be used to generate expected outputs for functional testing.

```bash
poetry run python3 process_local_csv.py {filename}
```

Note that the filename does not need to be the full path to the file, as the 'process_local_csv.py' file will check the 'test_csv_files' subdirectory by default.
