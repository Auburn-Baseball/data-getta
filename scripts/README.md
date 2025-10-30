## Overview

The scripts directory contains an orchestrator python script (process_all_data.py) that pulls files from a remote ftp Trackman server and uses helper upload files to process the data received from csv files on the ftp server and upload them to a Supabase database.

## Setup

- Use the make command or poetry to install all of the project's python dependencies:
```bash
make install
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

Once the dependencies are installed and the .env file(s) are prepared, the main script is ready to run! The Makefile is your friend, but manually running the command is also an option.

```bash
make process  # Run using the Makefile shortcut

poetry run python3 process_all_data.py  # Run manually
```

There are two flags supported when running the script: test and date-range

```bash
make process-args ARGS="--test"
make process-args ARGS="--date-range {range}"

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

## Linting, auto-formatting, and testing

A series of tools has been included in the pyproject.toml file and combined with the Makefile in order to provide automated formatting (isort), linting (flake8), static type checking (mypy), pytest configuration (ini_options). This is both quality of life and also just makes the scripts more maintainable overall.

For the purposes of deployment, poetry install should be run with the --without dev flag to refrain from installing unnecessary dev tools.

## Note to future devs

A workflow of auto-formatting, linting, and performing tests can be set to run on commit. Running 'poetry run pre-commit install' will setup a pre-commit hook in your local github repository according to the pyproject.toml file. Afterward, when committing, the pipeline is run, and any failures prevent a successful commit. You can skip the pre-commit with the --no-verify flag when committing if necessary.
