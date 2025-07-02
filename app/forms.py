from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class SignupForm(FlaskForm):
    """Form for users to create new account"""
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=25)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )
    submit = SubmitField('Sign Up')

    # The validation for existing username is removed because
    # the Auth service will handle it.

class LoginForm(FlaskForm):
    """Form for users to login"""
    username = StringField(
        'Username',
        validators=[DataRequired()]
    )
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
