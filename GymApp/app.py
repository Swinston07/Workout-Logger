from platform import android_ver

from flask import Flask, request, render_template, redirect, url_for, flash, get_flashed_messages
import mysql.connector
import re
import bcrypt
from datetime import datetime, timedelta, date
import os
import openai
from dotenv import load_dotenv
import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'y0uc4nth4v31tmyb01')

#Database conneciton function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user = "root",
        password = "",
        database = "gym_tracker"
    )

def validate_password(password):
    """
        Validates a password to ensure it contains:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one special character
        - At least one number
        - Minimum length of 8 characters
        """

    if (len(password)>=8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):
        return True
    return False

def hash_password(password):
    """
    Hashes a password using bcrypt.
    """

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def verify_password(input_password, hashed_password):
    """
    Verifies the input password against the stored hashed password.
    """
    return bcrypt.checkpw(input_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_llm_response(prompt):
    """
    Get a response from the OpenAI GPT model.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a fitness coach providing constructive feedback."},
            {"role": "user", "content": prompt}
        ]
    )
    return response


def save_weekly_workout_log(user_id, workouts):
    """
    Save or update the user's weekly workout log in the database.
    """
    # Establish database connection
    connection = get_db_connection()
    if not connection:
        flash("Failed to connect to the database. Please try again later.")
        return

    # Ensure workouts are JSON-serializable
    for workout in workouts:
        if isinstance(workout.get('date'), datetime):
            workout['date'] = workout['date'].strftime('%Y-%m-%d')

    try:
        # Serialize workouts to JSON
        workout_log = json.dumps(workouts)

        # Determine the start and end of the current week
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        query = """
        INSERT INTO weeklyworkouts (user_id, week_start, week_end, workout_log)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE workout_log = VALUES(workout_log)
        """

        with connection.cursor() as cursor:
            # Execute query
            cursor.execute(query, (
                user_id,
                start_of_week.strftime('%Y-%m-%d'),
                end_of_week.strftime('%Y-%m-%d'),
                workout_log
            ))
            connection.commit()

        flash("Weekly workout log saved!")

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
    except Exception as e:
        flash(f"Unexpected error: {e}")
    finally:
        # Close connection
        connection.close()

#Route: Home Page
@app.route('/')
def home():
    """
    Displays the start menu for the Gym Tracker App.
    """
    return render_template('home.html')

@app.route('/main_menu/<int:user_id>', methods=['GET', 'POST'])
def main_menu(user_id):
    # Fetch user data from the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Retrieve user details
        cursor.execute("SELECT id, name, goal FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            flash("User not found. Please log in again.")
            return redirect(url_for('login_user'))

        # Render the main menu template
        return render_template('main_menu.html', user_data=user_data)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('login_user'))

    finally:
        cursor.close()
        conn.close()

@app.route('/register')
def register():
    """
    Redirects to the registration page.
    """
    return redirect(url_for('register_user'))

@app.route('/login')
def login():
    """
    Redirects to the login page.
    """
    return redirect(url_for('login_user'))

@app.route('/register_user', methods = ['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            age = int(request.form['age'])  # Convert to integer
            feet = int(request.form['feet'])  # Convert to integer
            inches = int(request.form['inches'])  # Convert to integer
            weight = float(request.form['weight'])  # Convert to float (e.g., 150.5)
            goal = request.form['goal']

            # Validate Password
            if not validate_password(password):
                flash("Invalid Password: min 8 characters, 1 uppercase, 1 lowercase, "
                      "1 special character, 1 number.")
                return render_template('register.html', age_range=range(15, 101))

            # Ensure passwords match
            if password != confirm_password:
                flash("Passwords do not match.")
                return render_template('register.html', age_range=range(15, 101))

            # Hash password
            hashed_password = hash_password(password)

            # Ensure hashed password is decoded to a string
            hashed_password = hashed_password.decode('utf-8') if isinstance(hashed_password, bytes) else hashed_password

            # Database connection
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                Flask("An account with this email already exists.")
                return render_template('register.html', age_range=range(15, 101))

            # Insert user into the database
            cursor.execute(
                """
                INSERT INTO users (name, email, age, feet, inches, weight, goal, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (name, email, age, feet, inches, weight, goal, hashed_password)
            )
            conn.commit()
            cursor.close()
            conn.close()

            flash("Registration successful! You can now log in.")
            return redirect(url_for('home'))  # Redirect to login page

        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            return render_template('register.html', age_range=range(15, 101))

        except ValueError:
            flash("Invalid input. Please ensure all fields are filled correctly.")
            return render_template('register.html', age_range=range(15, 101))

    # Pass age range to the template
    return render_template('register.html', age_range=range(15, 101))

@app.route('/login_user', methods = ['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        #Get from data
        email = request.form['email']
        password = request.form['password']

        #Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #Check if email address exists
        cursor.execute("SELECT * FROM users WHERE email = %s",(email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return "Invalid email or password."

        if not verify_password(password, user['password']):
            cursor.close()
            conn.close()
            return "Invalid email or password."

        #Successful login
        return redirect(url_for('main_menu', user_id=user['id']))

    #Render the login from the GET request
    return render_template('login.html')

@app.route('/logout')
def logout_user():
    flash("You have been logged out.")
    return redirect(url_for('login_user'))

@app.route('/log_workout/<int:user_id>', methods = ['GET', 'POST'])
def log_workout(user_id):
    if request.method == 'POST':
        #Get from data
        exercise = request.form['exercise']
        sets = request.form['sets']
        reps = request.form['reps']
        intensity = request.form['intensity']
        workout_date = datetime.now().strftime('%Y-%m-%d')

        #Connecto to database
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            #Insert workout into database
            cursor.execute(
                """
                INSERT INTO workouts (user_id, date, exercise, sets, reps, intensity)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, workout_date, exercise, sets, reps, intensity)
            )
            conn.commit()
            flash("Workout logged succesfully!")
            return redirect(url_for('main_menu', user_id=user_id))

        except mysql.connector.Error as err:
            flash(f"Database error: {err}")

        finally:
            cursor.close()
            conn.close()

    #Render the workout logging form for GET requests
    return render_template('log_workout.html', user_id=user_id)

@app.route('/track_progress/<int:user_id>', methods=['GET', 'POST'])
def track_progress(user_id):
    """
    Fetch the user's weekly workouts, save the log, and provide AI-generated feedback.
    If no workouts are logged, flash an error message and redirect to the main menu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if the user has any logged workouts
        query = "SELECT COUNT(*) as count FROM workouts WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if result['count'] == 0:
            flash("No workouts logged yet. Please log a workout first.")
            return redirect(url_for('main_menu', user_id=user_id))

        # Continue with the original logic
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Retrieve user's goal
        cursor.execute("SELECT goal FROM users WHERE id = %s", (user_id,))
        user_goal = cursor.fetchone()

        if not user_goal:
            flash("User goal not found. Please set a goal first.")
            return redirect(url_for('main_menu', user_id=user_id))

        # Retrieve workouts for the current week
        cursor.execute("""
            SELECT * FROM workouts
            WHERE user_id = %s AND date BETWEEN %s AND %s
        """, (user_id, start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')))
        workouts = cursor.fetchall()

        if not workouts:
            flash("No workouts logged for this week.")
            return redirect(url_for('main_menu', user_id=user_id))

        # Serialize date fields
        for workout in workouts:
            if isinstance(workout['date'], (datetime, date)):
                workout['date'] = workout['date'].strftime('%Y-%m-%d')

        # Save weekly workout log
        save_weekly_workout_log(user_id, workouts)

        # Generate feedback using OpenAI
        workout_log_summary = "\n".join(
            [f"Exercise: {workout['exercise']}, Sets: {workout['sets']}, Reps: {workout['reps']}"
             for workout in workouts]
        )

        prompt = (
            f"Based on the following workout log, provide constructive feedback for the user:\n\n"
            f"Goals: {user_goal['goal']}\n\n"
            f"Weekly Workout Log:\n{workout_log_summary}\n\n"
            f"Focus on encouragement, areas for improvement, and suggestions for next week."
        )
        response = get_llm_response(prompt)
        feedback = response['choices'][0]['message']['content']

        # Save feedback to the database
        cursor.execute("""
            INSERT INTO weeklyfeedback (user_id, week_start, week_end, feedback)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE feedback = VALUES(feedback)
        """, (
            user_id,
            start_of_week.strftime('%Y-%m-%d'),
            end_of_week.strftime('%Y-%m-%d'),
            feedback
        ))
        conn.commit()

        flash("Weekly progress tracked and feedback provided!")
        return render_template('progress_feedback.html', feedback=feedback, user_id=user_id)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('main_menu', user_id=user_id))
    finally:
        cursor.close()
        conn.close()

@app.route('/workout_history/<int:user_id>', methods=['GET'])
def display_workout_history(user_id):
    """
    Display the workout history for a specific user.
    If no workouts are logged, flash an error message and redirect to the main menu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if user has any workout history
        query = "SELECT COUNT(*) as count FROM workouts WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if result['count'] == 0:
            flash("No workout history available. Please log a workout first.")
            return redirect(url_for('main_menu', user_id=user_id))

        # Fetch workout history
        cursor.execute("""
            SELECT date, exercise, sets, reps
            FROM workouts
            WHERE user_id = %s
            ORDER BY date DESC
        """, (user_id,))
        workout_history = cursor.fetchall()

        return render_template('workout_history.html', workout_history=workout_history, user_id=user_id)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('main_menu', user_id=user_id))
    finally:
        cursor.close()
        conn.close()

@app.route('/update_goal/<int:user_id>', methods=['GET', 'POST'])
def update_fitness_goal(user_id):
    print(f"Accessed update_goal for user_id: {user_id}")  # Debugging
    connection = get_db_connection()
    if not connection:
        flash("Failed to connect to the database. Please try again later.")
        print("Database connection failed.")  # Debugging
        return redirect(url_for('home'))

    try:
        cursor = connection.cursor(dictionary=True)

        if request.method == 'POST':
            print("POST request received.")  # Debugging
            # Get the new goal from the form
            new_goal = request.form['new_goal']
            print(f"New goal: {new_goal}")  # Debugging

            # Update the fitness goal in the database
            query = """
            UPDATE users
            SET goal = %s
            WHERE id = %s
            """
            cursor.execute(query, (new_goal, user_id))
            connection.commit()

            flash("Fitness goal updated successfully!")
            return redirect(url_for('main_menu', user_id=user_id))

        else:
            print("GET request received.")  # Debugging
            # Fetch the current goal to display in the form
            query = "SELECT goal FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()

            if not user:
                flash("User not found.")
                print("User not found.")  # Debugging
                return redirect(url_for('home'))

            current_goal = user['goal']
            print(f"Current goal: {current_goal}")  # Debugging

        return render_template('update_goal.html', current_goal=current_goal, user_id=user_id)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        print(f"Database error: {err}")  # Debugging
        return redirect(url_for('home'))

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)