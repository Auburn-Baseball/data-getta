# Developer Docs for the Postgres Database of the Data Getta Project for Auburn Baseball

Last Updated: April 22, 2024 by Caden Garrett

## Database General Information

The database for the Data Getta project is a Postgresql Docker container hosted on the Data Getta server.
The current username, password, and port are all located in the **db.env** file in the root of the project.
The current port that is used for connecting to the database is the default port of 5432.

### Version

The current version of Postgresql that is being used is Version 16.

### Documentation

Here is the link for the official Postgresql documentation: https://www.postgresql.org/docs/

Here is also a link for learning SQL: https://www.w3schools.com/sql/

## Database SQL Files

The way that SQL scripts are stored and ran is through a series of SQL files in the **database/sql** folder in the root of the project. The reason for this is to allow for easy version control and to allow for easy access to the SQL scripts and a easy way to run them if something were to happen to the database.
Here is a current list of the SQL files in the **database/sql** folder and what they do:

- **add-conferences.sql** - Adds the NCAA Division 1 baseball conferences to the database in the `conferences` table.
- **functions.sql** - Contains all of the functions that are used both by the database itself and the modeling teams connecting to the database. Documentation of the functions and what they do individually can be found within the actual file.
- **keepd1.sql** - When ran, will go through and delete all teams that have their conference set to `NotSet` and every bit of data that is associated with those teams. This is ran immediately after the **team-assignment.sql** script is ran.
- **pre-schema.sql** - Provides the database with all the necessary extensions, types, or anything else that is needed before the schema is created.
- **schema.sql** - Houses the schema used for the database. This includes all of the tables, constraints, and indexes that are used in the database.
- **seasons.sql** - Adds the NCAA Division 1 baseball seasons to the database in the `seasons` table.
- **team-assignment.sql** - Assigns each team to a conference based on the conference that is in the `conferences` table. This script is intended to be run after any new data is added to ensure all the correct and relevant data is present in the database.
- **views.sql** - Contains all of the views that are used by the database itself and the modeling teams connecting to the database. Documentation of the views and what they do individually can be found within the actual file.

## Future Work and Goals
