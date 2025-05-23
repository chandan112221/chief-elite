from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                    TextAreaField, SelectField, FloatField, HiddenField,
                    DateTimeField, IntegerField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
import re

# Login form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Registration form (if needed)
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Profile form
class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Address')
    submit = SubmitField('Update Profile')

# Password change form
class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

# Fund request form
class FundRequestForm(FlaskForm):
    amount = FloatField('Amount (BDT)', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', 
                                choices=[('bkash', 'Bkash'), ('nagad', 'Nagad'), ('rocket', 'Rocket')],
                                validators=[DataRequired()])
    transaction_id = StringField('Transaction ID', validators=[DataRequired(), Length(min=4, max=100)])
    submit = SubmitField('Submit Request')

# Comment form
class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Post Comment')

# Other order form
class OtherOrderForm(FlaskForm):
    order_type = SelectField('Service Type', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    field_data = HiddenField()  # Will store JSON data of custom fields
    submit = SubmitField('Place Order')

# Admin Forms
class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Full Name', validators=[Length(max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Address')
    password = PasswordField('Password (leave blank to keep unchanged)', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    is_active = BooleanField('Is Active')
    is_admin = BooleanField('Is Admin')
    role_id = SelectField('Role', coerce=int, choices=[], validators=[DataRequired()])
    balance = FloatField('Balance', default=0.0)
    submit = SubmitField('Save User')

class ServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    rate = FloatField('Default Rate', validators=[DataRequired()])
    validity = StringField('Validity', validators=[Length(max=50)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Service')

class StockItemForm(FlaskForm):
    service_id = SelectField('Service', coerce=int, validators=[DataRequired()])
    name = StringField('Name', validators=[Length(max=100)])
    mail = StringField('Email', validators=[Length(max=100)])
    password = StringField('Password', validators=[Length(max=100)])
    profile_link = StringField('Profile Link', validators=[Length(max=255)])
    recovery_mail = StringField('Recovery Email', validators=[Length(max=100)])
    two_factor = StringField('2FA', validators=[Length(max=100)])
    rate = FloatField('Rate', validators=[DataRequired()])
    is_old = BooleanField('Is Old')
    submit = SubmitField('Save Item')

from flask_wtf.file import FileField, FileAllowed

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    photo_url = StringField('Photo URL (Enter a URL)', validators=[Optional(), Length(max=255)])
    photo_file = FileField('Photo Upload', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    video_url = StringField('Video URL (Enter a URL)', validators=[Optional(), Length(max=255)])
    video_file = FileField('Video Upload', validators=[Optional(), FileAllowed(['mp4', 'mov', 'avi', 'wmv'], 'Videos only!')])
    submit = SubmitField('Save Post')

class FundProcessForm(FlaskForm):
    status = SelectField('Status', 
                        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                        validators=[DataRequired()])
    is_received = BooleanField('Received')
    admin_notes = TextAreaField('Admin Notes')
    submit = SubmitField('Process Request')

class WebsiteSettingForm(FlaskForm):
    site_name = StringField('Website Name', validators=[DataRequired(), Length(max=100)])
    logo_url = StringField('Logo URL', validators=[Length(max=255)])
    primary_color = StringField('Primary Color', validators=[Length(max=20)])
    secondary_color = StringField('Secondary Color', validators=[Length(max=20)])
    contact_phone = StringField('Contact Phone', validators=[Length(max=20)])
    contact_email = StringField('Contact Email', validators=[Email(), Length(max=100)])
    admin_notice = TextAreaField('Admin Notice')
    minimum_fund = FloatField('Minimum Fund (BDT)', validators=[DataRequired()])
    submit = SubmitField('Save Settings')

class OtherOrderTypeForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired(), Length(max=100)])
    rate = FloatField('Rate', validators=[DataRequired()])
    validity = StringField('Validity', validators=[Length(max=50)])
    description = TextAreaField('Description')
    required_fields = TextAreaField('Required Fields (JSON)')
    is_active = BooleanField('Is Active')
    submit = SubmitField('Save Order Type')
