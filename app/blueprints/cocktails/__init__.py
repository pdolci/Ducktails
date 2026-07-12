from flask import Blueprint

bp = Blueprint("cocktails", __name__, url_prefix="/cocktails")

from app.blueprints.cocktails import routes  # noqa: E402,F401
