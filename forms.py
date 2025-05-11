
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from datetime import datetime

from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8)
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), EqualTo('password')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken. Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('This email is already registered. Please use a different email.')

class BookingForm(FlaskForm):
    hall_id = SelectField('Hall', coerce=int, validators=[DataRequired()])
    event_name = StringField('Event Name', validators=[DataRequired(), Length(max=100)])
    event_description = TextAreaField('Event Description', validators=[Optional(), Length(max=500)])
    start_time = DateTimeField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeField('End Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    attendees = IntegerField('Number of Attendees', validators=[Optional(), NumberRange(min=1)])
    submit = SubmitField('Request Booking')

    def validate_end_time(self, end_time):
        if end_time.data <= self.start_time.data:
            raise ValidationError('End time must be after start time')
        
        if self.start_time.data < datetime.now():
            raise ValidationError('Booking must be for a future date')

class HallForm(FlaskForm):
    name = StringField('Hall Name', validators=[DataRequired(), Length(max=100)])
    hall_type = SelectField('Hall Type', choices=[('seminar', 'Seminar Hall'), ('computer', 'Computer Center')], validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[Optional()])
    features = TextAreaField('Features', validators=[Optional()])
    image_url = StringField('Image URL', validators=[Optional()])
    is_active = BooleanField('Active')
    submit = SubmitField('Save Hall')

class BookingAdminForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Admin Notes', validators=[Optional()])
    submit = SubmitField('Update Booking')
