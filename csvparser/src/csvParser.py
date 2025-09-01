'''
Python script parses the passed csv file into the sql database

run:
    this file is not ran on its own, called from ftpPuller.py

Auth: Micah Key
'''

# imports
from datetime import datetime
import json
import logging
import os
import pandas as pd
import psycopg2
import time
import yaml

# Method that is initally called, sets up yaml file and logger
def init():
    print('Starting init()...')
    global yaml_
    global logger_

    # Yaml
    try:
        with open("../include/config.yaml", 'r') as file:
            yaml_ = yaml.safe_load(file)
            print('Yaml setup success...')
    except Exception as e:
        print(f"An error occurred while loading YAML file: {e}")
        return
    
    # Setup Logger
    try:
        today_date = datetime.now().strftime("%Y-%m-%d")
        log_file = f"csv_log_{today_date}.txt"

        logger_ = logging.getLogger('csv_logger')
        logger_.setLevel(logging.INFO)
        
        # Create a file handler
        file_handler = logging.FileHandler(log_file)
        
        # Create a logging format
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        # Add the file handler to the logger
        logger_.addHandler(file_handler)
        
        print('Logger setup success...')
    except Exception as e:
        print(f"An error occurred while setting up the logger: {e}")
        return None
# end of init()

# Method for connecting to the sql database
def connect_to_db():
    print('Connecting to db...')
    try:
        conn = psycopg2.connect(
                                host=f"{yaml_.get('SQL_SERVER_NAME')}", 
                                port=f"{yaml_.get('SQL_PORT')}", 
                                database=f"{yaml_.get('SQL_DB_NAME')}", 
                                user=f"{yaml_.get('SQL_USERNAME')}", 
                                password=f"{yaml_.get('SQL_PASSWORD')}"
                               )

        curs = conn.cursor()

        print('SQL VER: ')
        curs.execute('SELECT version()')
        db_ver = curs.fetchone()
        print(db_ver)
        
        print("Connected to database successfully...\n")
        return conn
    
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None
# end of connect_to_db()

# Method for setting up the staging table 
def staging(conn, stage_name):
    print('Creating staging table...')
    try:
        # Create cursor
        curs = conn.cursor()

        # Check if the table exists
        curs.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{stage_name}')")
        exists = curs.fetchone()[0]

        if exists:
            # Table already exists, handle accordingly (drop or rename)
            curs.execute(f"DROP TABLE {stage_name}")
            print(f"Existing staging table '{stage_name}' dropped")

        # Get headers from csv file
        with open(yaml_.get('JSON_MAP'), 'r') as f:
            schema = json.load(f)
            columns = schema.get("columns", [])  # Get the list of columns
            # Construct SQL for each column without modification
            columns_sql = [f"{column['name']} {column['type']}" for column in columns]

        # Create the staging table with column names exactly as in the JSON file
        curs.execute(f"CREATE TABLE {stage_name} ({', '.join(columns_sql)});")
        curs.execute(f"ALTER TABLE {stage_name} ADD PRIMARY KEY (PitchUID);")

        conn.commit()
        print(f"Staging table '{stage_name}' created successfully\n")

    except Exception as e:
        print(f"Error creating staging table: {e}")
        return
# end of staging()

# Method that parses the .csv file
def parse(csvFile, conn, stage_name):
    print('Parsing...')
    try:
        # Read CSV, handle empty cells
        df = pd.read_csv(csvFile, na_values=[''])

        # Convert NaN values to None
        df = df.where(pd.notnull(df), None)

        print(f'Read {len(df)} records from {csvFile}')

        curs = conn.cursor()

        # Get column names from the CSV file
        columns = ", ".join(df.columns)

        # Construct the parameterized INSERT INTO statement
        insert_statement = f"INSERT INTO {stage_name} ({columns}) VALUES ({', '.join(['%s']*len(df.columns))})"

        # Prepare data for insertion
        data = [tuple(row) for row in df.itertuples(index=False, name=None)]

        # Execute the INSERT statement with the data
        curs.executemany(insert_statement, data)

        print(f"Data inserted into staging table '{stage_name}' successfully\n")

        ### Print data in stage table *Debugging ###
        # print("\n##### Table Info ######\n")
        
        # curs.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.columns WHERE table_name = '{stage_name}'")
        # columns_info = curs.fetchall()

        # print("### stage_name Names and Types ###")
        # for column_info in columns_info:
        #     column_name, column_type = column_info
        #     print(f"{column_name}: {column_type}")
        # print("")

        # curs.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.columns WHERE table_name = 'trackman_pitcher'")
        # columns_info = curs.fetchall()

        # print("### Pitcher Names and Types ###")
        # for column_info in columns_info:
        #     column_name, column_type = column_info
        #     print(f"{column_name}: {column_type}")
        # print("")

        # curs.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.columns WHERE table_name = 'trackman_batter'")
        # columns_info = curs.fetchall()

        # print("### Batter Names and Types ###")
        # for column_info in columns_info:
        #     column_name, column_type = column_info
        #     print(f"{column_name}: {column_type}")
        # print("")

        # curs.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.columns WHERE table_name = 'trackman_catcher'")
        # columns_info = curs.fetchall()

        # print("### Catcher Names and Types ###")
        # for column_info in columns_info:
        #     column_name, column_type = column_info
        #     print(f"{column_name}: {column_type}")
        # print("")

        # print("\n##### Data ######\n")
        # print('Staging table:')
        # curs.execute(f"SELECT * FROM {stage_name}")
        # print(curs.fetchall())

        # print('Pitcher table:')
        # curs.execute(f"SELECT * FROM trackman_pitcher")
        # print(curs.fetchall())

        # print('Staging table:')
        # curs.execute(f"SELECT * FROM trackman_batter")
        # print(curs.fetchall())

        # print('Staging table:')
        # curs.execute(f"SELECT * FROM trackman_catcher")
        # print(curs.fetchall())

        # print("\n#### end of table info #####\n")

    except FileNotFoundError:
        print(f"Error: File '{csvFile}' not found.")
        return
    except Exception as e:
        print(f"An error occurred while parsing CSV file: {e}")
        return
# end of parse()

# Method that fixes the headers of the .csv files to match the sql server 
def fix_headers(csvFile, changes):
    print('Fixing headers...\n')
    # Check if input file exists
    if not os.path.exists(csvFile):
        print(f"Error: Input file '{csvFile}' not found.")
        return

    # Read the CSV file into a DataFrame
    df = pd.read_csv(csvFile)

    # Apply changes to the header
    for old_header, new_header in changes.items():
        if old_header in df.columns:
            df.rename(columns={old_header: new_header}, inplace=True)

    # Fix naming schemes
    try:
        if 'Pitcher' in df.columns:
            df['Pitcher'] = df['Pitcher'].apply(lambda x: ''.join(word.capitalize() for word in x.split(', ')))

    except Exception as e:
        print(f"An error occurred while fixing 'Pitcher' column: {e}")

    try:
        if 'Batter' in df.columns:
            df['Batter'] = df['Batter'].apply(lambda x: ''.join(word.capitalize() for word in x.split(', ')))
    except Exception as e:
        print(f"An error occurred while fixing 'Batter' column: {e}")

    try:
        if 'Catcher' in df.columns:
            df['Catcher'] = df['Catcher'].apply(lambda x: ''.join(word.capitalize() for word in x.split(', ')))
    except Exception as e:
        print(f"An error occurred while fixing 'Catcher' column: {e}")

    # Write the modified DataFrame back to the input file
    df.to_csv(csvFile, index=False)
# end of fix_headers()

# Method that calls sql to move the data from the staging table -> sql tables
def distribute_data(conn, stage_name):
    print('Uploading...')
    global uploadErr_
    uploadErr_ = True
    
    try:
        curs = conn.cursor()

        print('Teams...')
        insert_team = f"""
        INSERT INTO public.teams
                    ("TeamName", "DisplayName", "Conference")
        SELECT "pitcherteam", 'NotSet', 'NotSet'
        FROM {stage_name}
        ON CONFLICT DO NOTHING;
        """
        curs.execute(insert_team)
        time.sleep(0.1)
        
        print('PlayerData...')
        print('\tPitcher')
        insert_pitcher = f"""
            INSERT INTO public.players
                        ("PlayerName", "TeamName")
            SELECT COALESCE("pitcher", 'PitchDummy'), "pitcherteam"
            FROM {stage_name}
            ON CONFLICT DO NOTHING;
        """
        curs.execute(insert_pitcher)
        time.sleep(0.1)

        print('\tBatter')
        insert_batter = f"""
            INSERT INTO public.players
                        ("PlayerName", "TeamName")
            SELECT COALESCE("batter", 'BatterDummy'), "batterteam"
            FROM {stage_name}
            ON CONFLICT DO NOTHING;
        """
        curs.execute(insert_batter)
        time.sleep(0.1)

        print('\tCatcher')
        insert_catcher = f"""
            INSERT INTO public.players
                        ("PlayerName", "TeamName")
            SELECT COALESCE("catcher", 'CatchDummy'), "catcherteam"
            FROM {stage_name}
            ON CONFLICT DO NOTHING;
        """
        curs.execute(insert_catcher)
        time.sleep(0.1)
        
        print('MetaData...')
        insert_metadata = f"""
        INSERT INTO public.trackman_metadata
                    ("PitchUID", "GameDate", "PitchTime", "Inning", "TopBottom", "Outs", "Balls", "Strikes", "PitchCall", "KorBB", "TaggedHitType", "PlayResult", "OutsOnPlay", "RunsScored", "RunnersAt", "HomeTeam", "AwayTeam", "Stadium", "Level", "League", "GameID", "GameUID", "UTCDate", "UTCtime", "LocalDateTime", "UTCDateTime", "AutoHitType", "System", "HomeTeamForeignID", "AwayTeamForeignID", "GameForeignID", "PlayID")
        SELECT "pitchuid", "gamedate", "pitchtime", "inning", "topbottom", "outs", "balls", "strikes", "pitchcall", "korbb", "taggedhittype", "playresult", "outsonplay", "runsscored", "runnersat", "hometeam", "awayteam", "stadium", "level", "league", "gameid", "gameuid", "utcdate", "utctime", "localdatetime", "utcdatetime", "autohittype", "system", "hometeamforeignid", "awayteamforeignid", "gameforeignid", "playid"
        FROM {stage_name}
        ON CONFLICT DO NOTHING;
        """
        curs.execute(insert_metadata)
        time.sleep(0.1)

        print('Pitcher...')
        # pitcher table
        insert_pitcher = f"""
        INSERT INTO public.trackman_pitcher
                    ("PitchUID", "PitchNo", "PAofInning", "PitchofPA", "Pitcher", "PitcherID", "PitcherThrows", "PitcherTeam", "PitcherSet", "TaggedPitchType", "AutoPitchType", "RelSpeed", "VertRelAngle", "HorzRelAngle", "SpinRate", "SpinAxis", "Tilt", "RelHeight", "RelSide", "Extension", "VertBreak", "InducedVert", "HorzBreak", "PlateLocHeight", "PlateLocSide", "ZoneSpeed", "VertApprAngle", "HorzApprAngle", "ZoneTime", pfxx, pfxz, x0, y0, z0, vx0, vy0, vz0, ax0, ay0, az0, "SpeedDrop", "PitchLastMeasuredX", "PitchLastMeasuredY", "PitchLastMeasuredZ", "PitchTrajectoryXc0", "PitchTrajectoryXc1", "PitchTrajectoryXc2", "PitchTrajectoryYc0", "PitchTrajectoryYc1", "PitchTrajectoryYc2", "PitchTrajectoryZc0", "PitchTrajectoryZc1", "PitchTrajectoryZc2", "PitchReleaseConfidence", "PitchLocationConfidence", "PitchMovementConfidence")
        SELECT "pitchuid", "pitchno", "paofinning", "pitchofpa", COALESCE("pitcher", 'PitchDummy'), "pitcherid", "pitcherthrows", "pitcherteam", "pitcherset", "taggedpitchtype", "autopitchtype", "relspeed", "vertrelangle", "horzrelangle", "spinrate", "spinaxis", "tilt", "relheight", "relside", "extension", "vertbreak", "inducedvert", "horzbreak", "platelocheight", "platelocside", "zonespeed", "vertapprangle", "horzapprangle", "zonetime", pfxx, pfxz, x0, y0, z0, vx0, vy0, vz0, ax0, ay0, az0, "speeddrop", "pitchlastmeasuredx", "pitchlastmeasuredy", "pitchlastmeasuredz", "pitchtrajectoryxc0", "pitchtrajectoryxc1", "pitchtrajectoryxc2", "pitchtrajectoryyc0", "pitchtrajectoryyc1", "pitchtrajectoryyc2", "pitchtrajectoryzc0", "pitchtrajectoryzc1", "pitchtrajectoryzc2", "pitchreleaseconfidence", "pitchlocationconfidence", "pitchmovementconfidence"
        FROM {stage_name}
        ON CONFLICT DO NOTHING;
        """
        curs.execute(insert_pitcher)
        time.sleep(0.1)

        print('Catcher...')
        # catcher table
        insert_catcher = f"""
        INSERT INTO public.trackman_catcher
                    ("PitchUID", "Catcher", "CatcherID", "CatcherThrows", "CatcherTeam", "ThrowSpeed", "PopTime", "ExchangeTime", "TimeToBase", "CatchPositionX", "CatchPositionY", "CatchPositionZ", "ThrowPositionX", "ThrowPositionY", "ThrowPositionZ", "BasePositionX", "BasePositionY", "BasePositionZ", "ThrowTrajectoryXc0", "ThrowTrajectoryXc1", "ThrowTrajectoryXc2", "ThrowTrajectoryYc0", "ThrowTrajectoryYc1", "ThrowTrajectoryYc2", "ThrowTrajectoryZc0", "ThrowTrajectoryZc1", "ThrowTrajectoryZc2", "CatcherThrowCatchConfidence", "CatcherThrowReleaseConfidence", "CatcherThrowLocationConfidence")
        SELECT "pitchuid", COALESCE("catcher", 'CatchDummy'), "catcherid", "catcherthrows", "catcherteam", "throwspeed", "poptime", "exchangetime", "timetobase", "catchpositionx", "catchpositiony", "catchpositionz", "throwpositionx", "throwpositiony", "throwpositionz", "basepositionx", "basepositiony", "basepositionz", "throwtrajectoryxc0", "throwtrajectoryxc1", "throwtrajectoryxc2", "throwtrajectoryyc0", "throwtrajectoryyc1", "throwtrajectoryyc2", "throwtrajectoryzc0", "throwtrajectoryzc1", "throwtrajectoryzc2", "catcherthrowcatchconfidence", "catcherthrowreleaseconfidence", "catcherthrowlocationconfidence"
        FROM {stage_name}
        ON CONFLICT DO NOTHING;
        """
        curs.execute(insert_catcher)
        time.sleep(0.1)

        print('Batter...')
        # batter table
        insert_batter = f"""
        INSERT INTO public.trackman_batter
                    ("PitchUID", "Batter", "BatterID", "BatterSide", "BatterTeam", "ExitSpeed", "Angle", "Direction", "HitSpinRate", "PositionAt110X", "PositionAt110Y", "PositionAt110Z", "Distance", "LastTracked", "Bearing", "HangTime", "EffectiveVelo", "MaxHeight", "MeasuredDuration", "ContactPositionX", "ContactPositionY", "ContactPositionZ", "HitSpinAxis", "HitTrajectoryXc0", "HitTrajectoryXc1", "HitTrajectoryXc2", "HitTrajectoryXc3", "HitTrajectoryXc4", "HitTrajectoryXc5", "HitTrajectoryXc6", "HitTrajectoryXc7", "HitTrajectoryXc8", "HitTrajectoryYc0", "HitTrajectoryYc1", "HitTrajectoryYc2", "HitTrajectoryYc3", "HitTrajectoryYc4", "HitTrajectoryYc5", "HitTrajectoryYc6", "HitTrajectoryYc7", "HitTrajectoryYc8", "HitTrajectoryZc0", "HitTrajectoryZc1", "HitTrajectoryZc2", "HitTrajectoryZc3", "HitTrajectoryZc4", "HitTrajectoryZc5", "HitTrajectoryZc6", "HitTrajectoryZc7", "HitTrajectoryZc8", "HitLaunchConfidence", "HitLandingConfidence")
        SELECT "pitchuid", COALESCE("batter", 'BatterDummy'), "batterid", "batterside", "batterteam", "exitspeed", "angle", "direction", "hitspinrate", "positionat110x", "positionat110y", "positionat110z", "distance", "lasttracked", "bearing", "hangtime", "effectivevelo", "maxheight", "measuredduration", "contactpositionx", "contactpositiony", "contactpositionz", "hitspinaxis", "hittrajectoryxc0", "hittrajectoryxc1", "hittrajectoryxc2", "hittrajectoryxc3", "hittrajectoryxc4", "hittrajectoryxc5", "hittrajectoryxc6", "hittrajectoryxc7", "hittrajectoryxc8", "hittrajectoryyc0", "hittrajectoryyc1", "hittrajectoryyc2", "hittrajectoryyc3", "hittrajectoryyc4", "hittrajectoryyc5", "hittrajectoryyc6", "hittrajectoryyc7", "hittrajectoryyc8", "hittrajectoryzc0", "hittrajectoryzc1", "hittrajectoryzc2", "hittrajectoryzc3", "hittrajectoryzc4", "hittrajectoryzc5", "hittrajectoryzc6", "hittrajectoryzc7", "hittrajectoryzc8", "hitlaunchconfidence", "hitlandingconfidence"
        FROM {stage_name}
        ON CONFLICT DO NOTHING;
        """
        curs.execute(insert_batter)
        time.sleep(0.1)

        # commit changes
        conn.commit()
        print("Data distributed successfully\n")
        
        # this will change only if the logger succedes
        uploadErr_ = False

    except Exception as e:
        print(f"Error distributing data: {e}")
# end of distribute_data()

# 'Main' function, called from ftpPuller.py
def runParser(csvFile):
    # parse yaml variables
    init()

    # fix file headers
    changes = { 'Date': 'GameDate',
                'Time': 'PitchTime',
                'Top/Bottom': 'TopBottom',
                'Notes': 'RunnersAt',
                'InducedVertBreak': 'InducedVert',
                'LastTrackedDistance': 'LastTracked'}
    
    fix_headers(csvFile, changes)

    time.sleep(0.5)

    # connect to db
    conn = connect_to_db()
    if conn is None:
        return
    
    #define staging name
    stage_name = 'staging_table'

    staging(conn, stage_name)

    parse(csvFile, conn, stage_name)

    distribute_data(conn, stage_name)

    # close connection
    conn.close()

    # If uploadErr_ did not get changed
    if uploadErr_ == True:
        logger_.info(f"Error with {csvFile}\n")