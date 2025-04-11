import mysql.connector
from datetime import datetime, timedelta

from docutils.nodes import entry
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from dotenv import load_dotenv
import openai
import os
import bcrypt
import re

load_dotenv()
#Set OpenAI API KEY
openai.api_key=os.getenv("OPENAI_API_KEY")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="gym_tracker"
    )

def get_llm_response(prompt):
    """
    Interact with OPENAI API to generate feedback.
    """

    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a fitness coach providing constructive feedback"},
            {"role": "user", "content": prompt}
        ]
    )

    return response

class StartMenuScreen(Screen):
    """Start Menu Screen with Register and Login options."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #layout=BoxLayout(orientation='vertical', spacing=10, padding=[20,50,20,50])
        layout = FloatLayout()

        #Add background image
        background = Image(source='static/images/home.JPG', allow_stretch=True, keep_ratio=False)
        layout.add_widget(background)

        #Forground Content
        menu_layout = BoxLayout(orientation="vertical", spacing=10, padding=[20,50,20,50])
        menu_layout.size_hint = (0.8, 0.6)
        menu_layout.pos_hint={'center_x':0.5,'center_y':0.5}

        menu_layout.add_widget(Label(text="Welcome to Gym Tracker!", font_size='24sp', size_hint=(1, 0.2), color=(1, 0.84, 0, 1)))

        #Register Button
        register_button=Button(text="Register", size_hint=(0.8, 0.1), pos_hint={'center_x':0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1))
        register_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'register'))
        menu_layout.add_widget(register_button)

        # Login Buttons
        login_button = Button(text="Login", size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1))
        login_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        menu_layout.add_widget(login_button)

        #Add the menu to layout
        layout.add_widget(menu_layout)

        self.add_widget(layout)

class RegisterScreen(Screen):
    """Registration Screen"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        #Add Backround image
        background = Image(source='static/images/register.jpg', allow_stretch=True, keep_ratio=False)
        layout.add_widget(background)

        menu_layout=BoxLayout(orientation='vertical', spacing=10, padding=[20,50,20,50])
        #menu_layout.size_hint=(0.8, 0.6)
        #menu_layout.pos_hint={'center_x':0.5,'center_y':0.5}

        #Registration inputs
        self.name_input=TextInput(hint_text="Name", multiline=False, size_hint=(1,0.5))
        self.email_input=TextInput(hint_text="Email", multiline=False, size_hint=(1,0.5))
        self.password_input=TextInput(hint_text="password", multiline=False, password=True, size_hint=(1,0.5))
        self.confirm_password_input=TextInput(hint_text="Confirm Password", multiline=False, password=True, size_hint=(1,0.5))
        self.age_input=TextInput(hint_text="Age (in years)", multiline=False, input_filter="int", size_hint=(1,0.5))
        self.feet_input=TextInput(hint_text="Height (feet)", multiline=False, input_filter="int", size_hint=(1,0.5))
        self.inches_input=TextInput(hint_text="Height (inches)", multiline=False, input_filter="int", size_hint=(1,0.5))
        self.weight_input=TextInput(hint_text="Weight (lbs)", multiline=False, input_filter="float", size_hint=(1, 0.5))
        self.goal_input=TextInput(hint_text="Goal", multiline=False, size_hint=(1, 0.5))

        #Add widgets to layout
        menu_layout.add_widget(self.name_input)
        menu_layout.add_widget(self.email_input)
        menu_layout.add_widget(self.password_input)
        menu_layout.add_widget(self.confirm_password_input)
        menu_layout.add_widget(self.age_input)
        menu_layout.add_widget(self.feet_input)
        menu_layout.add_widget(self.inches_input)
        menu_layout.add_widget(self.weight_input)
        menu_layout.add_widget(self.goal_input)

        #Submit Button
        submit_button=Button(text="Submit", size_hint=(0.8, 0.5), pos_hint={'center_x':0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1))
        submit_button.bind(on_press=self.register_user)
        menu_layout.add_widget(submit_button)

        #Back Button
        back_button = Button(text="Return to Start Menu", size_hint=(0.8, 0.5), pos_hint={'center_x':0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1))
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'start_menu'))
        menu_layout.add_widget(back_button)

        #Feedback Label
        self.feedback_label=Label(text="", size=(1, 0.2), color=(1, 0.84, 0, 1))
        menu_layout.add_widget(self.feedback_label)

        #Add the menu to the layout
        layout.add_widget(menu_layout)

        self.add_widget(layout)

    def register_user(self, instance):
        """Register a new user"""
        name=self.name_input.text.strip()
        email=self.email_input.text.strip()
        password=self.password_input.text.strip()
        confirm_password=self.confirm_password_input.text.strip()
        age=int(self.age_input.text.strip())
        feet=int(self.feet_input.text.strip())
        inches=int(self.inches_input.text.strip())
        weight=float(self.weight_input.text.strip())
        goal=self.goal_input.text.strip()

        if not name or not email or not password or not confirm_password or not age or not feet or not inches or not weight or not goal:
            self.feedback_label.text = "Please fill in all data fields."
            return

        #Validate Email
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            self.feedback_label.text = "Invalid email address."
            return

        #Validate Password
        if not self.validate_password(password):
            self.feedback_label.text =(
                "Password must be at least 8 characters,"
                "Include an uppercase letter, a lower case letter, a nubmer, and a special character."
            )
            return

        #Check if passwords match
        if password != confirm_password:
            self.feedback_label.text="Passwords do not match."
            return

        #Hash the password
        hashed_password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            #Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))

            if cursor.fetchone():
                self.feedback_label.text = "Email already registered."
                return

            #Inser into database
            cursor.execute(
                """
                INSERT INTO users (name, email, age, feet, inches, weight, goal, password)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (name, email, age, feet, inches, weight, goal, hashed_password)
            )
            conn.commit()
            self.feedback_label.text = "Registration successful! Please Login"
            self.manager.current = 'start_menu'

        except mysql.connector.Error as err:
            self.feedback_label.text = f"Error:{err}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    @staticmethod
    def validate_password(password):
        """Validate password"""
        if(
            re.search(r"[A-Z]", password) and
            re.search(r"[a-z]", password) and
            re.search(r"\d", password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
        ):
            return True
        return False

class LoginScreen(Screen):
    """Login Screen"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        #Add background image
        background = Image(source='static/images/login.JPG', allow_stretch=True, keep_ratio=False)

        layout.add_widget(background)

        menu_layout=BoxLayout(orientation="vertical", spacing=10, padding=[20,50,20,50])

        #Input fields
        self.email_input=TextInput(hint_text="Email", multiline=False, size_hint=(1,0.1), pos_hint={'center_x':0.5})
        self.password_input=TextInput(hint_text="password", multiline=False, password=True, size_hint=(1, 0.1), pos_hint={'center_x':0.5})

        menu_layout.add_widget(self.email_input)
        menu_layout.add_widget(self.password_input)

        #Submit Button
        login_button = Button(text="Log In", size_hint=(0.8, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1))
        login_button.bind(on_press=self.login_user)
        menu_layout.add_widget(login_button)

        #Back Button
        back_button = Button(text="Return to Start Menu", size_hint=(0.8, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1))
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'start_menu'))
        menu_layout.add_widget(back_button)

        #Feedback Label
        self.feedback_label=Label(text="", size_hint=(1, 0.2), color=(1, 0.84, 0, 1))
        menu_layout.add_widget(self.feedback_label)

        #Add menu to background image
        layout.add_widget(menu_layout)

        self.add_widget(layout)
    def login_user(self, instance):
        """Verify user credentials and log in"""
        email=self.email_input.text.strip()
        password=self.password_input.text.strip()

        if not email or not password:
            self.feedback_label.text = "Pleae fill in all fields."
            return
        try:
            conn=get_db_connection()
            cursor=conn.cursor(dictionary=True)

            #Check if email exists
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if not user:
                self.feedback_label.text = "Invalid email or password"
                return

            #Verify Password
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                self.feedback_label.text = "Login Successful!"
                self.manager.user_id=user['id']
                self.manager.user_goal=user['goal']
                self.manager.current='main_menu'
            else:
                self.feedback_label.text = "Invalid email or password"
        except mysql.connector.Error as err:
            self.feedback_label.text = f"Error: {err}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        background = Image(source='static/images/main_menu.JPG', allow_stretch=True, keep_ratio=False)
        layout.add_widget(background)

        menu_layout = BoxLayout(orientation='vertical', spacing=10, padding=[20, 50, 20, 50])  # Padding: [left, top, right, bottom]

        # Add Welcome Label
        menu_layout.add_widget(Label(text="Welcome to GymTracker!", font_size='24sp', color=(1, 0.84,0,1), size_hint=(1, 0.2)))

        # Add Buttons for navigation
        menu_layout.add_widget(Button(text="Log a Workout", size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1), on_press=self.navigate_to_log_workout))
        menu_layout.add_widget(Button(text="View Weekly Progress and Feedback", size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1), on_press=self.navigate_to_progress))
        menu_layout.add_widget(Button(text="Set or Update Fitness Goal", size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1), on_press=self.navigate_to_update_goal))
        menu_layout.add_widget(Button(text="View Past Workouts", size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1), on_press=self.navigate_to_history))
        menu_layout.add_widget(Button(text="Exit", size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1), on_press=self.exit_app))

        layout.add_widget(menu_layout)

        self.add_widget(layout)

    def navigate_to_log_workout(self, instance):
        self.manager.current = 'log_workout'

    def navigate_to_progress(self, instance):
        self.manager.current = 'progress'

    def navigate_to_update_goal(self, instance):
        self.manager.current = 'update_goal'

    def navigate_to_history(self, instance):
        self.manager.current = 'history'

    def exit_app(self, instance):
        App.get_running_app().stop()

class LogWorkoutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        background = Image(source='static/images/log_workout.JPG', allow_stretch=True, keep_ratio=False)
        layout.add_widget(background)

        menu_layout = BoxLayout(orientation='vertical', spacing=10, padding=[20, 50, 20, 50])

        # Label for the screen title
        menu_layout.add_widget(Label(text='Log Workout', font_size='24sp', size_hint=(1, 0.2), color=(1, 0.84, 0, 1)))  # Gold

        # Text input for Exercise Name
        self.exercise_input = TextInput(hint_text="Exercise Name", multiline=False, size_hint = (1, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1))
        menu_layout.add_widget(self.exercise_input)

        # Text input for sets
        self.sets_input = TextInput(hint_text="Number of sets", multiline=False, input_filter='int', size_hint = (1, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1))
        menu_layout.add_widget(self.sets_input)

        # Text input for reps
        self.reps_input = TextInput(hint_text="Number of reps", multiline=False, input_filter='int', size_hint = (1, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1))
        menu_layout.add_widget(self.reps_input)

        # Text input for Intensity
        self.intensity_input = TextInput(hint_text="Intensity (e.g., Low, Medium, High)", multiline=False, size_hint = (1, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1))
        menu_layout.add_widget(self.intensity_input)

        # Submit button
        submit_button = Button(text="Submit Workout", size_hint=(1, 0.2), background_color=(0, 0, 0, 1), color=(1, 0.84, 0, 1))
        submit_button.bind(on_press=lambda instance: self.submit_workout(self.manager.user_id))
        menu_layout.add_widget(submit_button)

        #FeedBack Label
        self.feedback_label=Label(text="",size_hint=(1, 0.2), color=(1, 0.84, 0, 1))
        menu_layout.add_widget(self.feedback_label)

        # Back to main menu button
        back_button = Button(text="Return to Main Menu", size_hint=(1, 0.2), background_color=(0, 0, 0, 1), color=(1, 0.84, 0, 1))
        back_button.bind(on_press=self.navigate_to_main_menu)
        menu_layout.add_widget(back_button)

        layout.add_widget(menu_layout)

        self.add_widget(layout)

    def submit_workout(self, user_id):
        """
        Collect User Input and simulate saving the workout.
        Provide feedback based on user input.
        """
        exercise = self.exercise_input.text.strip()
        sets = self.sets_input.text.strip()
        reps = self.reps_input.text.strip()
        intensity = self.intensity_input.text.strip()
        workout_date=datetime.now().strftime('%Y-%m-%d')

        if exercise and sets.isdigit() and reps.isdigit() and intensity:
            try:
                #Save to database
                connection=get_db_connection()
                cursor=connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO workouts (user_id, date, exercise, sets, reps, intensity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, workout_date, exercise, sets, reps, intensity)
                )
                connection.commit()
                self.feedback_label.text="Workout logged successfully!"

                # Simulate successful workout logging
                self.feedback_label.text = f"Workout Logged: {exercise}, {sets} sets, {reps} reps, Intensity: {intensity}"
                self.clear_inputs()

            except mysql.connector.Error as err:
                self.feedback_label.text=f"Error: {err}"

            finally:
                if cursor:
                    cursor.close()
                if connection:
                    connection.close()
            self.clear_inputs()
        else:
            self.feedback_label.text="Please fill out all fields correctly!"

    def clear_inputs(self):
        """
        Clear all input fields after submission.
        """
        self.exercise_input.text = ""
        self.sets_input.text = ""
        self.reps_input.text = ""
        self.intensity_input.text = ""

    def navigate_to_main_menu(self, instance):
        """
        Navigate to Main Menu.
        """
        self.manager.current = 'main_menu'

class ProgressScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Use FloatLayout for the entire screen
        layout = FloatLayout()

        # Add background image
        background = Image(source='static/images/view_progress.JPG', allow_stretch=True, keep_ratio=False)
        layout.add_widget(background)

        # Semi-transparent background for the content area
        content_background = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=[20, 50, 20, 50],
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        with content_background.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0, 0, 0, 0.8)  # Black color with 50% transparency
            self.bg_rect = Rectangle(size=content_background.size, pos=content_background.pos)

        # Bind the rectangle size and position to the layout
        content_background.bind(size=lambda instance, value: setattr(self.bg_rect, 'size', value))
        content_background.bind(pos=lambda instance, value: setattr(self.bg_rect, 'pos', value))

        # Screen title
        content_background.add_widget(Label(text='Weekly Progress and Feedback', font_size='24sp', size_hint=(1, 0.2), color=(1, 0.84, 0, 1)))

        # Scrollable Feedback Display
        scroll_view = ScrollView(size_hint=(1, 0.6))
        self.feedback_label = Label(
            text="",
            size_hint_y=None,  # Allow dynamic height
            color=(1, 0.84, 0, 1),
            font_size='16sp',
            text_size=(Window.width * 0.8, None),  # Wrap text
            halign="left",
            valign="top",
        )
        self.feedback_label.bind(texture_size=self._update_label_height)
        scroll_view.add_widget(self.feedback_label)
        content_background.add_widget(scroll_view)

        # Back button
        back_button = Button(text="Return to Main Menu", size_hint=(1, 0.2))
        back_button.bind(on_press=self.navigate_to_main_menu)
        content_background.add_widget(back_button)

        layout.add_widget(content_background)
        self.add_widget(layout)

    def _update_label_height(self, instance, value):
        """Dynamically adjust label height to fit content."""
        instance.height = instance.texture_size[1]

    def on_enter(self):
        """Fetch data when entering the screen."""
        user_id = self.manager.user_id
        user_goal = self.manager.user_goal

        if not user_id or not user_goal:
            self.feedback_label.text = "User ID or goal is not set."
            return

        self.fetch_feedback(user_id, user_goal)

    def fetch_feedback(self, user_id, user_goal):
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            cursor.execute(
                """
                SELECT * FROM workouts WHERE user_id = %s AND date BETWEEN %s and %s
                """,
                (user_id, start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d'))
            )
            workouts = cursor.fetchall()

            if not workouts:
                self.feedback_label.text = "No workouts logged this week!"
                return

            # Generate feedback using OpenAI
            workouts_summary = "\n".join(
                f"Exercise: {w['exercise']}, Sets: {w['sets']}, Reps: {w['reps']}, Intensity: {w['intensity']}"
                for w in workouts
            )
            prompt = (
                f"Based on the following workout log, provide constructive feedback for the user:\n\n"
                f"Goals: {user_goal}\n\n"
                f"Weekly Workout Log:\n{workouts_summary}\n\n"
                f"Focus on encouragement, areas of improvements, and suggestions for next week."
            )

            response = get_llm_response(prompt)
            feedback = response['choices'][0]['message']['content']
            self.feedback_label.text = feedback
        except mysql.connector.Error as err:
            self.feedback_label.text = f"Database Error: {err}"
        except Exception as e:
            self.feedback_label.text = f"Unexpected Error: {e}"
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def navigate_to_main_menu(self, instance):
        """Navigate back to Main Menu."""
        self.manager.current = 'main_menu'


class UpdateGoalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout=BoxLayout(orientation='vertical', spacing=10, padding=[20,50,20,50])

        #Titel Label
        layout.add_widget(Label(text="Update Fitness Goal", font_size='24sp', size_hint=(1, 0.2), color=(1, 0.84, 0, 1)))

        #Input for new goal
        self.goal_input=TextInput(hint_text="Enter new Fitness Goal", multiline=False, size_hint=(1, 0.2))
        layout.add_widget(self.goal_input)

        #Feedback Label
        self.feedback_label=Label(text="", size_hint=(1,0.2), color=(1, 0.84, 0, 1))
        layout.add_widget(self.feedback_label)

        #Submit Button
        submit_button=Button(text="Update Goal", size_hint=(0.8, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1))
        submit_button.bind(on_press=lambda instance: self.update_goal(self.manager.user_id))
        layout.add_widget(submit_button)

        #Back to Main Menu Button
        back_button=Button(text="Return to Main Menu", size_hint=(0.8, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 0.84, 0, 1), color=(0, 0, 0, 1))
        back_button.bind(on_press=self.navigate_to_main_menu)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def on_enter(self):
        """
        Called when the Screen is entered. You could prepulate the goal field here,
        but it depends on your requirements
        """

        self.goal_input.text=""
        self.feedback_label.text=""

    def update_goal(self, user_id):
        """
        Update the user's fitness goal in the database
        """

        new_goal=self.goal_input.text.strip()

        if not new_goal:
            self.feedback_label.text="Please enter a new goal"
            return

        try:
            connection=get_db_connection()
            cursor=connection.cursor()

            #Update the goal in the database
            query="""
            UPDATE users
            SET goal = %s
            WHERE id = %s
            """
            cursor.execute(query, (new_goal,user_id))
            connection.commit()

            self.feedback_label.text="Fitness Goal updated successfully!"

        except mysql.connector.Error as err:
            self.feedback_label.text=f"Error: {err}"

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def navigate_to_main_menu(self, instance):
        """
        Navigate back to Main Menu
        """

        self.manager.current='main_menu'

class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout=BoxLayout(orientation='vertical', spacing=10, padding=[20,50,20,50])

        #Title Label
        layout.add_widget(Label(text="Workout History", size_hint=(1, 0.2), color=(1, 0.84, 0, 1)))

        #Scrollable workout history display
        self.scroll_view=ScrollView(size_hint=(1, 0.7))
        self.history_label=Label(
            text="",
            size_hint=(1, None),
            color=(1, 0.84, 0, 1),
            font_size='16sp',
            text_size=(Window.width*0.9, None),
            halign="left",
            valign="top",
        )

        self.history_label.bind(texture_size=self._update_label_height)
        self.scroll_view.add_widget(self.history_label)
        layout.add_widget(self.scroll_view)

        #Back Button
        back_button=Button(text="Return to Main Menu", size_hint=(0.8, 0.2), pos_hint={'center_x':0.5}, background_color=(1, 0.84, 0, 1),color=(0, 0, 0, 1))
        back_button.bind(on_press=self.navigate_to_main_menu)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def _update_label_height(self, instance, value):
        """Update height of the label based on its content"""
        instance.height = instance.texture_size[1]

    def on_enter(self):
        user_id=self.manager.user_id
        self.fetch_workout_history(user_id)

    def fetch_workout_history(self, user_id):
        try:
            connection=get_db_connection()
            cursor=connection.cursor(dictionary=True)

            #Check if the user has any workout history
            cursor.execute("SELECT COUNT(*) as count FROM workouts WHERE user_id = %s", (user_id,))
            result=cursor.fetchone()

            if result['count']==0:
                self.history_label.text="No workout history available. Please log a workout first."
                return

            #Fetch Workout History
            cursor.execute("""
            SELECT date, exercise, sets, reps, intensity
            FROM workouts
            WHERE user_id=%s
            ORDER BY date DESC
            """, (user_id,))
            workout_history=cursor.fetchall()

            #Format the workout history for display
            history_text="\n\n".join(
                f"Date: {entry['date']}\nExercise: {entry['exercise']}\nSets: {entry['sets']}\nReps: {entry['reps']}\nIntensity: {entry['intensity']}"
                for entry in workout_history
            )

            self.history_label.text=history_text

        except mysql.connector.Error as err:
            self.history_label.text=f"Error: {err}"

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def navigate_to_main_menu(self, instance):
        """Navigate back to Main Menu"""
        self.manager.current='main_menu'

# Main App
class GymApp(App):
    def build(self):
        sm = ScreenManager()
        sm.user_id = None
        sm.user_goal = None

        # Add Screens to the Screen Manager
        sm.add_widget(StartMenuScreen(name='start_menu'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(LogWorkoutScreen(name='log_workout'))
        sm.add_widget(ProgressScreen(name='progress'))
        sm.add_widget(UpdateGoalScreen(name='update_goal'))
        sm.add_widget(HistoryScreen(name='history'))

        return sm

if __name__ == '__main__':
    GymApp().run()