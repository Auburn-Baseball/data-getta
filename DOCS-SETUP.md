# Developer Docs for the server Infrastructure of the Data Getta Project for Auburn Baseball

Last Updated: April 22, 2024 by Caden Garrett

## Server General Information

The server for the Data Getta project is setup and ran by the OIT department at Auburn University, and is ran on campus and is accessible through the Auburn University VPN.
It is a Linux machine and is running Ubuntu 22.04 LTS.
The specs of the server are as follows:

- 24 GB of RAM
- 2 CPUs
- 5 TB of storage
- Current URL is datagetta.cse.eng.auburn.edu

This server is used to host the Postgresql database, the Next.js frontend, and te Python code for the modeling teams. All other code associated with the Data Getta project is stored on the server as well.

### Documentation 

Here is a few links that are useful for managing the server:

- Ubuntu Documentation - https://ubuntu.com/server/docs
- Docker Documentation - https://docs.docker.com/
- Bash Documentation - https://www.gnu.org/software/bash/manual/bash.html

## Server and Project Access

Since OIT manages the machine, the way to access the server if you are a new developer on this project is to email a member of OIT and request an account. The account will be created and you will be given the username and password to access the server under your own account.

Currently, we have most of the code available via a `git pull` from our GitHub repository. However, there are some env files and other configurations that was intentionally left out of the public repo. These files will need to be copied over to your new account on the server. The current location of the Data Getta project is in the `/home/csg0026/project/datagetta` folder.

### NOTE: DO NOT CHANGE SSH SETTINGS, ACCOUNT NAMES, OR PASSWORDS WITHOUT PERMISSION FROM OIT.

## Project Configuration

Since we are using different services for our UI, backend, and python code, we decided to use `docker-compose` to manage all of the services. This allows us to easily start, stop, and manage all of the services at once.

The current `docker-compose.yml` file is located in the root of the project. This file is used to start all of the services that are needed for the Data Getta project. The services that are currently being used are:

- Postgresql
- Next.js
- Python

The `docker-compose.yml` file is used to start all of the services at once. To start the services, you will need to run the following command:

```bash
docker compose up -d --build
```

This will start all of the services and you will be able to access the UI at `datagetta.cse.eng.auburn.edu`.

## Cron Script

The server has a cron script that is used to add new data and update the whole project afterwards. This script is set to run every Monday morning at 2:00 AM CST. This is done to ensure that the new data is updated and the whole project is updated before the start of the work week. Currently, the script does nothing of use but the setup is there to easily add the functionality.

## Future Work and Goals

- Add the ability to automatically create backups of the data and store them in a secure location.
- Finish the cron script to add new data and update the project.
