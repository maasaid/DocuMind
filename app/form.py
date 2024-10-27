from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .model import User
from .db import create_connection

class RegistrationForm(FlaskForm):
    user_name = StringField('user_name', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
 
    def validate_user_name(self, user_name):
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = %s", (user_name.data,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        

        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')

    def validate_email(self, email):
        connection = create_connection()
        cursor=connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email.data,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user:
            raise ValidationError('Email is already registered. Please choose a different one.')
        
 
        