'''
Python script that fixes the log files

run:
    python3 fixLog.py <filePath/fileName>

Auth: Micah Key
'''

# Imports
import sys

# Method to remove duplicate lines from txt file
def remove_duplicates(file_path):
    # Read lines from the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Remove duplicates while preserving the order
    unique_lines = []
    for line in lines:
        if line.strip() not in unique_lines:
            unique_lines.append(line.strip())

    # Write unique lines back to the file
    with open(file_path, 'w') as file:
        for line in unique_lines:
            file.write(line + '\n')

    print("Duplicates removed successfully.")
# end of remove_duplicates()

# Main
if __name__ == '__main__':
    # Check arguments
    if len(sys.argv) != 2:
        print('error: python3 fixLog.py <filePath/fileName>')
        sys.exit(1)
    
    # Run script
    remove_duplicates(sys.argv[1])