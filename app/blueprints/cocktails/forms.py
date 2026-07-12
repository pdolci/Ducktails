"""WTForms used by the cocktails blueprint."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional

from app.models import ALL_CATEGORIES


class CocktailForm(FlaskForm):
    """Create/edit form for a cocktail recipe."""

    name = StringField("Name", validators=[DataRequired()])
    category = SelectField(
        "Category",
        choices=[(c, c) for c in ALL_CATEGORIES],
        validators=[DataRequired()],
    )
    glass = StringField("Glass", validators=[Optional()])
    ingredients = TextAreaField(
        "Ingredients",
        validators=[Optional()],
        description="One per line",
    )
    garnish = StringField("Garnish", validators=[Optional()])
    method = TextAreaField("Method", validators=[Optional()])
    is_available = BooleanField("Available for requests", default=True)
