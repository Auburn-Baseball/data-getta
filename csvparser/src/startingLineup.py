'''
Python script to retrieve the starting lineup of a team

run:
    python3 startingLineup.py </filePath/file.csv>

call:
    dict = startingLineup.get_starting_lineup(csvFilePath)

Auth: Micah Key, ___
'''

# Imports
import csv
import sys


# Method to parse csv for the first 9 players in each team
def get_starting_lineup(csvFile):
    starting_lineups = {}

    try:
        # Open the CSV file
        with open(csvFile, 'r', newline='') as file:
            reader = csv.DictReader(file)
            
            # Iterate through each row in the CSV
            for row in reader:
                # Extract team and batter information
                team = row['BatterTeam']
                batter = row['Batter']
                
                # Check if the team is already in the starting_lineups dictionary
                if team not in starting_lineups:
                    starting_lineups[team] = []
                
                # Check if the batter is not already in the lineup for this team
                if batter not in starting_lineups[team]:
                    # Append batter to the corresponding team's starting lineup
                    if len(starting_lineups[team]) < 9:
                        starting_lineups[team].append(batter)

    except FileNotFoundError:
        print(f"Error: File '{csvFile}' not found.")
    except csv.Error as e:
        print(f"Error reading CSV file '{csvFile}': {e}")

    return starting_lineups

# end of get_starting_lineup(csv_file) 


# Method that prints the linups from the array
def print_starting_lineups(starting_lineups):
    for team, lineup in starting_lineups.items():
        print(f"Starting lineup for {team}:")
        for index, batter in enumerate(lineup, start=1):
            print(f"{index}. {batter}")
        print()

# end of print_starting_linups(starting_lineups)

# 'main'
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('python3 startingLineup.py /filePath/file.csv')
    
    else:
        # Get starting lineups from the CSV
        starting_lineups = get_starting_lineup(sys.argv[1])
        
        # Print starting lineups / Change to do what you need <here
        print_starting_lineups(starting_lineups)