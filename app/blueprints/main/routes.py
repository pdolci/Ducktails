from flask import render_template

from app.blueprints.main import bp
from app.models import Cocktail, Ingredient, Request, STATUS_PENDING
from app.utils import get_current_user


@bp.route("/")
def index():
    # What customers actually see: available AND fully in stock.
    orderable_count = sum(1 for c in Cocktail.query.all() if c.is_orderable)
    user = get_current_user()
    stats = None
    if user and user.is_admin:
        stats = {
            "cocktails": Cocktail.query.count(),
            "available": orderable_count,
            "pending": Request.query.filter_by(status=STATUS_PENDING).count(),
            "requests": Request.query.count(),
            "out_of_stock": Ingredient.query.filter_by(in_stock=False).count(),
        }
    return render_template("main/index.html", available_count=orderable_count, stats=stats)
