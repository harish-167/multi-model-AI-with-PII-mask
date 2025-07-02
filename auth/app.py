# auth_service/app.py

import os
import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import jwt

# Import the INSTANCES from models.py
# --- THIS IS THE LINE TO FIX ---
from models import db, bcrypt, User

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATIONS ---
app.config['SECRET_KEY'] = os.environ.get('AUTH_SECRET_KEY')

# Construct the PostgreSQL connection string from environment variables
db_user = os.environ.get('POSTGRES_USER')
db_password = os.environ.get('POSTGRES_PASSWORD')
db_host = os.environ.get('POSTGRES_HOST') # e.g., 'postgres-db' from docker-compose
db_name = os.environ.get('POSTGRES_DB')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- INITIALIZE EXTENSIONS ---
# Now, db and bcrypt are the imported instances, so init_app will work
db.init_app(app)
bcrypt.init_app(app)


# --- API ROUTES ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required.'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'That username is already taken.'}), 409

    try:
        new_user = User(username=data['username'], password=data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Account created successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Something went wrong during registration.', 'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required.'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user and user.check_password(data['password']):
        token_payload = {
            'sub': user.id,
            'username': user.username,
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        token = jwt.encode(
            token_payload,
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({'message': 'Login successful.', 'token': token}), 200
    else:
        return jsonify({'message': 'Invalid username or password.'}), 401


@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@app.cli.command("init-db")
def init_db_command():
    """Creates the database tables."""
    db.create_all()
    print("Initialized the database.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)
