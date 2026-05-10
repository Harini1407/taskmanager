import pandas as pd
import numpy as np
from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = postgresql://taskdb_jlkh_user:ZdjmTCrfQSIKfBqkaSvKyBe4T1rETgiS@dpg-d80f53t0lvsc738lm6u0-a.oregon-postgres.render.com/taskdb_jlkh
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

socketio = SocketIO(app, cors_allowed_origins="*")


class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100))

    description = db.Column(db.String(200))

    priority = db.Column(db.String(20))


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(100))


@app.route('/', methods=['GET', 'POST'])
def home():

    if request.method == 'POST':

        title = request.form['title']

        description = request.form['description']

        priority = request.form['priority']

        new_task = Task(
            title=title,
            description=description,
            priority=priority
        )

        db.session.add(new_task)

        db.session.commit()

        socketio.emit('new_task', {
            'title': title
        })

        return redirect('/')

    tasks = Task.query.all()

    return render_template('index.html', tasks=tasks)


@app.route('/api/tasks')
def get_tasks():

    tasks = Task.query.all()

    task_list = []

    for task in tasks:

        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority
        }

        task_list.append(task_data)

    return {'tasks': task_list}


@app.route('/delete/<int:id>')
def delete_task(id):

    task = Task.query.get(id)

    db.session.delete(task)

    db.session.commit()

    return redirect('/')


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_task(id):

    task = Task.query.get(id)

    if request.method == 'POST':

        task.title = request.form['title']

        task.description = request.form['description']

        task.priority = request.form['priority']

        db.session.commit()

        return redirect('/')

    return render_template('update.html', task=task)


@app.route('/analytics')
def analytics():

    tasks = Task.query.all()

    if len(tasks) == 0:

        return render_template(
            'analytics.html',
            total_tasks=0,
            high_tasks=0,
            medium_tasks=0,
            low_tasks=0
        )

    task_data = []

    for task in tasks:

        task_data.append({
            'title': task.title,
            'priority': task.priority
        })

    df = pd.DataFrame(task_data)

    total_tasks = len(df)

    high_tasks = np.sum(df['priority'] == 'High')

    medium_tasks = np.sum(df['priority'] == 'Medium')

    low_tasks = np.sum(df['priority'] == 'Low')

    return render_template(
        'analytics.html',
        total_tasks=total_tasks,
        high_tasks=high_tasks,
        medium_tasks=medium_tasks,
        low_tasks=low_tasks
    )

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        new_user = User(
            username=username,
            password=password
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:

            return redirect('/')

    return render_template('login.html')


if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    socketio.run(app, debug=True)