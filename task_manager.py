import mysql.connector
import datetime
from mysql.connector import Error
import threading
import time

# Database Configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'newpassword',
    'database': 'taskdb'
}

# Validation of inputs
def validate_date(date_str):
    try:
        due = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        if due < today:
            print("Due date cannot be in the past.")
            return False
        return True
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return False

def validate_priority(priority):
    return priority in ["Low", "Medium", "High"]

def validate_status(status):
    return status in ["Pending", "In Progress", "Completed"]

def task_exists(task_id, tm):
    if not task_id.isdigit():
        return False
    tm.cursor.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
    return tm.cursor.fetchone() is not None


# Task class representing a task object
class Task:
    def __init__(self, id, title, description, due_date, priority, status, timestamp):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = status
        self.timestamp = timestamp

    def __repr__(self):
        return f"[{self.id}] {self.title} ({self.priority}) - {self.status} - Due: {self.due_date}"

# Handles all database operations and task management
class TaskManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**self.db_config)
            self.cursor = self.conn.cursor(dictionary=True)
            print("Successfully connected to the database.")
        except Error as error:
            print("Database connection error:", error)

    # Add a new task record to the database
    def add_task(self, title, description, due_date, priority):
        try:
            sql = """INSERT INTO tasks (title, description, due_date, priority) VALUES (%s, %s, %s, %s)"""
            self.cursor.execute(sql, (title, description, due_date, priority))
            self.conn.commit()
            print("Task successfully added!")
        except Error as e:
            print("Error adding task:", e)

    # List tasks optionally filtered by a field and value
    def list_tasks(self, filter_by=None, filter_value=None):
        sql = "SELECT * FROM tasks"
        parameters = ()
        if filter_by and filter_value:
            sql += f" WHERE {filter_by} = %s"
            parameters = (filter_value,)
        try:
            self.cursor.execute(sql, parameters)
            results = self.cursor.fetchall()
            if not results:
                print("No tasks found.")
                return
            for row in results:
                print(Task(
                    id=row['id'],
                    title=row['title'],
                    description=row['description'],
                    due_date=row['due_date'],
                    priority=row['priority'],
                    status=row['status'],
                    timestamp=row['timestamp']
                ))
        except Error as e:
            print("Error listing tasks:", e)
    
    # Update an existing task, only changing specified fields
    def update_task(self, task_id, title=None, description=None, due_date=None, priority=None, status=None):
        fields = []
        values = []
        if title: 
            fields.append("title=%s")
            values.append(title)
        if description: 
            fields.append("description=%s")
            values.append(description)
        if due_date: 
            fields.append("due_date=%s")
            values.append(due_date)
        if priority: 
            fields.append("priority=%s")
            values.append(priority)
        if status: 
            fields.append("status=%s")
            values.append(status)
        if not fields:
            print("No task was updated.")
            return
        
        values.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id=%s"
        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
            print("Task has been updated.")
        except Error as e:
            print("Error updating task:", e)

    # Mark a task's status as Completed
    def mark_completed(self, task_id):
        try:
            self.cursor.execute("UPDATE tasks SET status = %s WHERE id = %s", ("Completed", task_id))
            self.conn.commit()
            print(f"Task {task_id} is marked as completed.")
        except Error as e:
            print("Error marking task:", e)

    # Delete a task by its ID
    def delete_task(self, task_id):
        try:
            self.cursor.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
            self.conn.commit()
            print(f"Task {task_id} has been deleted.")
        except Error as e:
            print("Error deleting task:", e)

# Background thread function to remind user of tasks due today every 60 seconds
def due_date_reminder(tm):
    while True:
        try:
            today = datetime.date.today()
            tm.cursor.execute(
                "SELECT * FROM tasks WHERE status = %s AND due_date = %s",
                ("Pending", today)
            )
            results = tm.cursor.fetchall()
            if results:
                print("\n Reminder: You have tasks due today!")
                for row in results:
                    print(f"  - {row['title']} (ID: {row['id']})")
            time.sleep(60)  # check every 60 seconds
        except Exception as e:
            print(" Reminder thread error:", e)
            break

# CLI Menu
if __name__ == "__main__":
    tm = TaskManager(DB_CONFIG)

    # Start background reminder thread
    reminder_thread = threading.Thread(target=due_date_reminder, args=(tm,), daemon=True)
    reminder_thread.start()

    while True:
        print("\n--- Task Manager Menu ---")
        print("[1] Add Task")
        print("[2] List Tasks")
        print("[3] Update Task")
        print("[4] Delete Task")
        print("[5] Mark Task as Completed")
        print("[6] Exit")

        choice = input("Enter choice: ").strip()

        # Add a new task
        if choice == "1":
            title = input("Title: ").strip()
            if not title:
                print("Title cannot be empty.")
                continue

            description = input("Description: ").strip() or ""

            due_date = input("Due Date (YYYY-MM-DD): ").strip()
            if not due_date:
                print("Due date is required.")
                continue
            if not validate_date(due_date):
                continue

            priority = input("Priority (Low, Medium, High): ").strip().title()
            if not validate_priority(priority):
                print("Invalid priority.")
                continue

            tm.add_task(title, description, due_date, priority)

        # List all tasks or with filter options
        elif choice == "2":
            print("Filter options:")
            print("1. No filter (list all)")
            print("2. Filter by Status")
            print("3. Filter by Priority")
            print("4. Filter by Due Date")
            f_choice = input("Choose filter: ").strip()

            if f_choice == "1":
                tm.list_tasks()

            elif f_choice == "2":
                status = input("Enter status (Pending, In Progress, Completed): ").strip().title()
                if not validate_status(status):
                    print("Invalid status.")
                else:
                    tm.list_tasks("status", status)

            elif f_choice == "3":
                priority = input("Enter priority (Low, Medium, High): ").strip().title()
                if not validate_priority(priority):
                    print("Invalid priority.")
                else:
                    tm.list_tasks("priority", priority)

            elif f_choice == "4":
                due_date = input("Enter due date (YYYY-MM-DD): ").strip()
                if not validate_date(due_date):
                    print("Invalid date format.")
                else:
                    tm.list_tasks("due_date", due_date)
            else:
                print("Invalid filter choice.")

        # Update a task by ID
        elif choice == "3":
            task_id = input("Enter task ID to update: ").strip()
            if not task_exists(task_id, tm):
                print("Invalid or non-existent task ID.")
                continue

            title = input("New title (leave blank to skip): ") or None
            description = input("New description (leave blank to skip): ") or None
            
            due_date = input("New due date (YYYY-MM-DD, leave blank to skip): ") or None
            if due_date and not validate_date(due_date):
                continue

            priority = input("New priority (Low, Medium, High, leave blank to skip): ") or None
            if priority and not validate_priority(priority.title()):
                print("Invalid priority.")
                continue

            status = input("New status (Pending, In Progress, Completed, leave blank to skip): ") or None
            if status and not validate_status(status.title()):
                print("Invalid status.")
                continue

            tm.update_task(task_id, title, description, due_date, priority, status)

        # Delete a task by ID
        elif choice == "4":
            task_id = input("Enter task ID to delete: ").strip()
            if not task_exists(task_id, tm):
                print("Invalid or non-existent task ID.")
                continue
            tm.delete_task(task_id)

        # Mark task as accomplished by ID
        elif choice == "5":
            task_id = input("Enter task ID to mark as completed: ").strip()
            if not task_exists(task_id, tm):
                print("Invalid or non-existent task ID.")
                continue
            tm.mark_completed(task_id)

        elif choice == "6":
            print("Exiting...")
            break

        else:
            print("Invalid choice, please try again.")
