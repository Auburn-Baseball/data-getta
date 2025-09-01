'''
Python script to test the connection to the sql database

run:
    python3 sqlConnectTest.py

Auth: Micah Key
'''

# Imports
import psycopg2
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

# Connect to database and print out table names
def connect():    
    try:
        # Postgres connect
        conn = psycopg2.connect(
                                host=f"{yaml_.get('SQL_SERVER_NAME')}", 
                                port=f"{yaml_.get('SQL_PORT')}", 
                                database=f"{yaml_.get('SQL_DB_NAME')}", 
                                user=f"{yaml_.get('SQL_USERNAME')}", 
                                password=f"{yaml_.get('SQL_PASSWORD')}"
                               )

        # Make cursor
        curs = conn.cursor()

        # Pull and print out metadata (a large amount of data)
        curs.execute('SELECT * FROM trackman_metadata;')
        print(curs.fetchall())

        # Close connection
        curs.close()
        conn.close()

    except Exception as e:
        print("Connection failed:", e)
        return
    
# end of connect()

# 'main'
if __name__ == '__main__':
    setup_yaml()
    connect()