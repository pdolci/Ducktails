"""WTForms used by the auth blueprint."""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired


class NameForm(FlaskForm):
    """Regular-user identification form: name only, no password."""

    name = StringField("Your name", validators=[DataRequired()])


class AdminLoginForm(FlaskForm):
    """Administrator login form: name + password."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
