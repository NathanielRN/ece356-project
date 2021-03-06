# UN*X File System - Relational Database
This is our ECE 356 Project Submission made by Eliseo Ruiz Nowell
and Gerald Aryeetey

## Project Description
This project uses MySQL to implement a UN*X File System using a Relational
Database. An ER Model of the Database is included in the root folder, and the
tables used are all in BCNF and therefore _normalized_.

## System Requirements
Python 3.X+
hon 3.X+
  * PIP
MySQL 8.0+

## Steps Before you Run Our Project
1. If you don't have it, download python pip using `sudo apt install python3-pip`
2. Install the mysql connector using pip `apt install mysql-connector-python`
3. Create an empty MySQL Database `CREATE <database_name>` and run `USE <database_name>`
4. Run `SOURCE fs_schema.sql` within the mysql database 
5. Copy .fs_db_rdbsh template and store it in ./.fs_db_rdbsh or ~/.fs_db_rdbsh
6. Fill in ./.fs_db.rdbsh with your specific database information
7. Fill the database with data by running `./fill_fs_rd.py` (If you want to see 
A LOT MORE data, rename the setup_template folder to be setup, we used the
current one for the demo and for testing because it was faster)

## Navigating the File System
1. Run `./rdbsh` to enter the file system
2. To exit, press Ctrl+D or alternatively type `exit` and press enter

## Potential Issues
* Too long of file paths or names i.e. filename/username/groupname
