from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import requests
import pymysql
from models.model import analyze_text
import threading

app = Flask(__name__)
app.secret_key = 'hello'

# MySQL configuration
conn = pymysql.connect(host='localhost',
                       port=3306,
                       user='root',
                       password='Bharath@1708',
                       database='databse')

api_key = 'AIzaSyBnIHU7FBaxatDaR-tAh-ngvPkaW3shcnk'

# Function to remove non-toxic messages after 10 seconds
def remove_non_toxic_messages():
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE analysis != "Not Toxic"')
    conn.commit()
    cursor.close()

# Route for the home page
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('chat_room'))
    return render_template('index.html')

# Route for user signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Extract username and password from form data
        username = request.form['username']
        password = request.form['password']
        # Add code for inserting user into database (e.g., using conn.cursor())
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()
        cursor.close()
        # Redirect to login page after signup
        return redirect(url_for('login'))
    return render_template('signup.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Extract username and password from form data
        username = request.form['username']
        password = request.form['password']
        # Add code for verifying user credentials from database (e.g., using conn.cursor())
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            session['username'] = username
            return redirect(url_for('chat_room'))
        else:
            return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html')

# Route for user logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Route for the chat room
@app.route('/chat-room')
def chat_room():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat_room.html', username=session['username'])

# Route for sending messages
@app.route('/send-message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    message = request.form['message']
    username = session['username']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Call the analysis function to get analysis scores
    analysis = analyze_text(message, api_key)
    
    # Save message and analysis to database
    cursor = conn.cursor()
    if not analysis:
        # If analysis is empty, set default category and score
        max_category = "No Analysis"
    else:
        # Extract the maximum score and its corresponding category
        if analysis["TOXICITY"]["summaryScore"]["value"] > 0.40:
            analysis.pop("TOXICITY")
            max_category = max(analysis, key=lambda k: analysis[k]['summaryScore']['value'])
        else:
            max_category = "Not Toxic"
    cursor.execute('INSERT INTO messages (username, message, timestamp, analysis) VALUES (%s, %s, %s, %s)', (username, message, timestamp, max_category))
    conn.commit()
    cursor.close()

    # Start a thread to remove non-toxic messages after 10 seconds
    threading.Timer(5, remove_non_toxic_messages).start()

    return redirect(url_for('chat_room'))

# Route for fetching messages
@app.route('/fetch-messages')
def fetch_messages():
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 10')
    messages = cursor.fetchall()
    cursor.close()
    message_data = [{'username': msg[0], 'message': msg[1], 'timestamp': msg[2], 'analysis': msg[3]} for msg in reversed(messages)]
    return jsonify(message_data)

if __name__ == '__main__':
    app.run(debug=True)
