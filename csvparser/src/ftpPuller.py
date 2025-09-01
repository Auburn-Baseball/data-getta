'''
Python script that pulls files from a set directory in the .yaml file and sends the file to csvParser.py

run:
    python3 ftpPuller.py <mode> 

<mode>: 
        single <filePath>, all, check_pull, local
        * see '# Main' for more info

Auth: Micah Key
'''

# Imports
import csvParser
from ftplib import FTP_TLS
import itertools
import os
import sys
import time
import yaml

# Method that is initally called, sets up ftp server, yaml file, and calculations
def init():
    # global variables
    global yaml_
    global ftp_
    global totalFiles_
    global currFileNum_
    totalFiles_ = 0
    currFileNum_ = 1

    # Setup Yaml
    print('Initial Ftp...')
    try:
        with open('../include/config.yaml', 'r') as file:
            yaml_ = yaml.safe_load(file)
            print('YamlSetup...')

    except FileNotFoundError:
        print("Error: The specified file was not found.")
        return
    except yaml.YAMLError as e:
        print("Error loading YAML data:", e)
        return
    except Exception as e:
        print("An unexpected error occurred:", e)
        return
    
    # Setup FTP client
    try:
        ftp_ = FTP_TLS(yaml_.get('TRACKMAN_URL'))
        ftp_.login(yaml_.get('TRACKMAN_USERNAME'), yaml_.get('TRACKMAN_PASSWORD'))
        ftp_.prot_p()

    except Exception as e:
        print("An error occurred while establishing FTP connection:", e)
        return
# end of init()

# Method that get the number of files to be downloaded
def count_csv_files(directory):
    global totalFiles_

    # Change directory to the specified directory
    ftp_.cwd(directory)
    items = ftp_.nlst()

    spinner = itertools.cycle(['-', '/', '|', '\\'])

    for item in items:
        # Check if it's a directory
        if '.' not in item:
            # Recursively call count_csv_files on subdirectories
            count_csv_files(directory + '/' + item)
        else:
            # If it's a CSV file and '_playerpositioning' is not in the name, increment totalFiles_
            if item.endswith('.csv') and '_playerpositioning' not in item:
                totalFiles_ += 1
                print(f'\rCalculating files... {next(spinner)}', end='', flush=True)
# end of count_csv_files()

# Method that downloads and parses the inputted file
def download_and_parse(ftpFilePath, csvFileName):
    global currFileNum_
    
    # Check if file is in db, if so skip
    # Read the already parsed files into a set
    parsed_files = set()
    try:
        with open(yaml_.get('FILES_TXT'), "r") as txt_file:
            for line in txt_file:
                parsed_files.add(line.strip())

    except FileNotFoundError:
        print(".txt not found. Continuing without skipping.")

    # Check
    if csvFileName in parsed_files:
        print(f'{csvFileName} in db skipping...\n')
        currFileNum_ += 1
        return

    print(f"Downloading... {csvFileName}\n")
    # Go to desired directory
    ftp_.cwd(ftpFilePath)

    local_file_path = os.path.join(yaml_.get('CSV_DIR'), csvFileName)
    
    # Check if the file already exists locally
    if os.path.exists(local_file_path):
        try:
            os.remove(local_file_path)
            print("File found local, removing... File deleted:", local_file_path)
        except OSError as e:
            print(f"Error deleting file {local_file_path}: {e}")

    if not os.path.exists(local_file_path):
        # Ensure that the directory for the file exists
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        with open(local_file_path, 'wb') as file:
            # download
            ftp_.retrbinary('RETR ' + csvFileName, file.write)

        time.sleep(0.1)

        ### Parse ###
        csvParser.runParser(local_file_path)
        time.sleep(0.1)

        ### Append to txt document ###
        try:
            with open(yaml_.get('FILES_TXT'), "a") as txt_file:
                txt_file.write(csvFileName + '\n')
        except Exception as e:
            print(f"Error appending to parsed_files.txt: {e}")
        time.sleep(0.1)

        ## Delete ###
        try:
            os.remove(local_file_path)
            print("File deleted:", local_file_path)
        except OSError as e:
            print(f"Error deleting file {local_file_path}: {e}")

        # Iterate currFileNum_
        currFileNum_ += 1

        # For terminal readability        
        for ii in range(50):
            print('#', end='')
        print('\n')

        # Help pwith errors
        time.sleep(0.05)
# end of download_and_parse()

# Method for the 'pull_all' mode, pulls all .csv files in a directory
def pull_all(directory, local_dir):
    # Change directory to the specified directory
    ftp_.cwd(directory)
    items = ftp_.nlst()
    
    for item in items:
        # Check if it's a directory
        if '.' not in item:
            # Recursively call pull_all on subdirectories
            pull_all(directory + '/' + item, os.path.join(local_dir, item))
        else:
            # If it's a CSV file and '_playerpositioning' is not in the name, download it
            if item.endswith('.csv') and '_playerpositioning' not in item:
                download_and_parse(directory, item)
                print(f'{directory}{item} \t {currFileNum_}/{totalFiles_}...')
# end of pull_all()
        
# Method for 'single' mode, pulls a single file from the inputted filepath
def pull_single(csvFileName):
    try:
        dir = f'/./v3/{csvFileName[:4]}/{csvFileName[4:6]}/{csvFileName[6:8]}/CSV/'
        ftp_.cwd(dir)
        items = ftp_.nlst()
        print(dir)
        csvFile = os.path.join(dir, csvFileName)
        print(csvFile)
        # print(items)

        # Check if the file already exists locally
        for item in items:
            if item == csvFileName:
                local_file_path = os.path.join(yaml_.get('CSV_DIR'), csvFileName)
                if os.path.exists(local_file_path):
                    try:
                        os.remove(local_file_path)
                        print("File found locally, removing... File deleted:", local_file_path)
                    except OSError as e:
                        print(f"Error deleting file {local_file_path}: {e}")

                if not os.path.exists(local_file_path):
                    # Ensure that the directory for the file exists
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                    with open(local_file_path, 'wb') as file:
                        # download
                        csvFile = os.path.join(dir, csvFileName)
                        print(csvFile)
                        ftp_.retrbinary('RETR ' + csvFileName, file.write)
                        print(f'Downloaded {csvFileName}')
                        return

    except Exception as e:
        print(f"An error occurred: {e}")

    print('file not found')
# end of pull_single()

# Method for 'check_pull' mode, checks the files in the directory to the db_files.txt to only pull new files
def check_pull(directory, local_dir):
    # Change directory to the specified directory
    ftp_.cwd(directory)
    items = ftp_.nlst()

    for item in items:
        # Check if it's a directory
        if '.' not in item:
            # Recursively call check_pull on subdirectories
            pull_all(directory + '/' + item, os.path.join(local_dir, item))
        else:
            # If it's a CSV file and '_playerpositioning' is not in the name, start download
            if item.endswith('.csv') and '_playerpositioning' not in item:
                download_and_parse(directory, item)
                print(f'{directory}{item} \t\t {currFileNum_}/{totalFiles_}...')
# end of check_pull()                

# Method for 'local' mode, parses file inputted on local machine
def pull_localFile(csvFileName):
    csvParser.runParser(csvFileName)

# Main
if __name__ == "__main__":
    mode = sys.argv[1]

    # Only start the function if a correct option
    if mode in ['single', 'all', 'check_pull', 'local']:
        init()

    ### Modes ###
    # single mode, tries to find and parse the inputted file
    # usage: ... single filePath/fileName.csv
    if mode == 'single':
        pull_single(sys.argv[2])
    
    # all mode, pulls all csv files in the .yaml directory
    # usage: ... all
    elif mode == 'all':
        print('Calculating files...', end='')
        count_csv_files(yaml_.get('TRACKMAN_DIR'))
        pull_all(yaml_.get('TRACKMAN_DIR'), yaml_.get('CSV_DIR'))

    # check_pull mode, checks the file in ftp server to the db_files.txt before downloading and parsing 
    # usage: ... check_pull
    elif mode == 'check_pull':
        print('Calculating files...', end='')
        count_csv_files(yaml_.get('TRACKMAN_DIR'))
        check_pull(yaml_.get('TRACKMAN_DIR'), yaml_.get('CSV_DIR'))

    # local mode, used for debugging
    # usage: ... local filePath/fileName
    elif mode == 'local':
        pull_localFile(sys.argv[2])

    # error message
    else:
        print('options are \'single <filePath>\' \'all\' \'check_pull\' try again...')
        quit()

    # makes sure that the ftp server connection is closed 
    if ftp_ is not None:
        ftp_.quit()
# end of main()