# Flask ToDo App

A simple Flask-based ToDo application implementing task metadata, search, and tag filtering.

## Features

- Create, edit, and delete tasks
- Task description, priority, due date, and status
- Search tasks by title and description
- Tag tasks and filter by tag
- SQLite persistence
- Docker container support

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

## Docker

Build and run:

```bash
docker build -t todo-saas:0.1.0 .
docker run -p 5000:5000 todo-saas:0.1.0
```
