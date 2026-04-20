import json
from datetime import datetime, date
from pathlib import Path
import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'dev-secret')

DATA_FILE = Path(os.getenv('TODO_DATA_FILE', 'todo.json'))
PRIORITY_CHOICES = ['Low', 'Medium', 'High']
STATUS_CHOICES = ['Pending', 'In Progress', 'Completed']


def ensure_data_file():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text('[]', encoding='utf-8')


def load_tasks():
    ensure_data_file()
    with DATA_FILE.open('r', encoding='utf-8') as handle:
        raw_tasks = json.load(handle)

    tasks = []
    for task in raw_tasks:
        tasks.append(normalize_task(task))
    return tasks


def save_tasks(tasks):
    raw_tasks = [serialize_task(task) for task in tasks]
    with DATA_FILE.open('w', encoding='utf-8') as handle:
        json.dump(raw_tasks, handle, indent=2)


def normalize_task(task):
    due_date = task.get('due_date')
    if isinstance(due_date, str) and due_date:
        due_date = date.fromisoformat(due_date)

    created_at = task.get('created_at')
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    updated_at = task.get('updated_at')
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)

    return {
        'id': task['id'],
        'title': task.get('title', ''),
        'description': task.get('description', ''),
        'priority': task.get('priority', 'Medium'),
        'status': task.get('status', 'Pending'),
        'due_date': due_date,
        'created_at': created_at,
        'updated_at': updated_at,
        'tags': task.get('tags', []),
    }


def serialize_task(task):
    return {
        'id': task['id'],
        'title': task['title'],
        'description': task['description'],
        'priority': task['priority'],
        'status': task['status'],
        'due_date': task['due_date'].isoformat() if task['due_date'] else '',
        'created_at': task['created_at'].isoformat(),
        'updated_at': task['updated_at'].isoformat(),
        'tags': task['tags'],
    }


def next_task_id(tasks):
    if not tasks:
        return 1
    return max(task['id'] for task in tasks) + 1


def get_task_or_404(task_id, tasks):
    for task in tasks:
        if task['id'] == task_id:
            return task
    abort(404)


def parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value)


def sort_tasks(tasks):
    return sorted(
        tasks,
        key=lambda task: (
            task['due_date'] is None,
            task['due_date'] if task['due_date'] else date.max,
            -task['created_at'].timestamp(),
        ),
    )


@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    priority_filter = request.args.get('priority', '').strip()
    due_date_from = request.args.get('due_date_from', '').strip()
    due_date_to = request.args.get('due_date_to', '').strip()
    tag_filter = request.args.get('tag', '').strip()
    sort_by = request.args.get('sort', 'due_date').strip()

    tasks = load_tasks()

    if q:
        q_lower = q.lower()
        tasks = [
            task for task in tasks
            if q_lower in task['title'].lower() or q_lower in task['description'].lower()
        ]

    if status_filter:
        tasks = [task for task in tasks if task['status'] == status_filter]

    if priority_filter:
        tasks = [task for task in tasks if task['priority'] == priority_filter]

    if due_date_from:
        from_date = date.fromisoformat(due_date_from)
        tasks = [task for task in tasks if task['due_date'] and task['due_date'] >= from_date]

    if due_date_to:
        to_date = date.fromisoformat(due_date_to)
        tasks = [task for task in tasks if task['due_date'] and task['due_date'] <= to_date]

    if tag_filter:
        tasks = [task for task in tasks if tag_filter in task['tags']]

    # Sorting
    if sort_by == 'due_date':
        tasks = sorted(tasks, key=lambda t: (t['due_date'] is None, t['due_date'] or date.max))
    elif sort_by == 'created_at':
        tasks = sorted(tasks, key=lambda t: t['created_at'], reverse=True)
    elif sort_by == 'priority':
        priority_order = {'Low': 1, 'Medium': 2, 'High': 3}
        tasks = sorted(tasks, key=lambda t: priority_order.get(t['priority'], 0), reverse=True)
    else:
        tasks = sort_tasks(tasks)  # default

    # Get unique tags for filter dropdown
    all_tags = set()
    for task in load_tasks():
        all_tags.update(task['tags'])
    tags = sorted(list(all_tags))

    return render_template('index.html', tasks=tasks, q=q, status_filter=status_filter, priority_filter=priority_filter, due_date_from=due_date_from, due_date_to=due_date_to, tag_filter=tag_filter, sort_by=sort_by, tags=tags)


@app.route('/task/new', methods=['GET', 'POST'])
def create_task():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Task title is required.', 'danger')
            return redirect(url_for('create_task'))

        tasks = load_tasks()
        now = datetime.utcnow()
        tags = [tag.strip() for tag in request.form.get('tags', '').split(',') if tag.strip()]
        task = {
            'id': next_task_id(tasks),
            'title': title,
            'description': request.form.get('description', '').strip(),
            'priority': request.form.get('priority', 'Medium') if request.form.get('priority') in PRIORITY_CHOICES else 'Medium',
            'status': request.form.get('status', 'Pending') if request.form.get('status') in STATUS_CHOICES else 'Pending',
            'due_date': parse_date(request.form.get('due_date')),
            'created_at': now,
            'updated_at': now,
            'tags': tags,
        }
        tasks.append(task)
        save_tasks(tasks)
        flash('Task created successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('task_form.html', task=None, priorities=PRIORITY_CHOICES, statuses=STATUS_CHOICES)


@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    tasks = load_tasks()
    task = get_task_or_404(task_id, tasks)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Task title is required.', 'danger')
            return redirect(url_for('edit_task', task_id=task_id))

        task['title'] = title
        task['description'] = request.form.get('description', '').strip()
        task['priority'] = request.form.get('priority', 'Medium') if request.form.get('priority') in PRIORITY_CHOICES else 'Medium'
        task['status'] = request.form.get('status', 'Pending') if request.form.get('status') in STATUS_CHOICES else 'Pending'
        task['due_date'] = parse_date(request.form.get('due_date'))
        task['tags'] = [tag.strip() for tag in request.form.get('tags', '').split(',') if tag.strip()]
        task['updated_at'] = datetime.utcnow()

        save_tasks(tasks)
        flash('Task updated successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('task_form.html', task=task, priorities=PRIORITY_CHOICES, statuses=STATUS_CHOICES)


@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    tasks = load_tasks()
    tasks = [task for task in tasks if task['id'] != task_id]
    save_tasks(tasks)
    flash('Task deleted.', 'success')
    return redirect(url_for('index'))


@app.route('/task/<int:task_id>')
def task_detail(task_id):
    tasks = load_tasks()
    task = get_task_or_404(task_id, tasks)
    return render_template('task_detail.html', task=task)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
