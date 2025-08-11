# Task Manager

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/laurence-c-jpg/task-manager.git
   cd your-repo

2. **Create and activate a virtual environment**
python -m venv venv
.\venv\Scripts\activate

3. **Install Dependencies**
pip install mysql-connector-python

4. **Set up MySQL Database**
CREATE DATABASE taskdb;
Run the schema.sql file included in this repository to create the required table:
mysql -u your_mysql_username -p taskdb < schema.sql

5. **Configure database connection**
If your MySQL username, password, or host differs, update the DB_CONFIG dictionary in the Python script accordingly.

6. **Run the application**
python task_manager.py

## Database Configuration
The schema.sql file contains the SQL commands to create the tasks table with the following columns:

id (INT, primary key, auto-increment)
title (VARCHAR)
description (TEXT)
due_date (DATE)
priority (ENUM: Low, Medium, High)
status (ENUM: Pending, In Progress, Completed)
timestamp (TIMESTAMP, default current timestamp)
