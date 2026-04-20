from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'dev-secret')

from database import db

db.init_app(app)

from models import Task, Tag, task_tags

PRIORITY_CHOICES = ['Low', 'Medium', 'High']
STATUS_CHOICES = ['Pending', 'In Progress', 'Completed']


def create_app():
    return app


@app.before_first_request
def ensure_db():
    db.create_all()


@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    tag_id = request.args.get('tag', type=int)

    tasks_query = Task.query.order_by(Task.due_date.nullslast(), Task.created_at.desc())

    if q:
        search = f"%{q}%"
        tasks_query = tasks_query.filter(
            (Task.title.ilike(search)) | (Task.description.ilike(search))
        )

    if tag_id:
        tasks_query = tasks_query.join(Task.tags).filter(Tag.id == tag_id)

    tasks = tasks_query.all()
    tags = Tag.query.order_by(Tag.name).all()
    return render_template(
        'index.html',
        tasks=tasks,
        tags=tags,
        q=q,
        selected_tag=tag_id,
        priorities=PRIORITY_CHOICES,
        statuses=STATUS_CHOICES,
    )


@app.route('/task/new', methods=['GET', 'POST'])
def create_task():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Task title is required.', 'danger')
            return redirect(url_for('create_task'))

        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium')
        due_date = request.form.get('due_date')
        status = request.form.get('status', 'Pending')
        tag_names = request.form.get('tags', '').split(',')

        task = Task(
            title=title,
            description=description,
            priority=priority if priority in PRIORITY_CHOICES else 'Medium',
            due_date=datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None,
            status=status if status in STATUS_CHOICES else 'Pending',
        )

        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            tag = Tag.query.filter_by(name=name).first() or Tag(name=name)
            task.tags.append(tag)

        db.session.add(task)
        db.session.commit()
        flash('Task created successfully.', 'success')
        return redirect(url_for('index'))

    tags = Tag.query.order_by(Tag.name).all()
    return render_template('task_form.html', task=None, tags=tags, priorities=PRIORITY_CHOICES, statuses=STATUS_CHOICES)


@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Task title is required.', 'danger')
            return redirect(url_for('edit_task', task_id=task_id))

        task.title = title
        task.description = request.form.get('description', '').strip()
        task.priority = request.form.get('priority', 'Medium') if request.form.get('priority') in PRIORITY_CHOICES else 'Medium'
        task.status = request.form.get('status', 'Pending') if request.form.get('status') in STATUS_CHOICES else 'Pending'
        due_date = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None

        tag_names = request.form.get('tags', '').split(',')
        task.tags = []
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            tag = Tag.query.filter_by(name=name).first() or Tag(name=name)
            task.tags.append(tag)

        db.session.commit()
        flash('Task updated successfully.', 'success')
        return redirect(url_for('index'))

    tags = Tag.query.order_by(Tag.name).all()
    return render_template('task_form.html', task=task, tags=tags, priorities=PRIORITY_CHOICES, statuses=STATUS_CHOICES)


@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'success')
    return redirect(url_for('index'))


@app.route('/task/<int:task_id>')
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('task_detail.html', task=task)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
