import os
import requests
import jwt
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, flash, session, g
)
from dotenv import load_dotenv

from forms import LoginForm, SignupForm

load_dotenv()

app = Flask(__name__)

# --- CONFIGURATIONS ---
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL')
PII_SERVICE_URL = os.environ.get('PII_SERVICE_URL')
JWT_SECRET_KEY = os.environ.get('AUTH_SECRET_KEY')

# --- NEW: Define the URLs for our AI worker services ---
AI_SERVICE_URLS = {
    'gemini': os.environ.get('GEMINI_SERVICE_URL')
    # In the future, you'll add more:
    # 'openai': os.environ.get('OPENAI_SERVICE_URL')
}

# --- START OF MISSING CODE (RESTORED) ---

# --- AUTHENTICATION DECORATOR & HELPERS ---

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('jwt_token')
        if not token:
            flash("Please log in to access this page.", "info")
            return redirect(url_for('login'))
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
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
            session.pop('jwt_token', None)

# --- END OF MISSING CODE ---


# --- UI & AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.get('current_user'):
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            api_response = requests.post(
                f"{AUTH_SERVICE_URL}/api/login",
                json={'username': form.username.data, 'password': form.password.data}
            )
            api_response.raise_for_status()
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
            if err.response.status_code == 409:
                flash(err.response.json().get('message', 'Username already exists.'), 'danger')
            else:
                flash('An error occurred during registration.', 'danger')
        except requests.exceptions.RequestException:
            flash('Could not connect to the authentication service.', 'danger')

    return render_template('signup.html', form=form)


@app.route('/logout')
def logout():
    session.pop('jwt_token', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# --- MAIN APPLICATION ROUTES ---

@app.route('/')
@token_required
def index():
    # Get the list of available models from our configuration
    available_models = list(AI_SERVICE_URLS.keys())
    # Pass this list to the template
    return render_template('index.html', models=available_models)


# This is the main router logic
@app.route('/generate_text', methods=['POST'])
@token_required
def generate_text():
    data = request.json
    user_prompt = data.get('prompt')
    conversation_history = data.get('history', [])
    model_choice = data.get('model', 'gemini')
    
    if not user_prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        # 1. Sanitize user input (INGRESS)
        pii_response_in = requests.post(f"{PII_SERVICE_URL}/api/mask-pii", json={'text': user_prompt})
        pii_response_in.raise_for_status()
        masked_prompt = pii_response_in.json().get('masked_text')

        # 2. Build the message list to send to the worker service
        messages_to_send = conversation_history
        messages_to_send.append({'role': 'user', 'parts': [{'text': masked_prompt}]})

        # 3. ROUTE: Choose the correct AI worker based on model_choice
        ai_worker_url = AI_SERVICE_URLS.get(model_choice)
        if not ai_worker_url:
            return jsonify({'error': f'Model "{model_choice}" is not supported.'}), 400
        
        # 4. Call the chosen AI worker service
        ai_response = requests.post(f"{ai_worker_url}/api/generate", json={'messages': messages_to_send})
        ai_response.raise_for_status()
        raw_ai_response = ai_response.json().get('response')

        # 5. Sanitize the AI's output (EGRESS)
        pii_response_out = requests.post(f"{PII_SERVICE_URL}/api/mask-pii", json={'text': raw_ai_response})
        pii_response_out.raise_for_status()
        masked_ai_response = pii_response_out.json().get('masked_text')

        # 6. Build the final, sanitized history
        updated_history = messages_to_send
        updated_history.append({'role': 'model', 'parts': [{'text': masked_ai_response}]})

        # 7. Return the sanitized data to the client
        return jsonify({
            'generated_text': masked_ai_response,
            'history': updated_history
        })

    except requests.exceptions.HTTPError as err:
        error_json = err.response.json()
        print(f"Downstream service error: {error_json.get('error', 'Unknown error')}")
        return jsonify({'error': f"An error occurred with a backend service: {error_json.get('error')}"}), 502
    except requests.exceptions.RequestException as e:
        print(f"Connection error to a downstream service: {e}")
        return jsonify({'error': 'Could not connect to a required backend service.'}), 503
    except Exception as e:
        print(f"An unexpected error occurred in app-service: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
