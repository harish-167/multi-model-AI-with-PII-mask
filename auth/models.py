# auth_service/models.py

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime

# Instantiate the extensions here
db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    """User model for storing user details."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, username, password):
        self.username = username
        # Use the bcrypt instance to hash the password
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.registered_on = datetime.datetime.now()

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
