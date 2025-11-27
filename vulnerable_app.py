from flask import Flask, request, render_template_string, session, redirect, url_for, flash, g
import sqlite3
import os
import hashlib

app = Flask(__name__)
# IL 3.2: La llave secreta se mantiene en un lugar seguro (os.urandom(24))
app.secret_key = os.urandom(24) 

# IL 3.2: Corrección Adicional DAST: Añadir Headers de Seguridad (X-Content-Type-Options)
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # También se podría añadir Content-Security-Policy o Strict-Transport-Security (HSTS)
    return response

def get_db_connection():
    # Usar g para manejar la conexión y asegurar que se cierra
    if 'db' not in g:
        g.db = sqlite3.connect('database.db')
        g.db.row_factory = sqlite3.Row
    return g.db

# Función para cerrar la conexión al finalizar la solicitud
@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def hash_password(password):
    # IL 3.1: Usar SHA256 es mejor que MD5, pero se recomienda bcrypt o Argon2 para producción real.
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/')
def index():
    return 'Welcome to the Task Manager Application!'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()

        # IL 3.1: CORRECCIÓN DE INYECCIÓN SQL (CWE-89)
        # Se elimina el bloque 'if' vulnerable y se usa siempre la consulta parametrizada.
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        hashed_password = hash_password(password)
        
        # Uso seguro de consultas parametrizadas (SQLite se encarga del 'escaping')
        user = conn.execute(query, (username, hashed_password)).fetchone()

        # Se elimina el 'print' de la consulta para evitar fuga de información en logs
        # print("Consulta SQL generada:", query) 

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials!'
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    # IL 3.1: La consulta de tareas ya usaba un parámetro seguro, se mantiene.
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()

    # NOTA: Jinja2 usado por Flask hace auto-escaping por defecto, mitigando XSS en la mayoría de casos.

    return render_template_string('''
        <h1>Welcome, user {{ user_id }}!</h1>
        <form action="/add_task" method="post">
            <input type="text" name="task" placeholder="New task"><br>
            <input type="submit" value="Add Task">
        </form>
        <h2>Your Tasks</h2>
        <ul>
        {% for task in tasks %}
            <li>{{ task['task'] }} <a href="/delete_task/{{ task['id'] }}">Delete</a></li>
        {% endfor %}
        </ul>
    ''', user_id=user_id, tasks=tasks)


@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = request.form['task']
    user_id = session['user_id']

    conn = get_db_connection()
    # IL 3.1: La inserción de tareas ya usaba parámetros seguros, se mantiene.
    conn.execute(
        "INSERT INTO tasks (user_id, task) VALUES (?, ?)", (user_id, task))
    conn.commit()

    return redirect(url_for('dashboard'))


@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    # IL 3.1: La eliminación ya usaba parámetros seguros, se mantiene.
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()

    return redirect(url_for('dashboard'))


@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    return 'Welcome to the admin panel!'


if __name__ == '__main__':
    # NOTA: debug=True nunca debe usarse en producción.
    # En un entorno real, ejecutaríamos: gunicorn -w 4 vulnerable_app:app
    app.run(host='0.0.0.0', port=8080)