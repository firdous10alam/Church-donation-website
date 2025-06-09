from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import mysql.connector
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="templates")


# Routes
@app.route('/', methods=["GET", "POST"])
def home():
    return render_template('home.html')


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']

#         db = get_db()
#         cursor = db.cursor(dictionary=True)
#         cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
#         user = cursor.fetchone()
#         cursor.close()

#         if user and check_password_hash(user['password'], password):
#             session['user_id'] = user['id']
#             session['user_name'] = user['full_name']
#             return redirect(url_for('dashboard'))

#         return render_template('login.html', error="Invalid credentials")

#     return render_template('login.html')

# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         full_name = request.form['full_name']
#         email = request.form['email']
#         password = generate_password_hash(request.form['password'])
#         phone = request.form.get('phone', '')
#         address = request.form.get('address', '')

#         db = get_db()
#         cursor = db.cursor()
#         try:
#             cursor.execute("""
#             INSERT INTO users (full_name, email, password, phone, address)
#             VALUES (%s, %s, %s, %s, %s)
#             """, (full_name, email, password, phone, address))
#             db.commit()

#             # Get new user ID
#             user_id = cursor.lastrowid
#             session['user_id'] = user_id
#             session['user_name'] = full_name

#             return redirect(url_for('dashboard'))
#         except mysql.connector.Error as err:
#             db.rollback()
#             error = "Email already registered" if err.errno == 1062 else "Registration failed"
#             return render_template('signup.html', error=error)
#         finally:
#             cursor.close()

#     return render_template('signup.html')

# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('home'))

# @app.route('/dashboard')
# def dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     user_id = session['user_id']
#     db = get_db()
#     cursor = db.cursor(dictionary=True)

#     # Get user donations
#     cursor.execute("""
#     SELECT * FROM donations
#     WHERE user_id = %s
#     ORDER BY donation_date DESC
#     LIMIT 5
#     """, (user_id,))
#     donations = cursor.fetchall()

#     cursor.close()
#     return render_template('dashboard.html', donations=donations)

# @app.route('/branches')
# def branches():
#     db = get_db()
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM branches")
#     branches = cursor.fetchall()
#     cursor.close()
#     return render_template('branches.html', branches=branches)

# @app.route('/branch/<int:branch_id>')
# def branch_detail(branch_id):
#     db = get_db()
#     cursor = db.cursor(dictionary=True)

#     # Get branch details
#     cursor.execute("SELECT * FROM branches WHERE id = %s", (branch_id,))
#     branch = cursor.fetchone()

#     if not branch:
#         cursor.close()
#         return redirect(url_for('branches'))

#     # Get branch members
#     cursor.execute("SELECT * FROM members WHERE branch_id = %s", (branch_id,))
#     members = cursor.fetchall()

#     # Get branch events
#     cursor.execute("""
#     SELECT * FROM events
#     WHERE branch_id = %s AND event_date >= CURDATE()
#     ORDER BY event_date ASC
#     """, (branch_id,))
#     events = cursor.fetchall()

#     cursor.close()
#     return render_template('branch_detail.html',
#                          branch=branch,
#                          members=members,
#                          events=events)

# @app.route('/events')
# def events():
#     db = get_db()
#     cursor = db.cursor(dictionary=True)

#     # Get all upcoming events
#     cursor.execute("""
#     SELECT events.*, branches.name AS branch_name
#     FROM events
#     JOIN branches ON events.branch_id = branches.id
#     WHERE event_date >= CURDATE()
#     ORDER BY event_date ASC
#     """)
#     events = cursor.fetchall()

#     cursor.close()
#     return render_template('events.html', events=events)

# @app.route('/event/<int:event_id>')
# def event_detail(event_id):
#     db = get_db()
#     cursor = db.cursor(dictionary=True)

#     cursor.execute("""
#     SELECT events.*, branches.name AS branch_name, branches.address AS branch_address
#     FROM events
#     JOIN branches ON events.branch_id = branches.id
#     WHERE events.id = %s
#     """, (event_id,))
#     event = cursor.fetchone()

#     cursor.close()

#     if not event:
#         return redirect(url_for('events'))

#     return render_template('event_detail.html', event=event)

# @app.route('/donate', methods=['GET', 'POST'])
# def donate():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     if request.method == 'POST':
#         user_id = session['user_id']
#         amount = float(request.form['amount'])
#         payment_method = request.form['payment_method']
#         purpose = request.form['purpose']

#         # In a real app, you would integrate with a payment gateway here
#         # For demo, we'll just record the donation
#         transaction_id = f"CHURCH{datetime.now().strftime('%Y%m%d%H%M%S')}"

#         db = get_db()
#         cursor = db.cursor()
#         try:
#             cursor.execute("""
#             INSERT INTO donations
#             (user_id, amount, payment_method, purpose, transaction_id)
#             VALUES (%s, %s, %s, %s, %s)
#             """, (user_id, amount, payment_method, purpose, transaction_id))
#             db.commit()
#             return redirect(url_for('donation_success'))
#         except mysql.connector.Error as err:
#             db.rollback()
#             return render_template('donate.html', error="Donation failed")
#         finally:
#             cursor.close()

#     return render_template('donate.html')

# @app.route('/donation/success')
# def donation_success():
#     return render_template('donation_success.html')

# @app.route('/donations')
# def user_donations():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     user_id = session['user_id']
#     db = get_db()
#     cursor = db.cursor(dictionary=True)

#     cursor.execute("""
#     SELECT * FROM donations
#     WHERE user_id = %s
#     ORDER BY donation_date DESC
#     """, (user_id,))
#     donations = cursor.fetchall()

#     cursor.close()
#     return render_template('user_donations.html', donations=donations)

if __name__ == '__main__':
    app.run(debug=True)
