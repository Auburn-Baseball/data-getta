'''
Python script to parse a .txt file of the schema to a .json file for csvParser.py

run:
    python3 txtJsonParse.py

Auth: Micah Key
'''

# Imports
import re
import json
import yaml

# Set up YAML
def setup_yaml():
    try:
        global yaml_
        # Load YAML configuration file
        with open('../include/config.yaml', 'r') as file:
            yaml_ = yaml.safe_load(file)

    except FileNotFoundError:
        print("Error: The specified file was not found.")
        return
    except yaml.YAMLError as e:
        print("Error loading YAML data:", e)
        return
    except Exception as e:
        print("An unexpected error occurred:", e)
        return

# end of setup_yaml()


# Method to parse a .txt to .json file
def parse_txt_to_json(txtFile):
    # Variables
    tables = {}
    current_table = None
    all_column_names = set()

    try:
        # Open txt file
        with open(txtFile, 'r') as file:
            for line in file:
                # Remove leading/trailing whitespace
                line = line.strip()  

                # Get table name and entries
                if line.startswith('Table'):
                    table_name = line.split()[1]
                    tables[table_name] = {'columns': []}
                    current_table = table_name

                # Extract referenced tables and columns
                elif line.startswith('Ref'):
                    ref_match = re.match(r'Ref: (.+)\.(.+) - (.+)\.(.+)', line)

                    if ref_match:
                        ref_table1, ref_column1, ref_table2, ref_column2 = ref_match.groups()
                        ref_entry = {'table': ref_table1, 'column': ref_column1, 'ref_table': ref_table2, 'ref_column': ref_column2}
                        
                        if current_table is not None:
                            tables[current_table]['columns'].append(ref_entry) 
                
                # Reset current table when encountering '}'
                elif line.startswith('}'):
                    current_table = None

                
                # Parse column name and type
                elif current_table:
                    column_name, column_type = line.split()[:2]
                    
                    if column_name not in all_column_names:
                        all_column_names.add(column_name)

                        # Add column entry to current table
                        tables[current_table]['columns'].append({'name': column_name, 'type': column_type})

    except FileNotFoundError:
        print(f"Error: File '{txtFile}' not found.")
        return None
    except Exception as e:
        print("An unexpected error occurred:", e)
        return None
    
    # JSON data dictionary
    json_data = {'columns': []} 

    for table_name, table_info in tables.items():
        json_data['columns'] += table_info['columns']

    return json_data

# end of parse_txt_to_json(txtFile)

# 'main'
if __name__ == "__main__":
    try:
        # setup yaml
        setup_yaml()

        # get data from txt file
        json_data = parse_txt_to_json(yaml_.get('SCHEMA_TXT'))

        # write data to json file
        with open(yaml_.get('JSON_MAP'), 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

    except FileNotFoundError as e:
        print(f"Error: File not found: {e.filename}")
    except Exception as e:
        print("An unexpected error occurred:", e)