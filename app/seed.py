"""Database seeding: load official IBA cocktails and create a default admin.

The IBA cocktail data lives in ``app/data/iba_cocktails.json`` as a list of
objects with this schema:

    {
      "name": "Negroni",
      "category": "The Unforgettables",   # one of the IBA categories
      "glass": "Old Fashioned",
      "ingredients": ["30 ml Gin", "30 ml Campari", "30 ml Sweet Vermouth"],
      "garnish": "Half orange slice",
      "method": "Build into an old fashioned glass ... Garnish."
    }

Seeding is idempotent: existing cocktails (matched by name) and the admin user
are left untouched, so it is safe to run repeatedly.
"""
import json
from pathlib import Path

from flask import current_app

from app.extensions import db
from app.models import Cocktail, User

DATA_FILE = Path(__file__).resolve().parent / "data" / "iba_cocktails.json"


def _load_iba_data():
    if not DATA_FILE.exists():
        print(f"WARNING: {DATA_FILE} not found — no IBA cocktails seeded.")
        return []
    with DATA_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def seed_cocktails():
    added = 0
    for item in _load_iba_data():
        name = item.get("name", "").strip()
        if not name:
            continue
        if Cocktail.query.filter_by(name=name).first():
            continue
        ingredients = item.get("ingredients") or []
        if isinstance(ingredients, list):
            ingredients = "\n".join(ingredients)
        cocktail = Cocktail(
            name=name,
            category=item.get("category", "The Unforgettables"),
            glass=item.get("glass"),
            ingredients=ingredients,
            garnish=item.get("garnish"),
            method=item.get("method"),
            is_iba=True,
            is_available=True,
        )
        db.session.add(cocktail)
        added += 1
    db.session.commit()
    print(f"Seeded {added} new IBA cocktails ({Cocktail.query.count()} total).")


def seed_admin():
    username = current_app.config["DEFAULT_ADMIN_USERNAME"]
    if User.query.filter_by(name=username).first():
        print(f"Admin '{username}' already exists.")
        return
    admin = User(name=username, is_admin=True)
    admin.set_password(current_app.config["DEFAULT_ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()
    print(f"Created admin '{username}'.")


def seed_database():
    from app.ingredients import rebuild_ingredient_index

    db.create_all()
    seed_admin()
    seed_cocktails()
    # Parse recipes into the ingredient inventory used for bar-stock filtering.
    rebuild_ingredient_index()
    from app.models import Ingredient

    print(f"Indexed {Ingredient.query.count()} distinct ingredients.")
