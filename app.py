from flask import Flask, jsonify, request, abort
from flask_httpauth import HTTPBasicAuth
import mysql.connector
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
auth = HTTPBasicAuth()
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend

# MySQL connection settings
db_config = {
    "host": "localhost",  # Change if using a remote MySQL server
    "user": "root",       # MySQL username
    "password": "root",       # MySQL password
    "database": "insert"
}

# Basic Authentication credentials (example)
users = {
    "admin": "password123"
}

# Basic Authentication callback
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

# MySQL connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

# API Endpoints

@app.route('/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tasks)

@app.route('/tasks/<task_id>', methods=['GET'])
@auth.login_required
def get_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
    task = cursor.fetchone()
    cursor.close()
    conn.close()
    if task is None:
        abort(404, description="Task not found")
    return jsonify(task)

@app.route('/tasks', methods=['POST'])
@auth.login_required
def create_task():
    data = request.get_json()
    if not data or 'title' not in data or 'description' not in data or 'due_date' not in data:
        abort(400, description="Missing required fields")
    
    try:
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
    except ValueError:
        abort(400, description="Invalid date format, should be YYYY-MM-DD")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (title, description, due_date)
        VALUES (%s, %s, %s)
    ''', (data['title'], data['description'], due_date))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Task created successfully'}), 201

@app.route('/tasks/<task_id>', methods=['PUT'])
@auth.login_required
def update_task(task_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
    task = cursor.fetchone()
    if task is None:
        cursor.close()
        conn.close()
        abort(404, description="Task not found")

    update_data = []
    update_query = "UPDATE tasks SET"
    if 'title' in data:
        update_query += " title = %s,"
        update_data.append(data['title'])
    if 'description' in data:
        update_query += " description = %s,"
        update_data.append(data['description'])
    if 'due_date' in data:
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            update_query += " due_date = %s,"
            update_data.append(due_date)
        except ValueError:
            cursor.close()
            conn.close()
            abort(400, description="Invalid date format")
    
    update_query = update_query.rstrip(',') + " WHERE id = %s"
    update_data.append(task_id)

    cursor.execute(update_query, tuple(update_data))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Task updated successfully'})

@app.route('/tasks/<task_id>', methods=['DELETE'])
@auth.login_required
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
    task = cursor.fetchone()
    if task is None:
        cursor.close()
        conn.close()
        abort(404, description="Task not found")
    
    cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return '', 204

@app.route('/tasks/<task_id>/complete', methods=['PATCH'])
@auth.login_required
def complete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
    task = cursor.fetchone()
    if task is None:
        cursor.close()
        conn.close()
        abort(404, description="Task not found")
    
    cursor.execute('UPDATE tasks SET status = %s WHERE id = %s', ('completed', task_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Task marked as completed'})

# Error Handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized"}), 401

if __name__ == '__main__':
    app.run(debug=True)
