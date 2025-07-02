import os
import requests
import jwt
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, flash, session, g
)
from dotenv import load_dotenv
import google.generativeai as genai

from forms import LoginForm, SignupForm

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATIONS ---
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL') # e.g., http://auth-service:5001
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
JWT_SECRET_KEY = os.environ.get('AUTH_SECRET_KEY') # Must be the same as in Auth Service

# --- START OF DIAGNOSTIC CODE ---
print("--- FLASK APP DEBUGGING ---", flush=True)
print(f"Value of AUTH_SERVICE_URL is: '{AUTH_SERVICE_URL}'", flush=True)
print(f"Type of AUTH_SERVICE_URL is: {type(AUTH_SERVICE_URL)}", flush=True)
print("--- END OF DEBUGGING ---", flush=True)
# --- END OF DIAGNOSTIC CODE ---

# --- GOOGLE GENERATIVE AI CONFIGURATION ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


# --- AUTHENTICATION DECORATOR & HELPERS ---

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('jwt_token')
        if not token:
            flash("Please log in to access this page.", "info")
            return redirect(url_for('login'))
        try:
            # Decode the token. The audience and issuer are not set, so we don't verify them.
            # In a production system, you'd want to verify these.
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            # Store user info in Flask's g object for this request
            g.current_user = {'id': data['sub'], 'username': data['username']}
        except jwt.ExpiredSignatureError:
            flash("Your session has expired. Please log in again.", "warning")
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            flash("Invalid token. Please log in again.", "danger")
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

# This makes 'current_user' available to all templates
@app.context_processor
def inject_user():
    return dict(current_user=g.get('current_user', None))


# --- UI & AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.get('current_user'):
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            # Internal API call to the Auth Service
            api_response = requests.post(
                f"{AUTH_SERVICE_URL}/api/login",
                json={'username': form.username.data, 'password': form.password.data}
            )
            api_response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            response_data = api_response.json()
            session['jwt_token'] = response_data.get('token')
            flash('Login successful!', 'success')
            return redirect(url_for('index'))

        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 401:
                flash('Invalid username or password.', 'danger')
            else:
                flash('An error occurred. Please try again later.', 'danger')
        except requests.exceptions.RequestException:
            flash('Could not connect to the authentication service.', 'danger')

    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if g.get('current_user'):
        return redirect(url_for('index'))

    form = SignupForm()
    if form.validate_on_submit():
        try:
            api_response = requests.post(
                f"{AUTH_SERVICE_URL}/api/register",
                json={'username': form.username.data, 'password': form.password.data}
            )
            api_response.raise_for_status()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))

        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 409: # Conflict
                flash(err.response.json().get('message', 'Username already exists.'), 'danger')
            else:
                flash('An error occurred during registration.', 'danger')
        except requests.exceptions.RequestException:
            flash('Could not connect to the authentication service.', 'danger')

    return render_template('signup.html', form=form)


@app.route('/logout')
def logout():
    session.pop('jwt_token', None) # Clear the token from the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# --- MAIN APPLICATION ROUTES ---

@app.route('/')
@token_required
def index():
    return render_template('index.html')


@app.route('/generate_text', methods=['POST'])
@token_required
def generate_text():
    data = request.json
    user_prompt = data.get('prompt')
    conversation_history = data.get('history', [])
    if not user_prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        chat = model.start_chat(history=conversation_history)
        response = chat.send_message(user_prompt)
        generated_content = response.text
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

# This check ensures that 'g.current_user' is set before every request if a token exists
@app.before_request
def load_logged_in_user():
    token = session.get('jwt_token')
    g.current_user = None
    if token:
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            g.current_user = {'id': data['sub'], 'username': data['username']}
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            # Token is invalid or expired, g.current_user remains None
            session.pop('jwt_token', None)


if __name__ == '__main__':
    # The port is 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
