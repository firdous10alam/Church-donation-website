from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import mysql.connector
from datetime import datetime, date, time, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# ---------------------- Database Connection ---------------------- #


def get_db_connection(db_name):
    try:
        return mysql.connector.connect(host="localhost",
                                       user="root",
                                       password="PHW#84#jeorr",
                                       database=db_name)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None


# ---------------------- Helper Functions ------------------------- #


def format_event_time(time_value):
    """Handle all possible time formats: string, time, timedelta"""
    # Handle None case
    if time_value is None:
        print("in the none")
        return ""

    # Handle string input
    if isinstance(time_value, str):
        print("in the str")
        # If it's in HH:MM:SS format, convert to HH:MM
        if len(time_value) >= 5 and time_value.count(':') >= 1:
            return time_value[:5]
        return time_value

    # Handle time objects
    if isinstance(time_value, time):
        print("in the time")
        return time_value.strftime('%H:%M')

    # Handle timedelta objects
    if isinstance(time_value, timedelta):
        print("in the time delta")
        total_seconds = time_value.total_seconds()
        if total_seconds == 0:
            return "00:00"

        sign = '-' if total_seconds < 0 else ''
        total_seconds = abs(total_seconds)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{sign}{hours:02d}:{minutes:02d}"

    # Fallback for other types
    return str(time_value)


def format_event_date(date_value):
    """Format date objects consistently"""
    if date_value is None:
        return ""

    if hasattr(date_value, 'strftime'):
        print("in the strftime")
        return date_value.strftime('%Y-%m-%d')

    if isinstance(date_value, str) and len(date_value) >= 10:
        print("in the str")
        return date_value[:10]

    return str(date_value)


# ---------------------- Routes ----------------------------------- #


@app.route('/')
def home():
    conn = get_db_connection("church_db")
    if not conn:
        return render_template('error.html',
                               error="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        # Get upcoming events
        cursor.execute("""
        SELECT events.*, branches.name AS branch_name 
        FROM events 
        JOIN branches ON events.branch_id = branches.id
        ORDER BY event_date ASC
        LIMIT 3
        """)
        upcoming_events = cursor.fetchall()

        # Format events
        for event in upcoming_events:
            event['event_date'] = format_event_date(event.get('event_date'))
            event['event_time'] = format_event_time(event.get('event_time'))

        # Get branches
        cursor.execute("SELECT * FROM branches LIMIT 3")
        branches = cursor.fetchall()

        return render_template('home.html',
                               upcoming_events=upcoming_events,
                               branches=branches)
    except mysql.connector.Error as err:
        print(f"Database error in home route: {err}")
        return render_template('error.html', error="Database error")
    finally:
        cursor.close()
        conn.close()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection("church_db")
    if not conn:
        return render_template('error.html',
                               error="Database connection failed")

    cursor = conn.cursor(dictionary=True)

    try:
        # Get user details
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id, ))
        user_data = cursor.fetchone()

        if not user_data:
            return redirect(url_for('logout'))

        # Get user donations
        cursor.execute(
            """
        SELECT * FROM donations 
        WHERE user_id = %s
        ORDER BY donation_date DESC
        LIMIT 5
        """, (user_id, ))
        donations = cursor.fetchall()

        # Format donation dates
        for donation in donations:
            donation['donation_date'] = donation['donation_date'].strftime(
                '%Y-%m-%d %H:%M') if donation.get('donation_date') else ""

        # Get upcoming events for dashboard
        cursor.execute("""
        SELECT events.*, branches.name AS branch_name 
        FROM events 
        JOIN branches ON events.branch_id = branches.id
        ORDER BY event_date ASC
        LIMIT 3
        """)
        upcoming_events = cursor.fetchall() or []

        # Format events
        for event in upcoming_events:
            event['event_date'] = format_event_date(event.get('event_date'))
            event['event_time'] = format_event_time(event.get('event_time'))
        print(f"Upcoming events count: {len(upcoming_events)}")
        return render_template('dashboard.html',
                               user=user_data,
                               donations=donations,
                               upcoming_events=upcoming_events)
    except mysql.connector.Error as err:
        print(f"Dashboard error: {err}")
        return render_template('error.html', error="Database error")
    finally:
        cursor.close()
        conn.close()


@app.route('/branches')
def branches():
    conn = get_db_connection("church_db")
    if not conn:
        return render_template('error.html',
                               error="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM branches")
        branches = cursor.fetchall()
        return render_template('branches.html', branches=branches)
    except mysql.connector.Error as err:
        print(f"Branches error: {err}")
        return render_template('error.html', error="Database error")
    finally:
        cursor.close()
        conn.close()


@app.route('/branch/<int:branch_id>')
def branch_detail(branch_id):
    conn = get_db_connection("church_db")
    if not conn:
        return render_template('error.html',
                               error="Database connection failed")

    cursor = conn.cursor(dictionary=True)

    try:
        # Get branch details
        cursor.execute("SELECT * FROM branches WHERE id = %s", (branch_id, ))
        branch = cursor.fetchone()

        if not branch:
            return redirect(url_for('branches'))

        # Get branch members
        # cursor.execute("SELECT * FROM members WHERE branch_id = %s", (branch_id,))
        # members = cursor.fetchall()

        # Get branch events
        cursor.execute(
            """
        SELECT * 
        FROM events 
        WHERE branch_id = %s
        ORDER BY event_date ASC
        """, (branch_id, ))
        events_data = cursor.fetchall()

        # Format events
        for event in events_data:
            event['event_date'] = format_event_date(event.get('event_date'))
            event['event_time'] = format_event_time(event.get('event_time'))

        return render_template('branch_detail.html',
                               branch=branch,
                               events=events_data)
    except mysql.connector.Error as err:
        print(f"Branch detail error: {err}")
        return render_template('error.html', error="Database error")
    finally:
        cursor.close()
        conn.close()


@app.route('/events')
def events():
    conn = get_db_connection("church_db")
    if not conn:
        return render_template('error.html',
                               error="Database connection failed")

    cursor = conn.cursor(dictionary=True)

    try:
        # Get all events
        cursor.execute("""
        SELECT events.*, branches.name AS branch_name 
        FROM events 
        JOIN branches ON events.branch_id = branches.id
        ORDER BY event_date ASC, event_time ASC
        """)
        events_data = cursor.fetchall()

        # Format events
        for event in events_data:
            event['event_date'] = format_event_date(event.get('event_date'))
            event['event_time'] = format_event_time(event.get('event_time'))

        return render_template('events.html', events=events_data)
    except mysql.connector.Error as err:
        print(f"Events error: {err}")
        return render_template('error.html', error="Database error")
    finally:
        cursor.close()
        conn.close()


@app.route('/event/<int:event_id>')
def event_detail(event_id):
    conn = get_db_connection("church_db")
    if not conn:
        return render_template('error.html',
                               error="Database connection failed")

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
        SELECT events.*, branches.name AS branch_name, branches.address AS branch_address
        FROM events 
        JOIN branches ON events.branch_id = branches.id
        WHERE events.id = %s
        """, (event_id, ))
        event = cursor.fetchone()

        if not event:
            return redirect(url_for('events'))

        # Format date and time
        event['event_date'] = format_event_date(event.get('event_date'))
        event['event_time'] = format_event_time(event.get('event_time'))

        return render_template('event_detail.html', event=event)
    except mysql.connector.Error as err:
        print(f"Event detail error: {err}")
        return render_template('error.html', error="Database error")
    finally:
        cursor.close()
        conn.close()


@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        amount = float(request.form['amount'])
        payment_method = request.form['payment_method']
        purpose = request.form['purpose']

        # Generate transaction ID
        transaction_id = f"CHURCH{datetime.now().strftime('%Y%m%d%H%M%S')}"

        conn = get_db_connection("church_db")
        if not conn:
            return render_template('donate.html',
                                   error="Database connection failed")

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
            INSERT INTO donations 
            (user_id, amount, payment_method, purpose, transaction_id)
            VALUES (%s, %s, %s, %s, %s)
            """, (user_id, amount, payment_method, purpose, transaction_id))
            conn.commit()
            return redirect(url_for('donation_success'))
        except mysql.connector.Error as err:
            conn.rollback()
            print(f"Donation error: {err}")
            return render_template('donate.html', error="Donation failed")
        finally:
            cursor.close()
            conn.close()

    return render_template('donate.html')


@app.route('/donation/success')
def donation_success():
    return render_template('donation_success.html')


@app.route('/donations')
def user_donations():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection("church_db")
    if not conn:
        return render_template('error.html',
                               error="Database connection failed")

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
        SELECT * FROM donations 
        WHERE user_id = %s
        ORDER BY donation_date DESC
        """, (user_id, ))
        donations = cursor.fetchall()

        # Format donation dates
        for donation in donations:
            donation['donation_date'] = donation['donation_date'].strftime(
                '%Y-%m-%d %H:%M') if donation.get('donation_date') else ""

        return render_template('user_donations.html', donations=donations)
    except mysql.connector.Error as err:
        print(f"User donations error: {err}")
        return render_template('error.html', error="Database error")
    finally:
        cursor.close()
        conn.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection("church_db")
        if not conn:
            return render_template('login.html',
                                   error="Database connection failed")

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email, ))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['user_email'] = user['email']
                return redirect(url_for('dashboard'))

            return render_template('login.html',
                                   error="Invalid email or password")
        except mysql.connector.Error as err:
            print(f"Login error: {err}")
            return render_template('login.html', error="Database error")
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')

        # Validate required fields
        if not full_name or not email or not password:
            return render_template('signup.html',
                                   error="All fields are required")

        # Check password match
        if password != confirm_password:
            return render_template('signup.html',
                                   error="Passwords do not match")

        # Hash the password
        hashed_password = generate_password_hash(password)

        conn = get_db_connection("church_db")
        if not conn:
            return render_template('signup.html',
                                   error="Database connection failed")

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
            INSERT INTO users (full_name, email, password, phone, address)
            VALUES (%s, %s, %s, %s, %s)
            """, (full_name, email, hashed_password, phone, address))
            conn.commit()

            # Get new user ID
            user_id = cursor.lastrowid

            # Fetch new user data
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id, ))
            new_user = cursor.fetchone()

            session['user_id'] = new_user['id']
            session['user_name'] = new_user['full_name']
            session['user_email'] = new_user['email']

            return redirect(url_for('dashboard'))
        except mysql.connector.Error as err:
            conn.rollback()
            if err.errno == 1062:  # Duplicate entry error
                error = "Email already registered"
            else:
                error = f"Registration failed: {err}"
            print(f"Signup error: {err}")
            return render_template('signup.html', error=error)
        finally:
            cursor.close()
            conn.close()

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# ---------------------- Error Handlers --------------------------- #


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# ---------------------- Main Program ----------------------------- #

if __name__ == '__main__':
    app.run(debug=True)
