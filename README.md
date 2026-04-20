# Flask ToDo App

A simple Flask ToDo application using file-based JSON persistence instead of a database.

## Features

- Create, edit, and delete tasks
- Task title, description, priority, status, and due date
- Search tasks by title and description
- Persistent storage in `todo.json`

## Run locally

1. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. Start the app:
   ```bash
   python3 app.py
   ```
3. Open `http://127.0.0.1:5000`

## Storage

Tasks are saved to a local JSON file named `todo.json` in the repository root.

## Notes

- No SQL database is required.
- Task metadata is persisted as JSON.
