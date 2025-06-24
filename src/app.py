import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import google.generativeai as genai

# Import our new components
from models import db, bcrypt, User
from forms import LoginForm, SignupForm

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATIONS ---
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
# For simplicity, we'll use SQLite for this example
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# --- INITIALIZE EXTENSIONS ---
db.init_app(app)
bcrypt.init_app(app)

# --- FLASK-LOGIN CONFIGURATION ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if user is not authenticated
login_manager.login_message_category = 'info'
login_manager.login_message = "Please log in to access this page."


@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in on every page load."""
    if user_id is not None:
        return User.query.get(int(user_id))
    return None

# --- GOOGLE GENERATIVE AI CONFIGURATION ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Using a more recent model


# --- ROUTE DEFINITIONS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = SignupForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# --- MAIN APPLICATION ROUTES ---

@app.route('/')
@login_required # Protect this route
def index():
    return render_template('index.html')


@app.route('/generate_text', methods=['POST'])
@login_required # Protect the API endpoint
def generate_text():
    data = request.json
    user_prompt = data.get('prompt')
    conversation_history = data.get('history', [])
    if not user_prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        # Reformat history for the API if necessary
        # The genai library expects a specific format.
        # The frontend sends a list of dicts: {'role': 'user'/'model', 'parts': [{'text': ...}]}
        # The library's `start_chat` history expects: {'role': 'user'/'model', 'parts': [...]}
        # Our current format is already correct.

        chat = model.start_chat(history=conversation_history)
        response = chat.send_message(user_prompt)
        generated_content = response.text

        # Convert the chat history to a JSON-serializable format to send back
        updated_history = [
            {'role': message.role, 'parts': [part.text for part in message.parts]}
            for message in chat.history
        ]

        return jsonify({
            'generated_text': generated_content,
            'history': updated_history
        })
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True, host='0.0.0.0', port=5000)