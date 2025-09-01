'''
Python script to test the connection to the sql database

run:
    python script.py <directory> <column>

Auth: Micah Key
'''

# Imports
import os
import pandas as pd
import sys

# Method to retrieve the column 'columnName'
def getData(columnName, csvFile):
    # Read the CSV file into a DataFrame
    try:
        df = pd.read_csv(csvFile)
    except FileNotFoundError:
        print(f"Error: File '{csvFile}' not found.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: File '{csvFile}' is empty.")
        return
    
    # Check if the column exists
    if columnName not in df.columns:
        print(f"Error: Column '{columnName}' not found in the CSV file '{csvFile}'.")
        return

    # Transform the "Pitcher" column
    if columnName == "Pitcher":
        df["Pitcher"] = df["Pitcher"].apply(lambda x: ''.join(word.capitalize() for word in x.split(', ')))
    
    # Extract the data from the specified column
    column_data = df[columnName]

    # Print the data
    print(f"Data in column '{columnName}' of CSV file '{csvFile}':")
    print(column_data)
    print("\n")

# 'main'
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <directory> <column>")

    else:
        # Check directory
        directory = sys.argv[1]
        if not os.path.isdir(directory):
            print(f"Error: '{directory}' is not a directory.")

        else:
            # Check for .csv file(s)
            csv_files = [file for file in os.listdir(directory) if file.endswith('.csv')]
            if not csv_files:
                print(f"No CSV files found in directory '{directory}'.")

            else:
                # Print 'column' data for all .csv files
                for csv_file in csv_files:
                    csv_path = os.path.join(directory, csv_file)
                    getData(sys.argv[2], csv_path)