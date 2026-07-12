"""Database models for Ducktails.

Three entities:
  - User     : anyone who can request a cocktail (identified by name). Admins
               additionally have a password and elevated privileges.
  - Cocktail : an IBA official cocktail or an admin-invented one.
  - Request  : a booking placed by a user for an available cocktail.
"""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

# --- Cocktail categories -----------------------------------------------------
CATEGORY_UNFORGETTABLES = "The Unforgettables"
CATEGORY_CONTEMPORARY = "Contemporary Classics"
CATEGORY_NEW_ERA = "New Era Drinks"
CATEGORY_CUSTOM = "House Creation"

IBA_CATEGORIES = [
    CATEGORY_UNFORGETTABLES,
    CATEGORY_CONTEMPORARY,
    CATEGORY_NEW_ERA,
]
ALL_CATEGORIES = IBA_CATEGORIES + [CATEGORY_CUSTOM]

# --- Request statuses --------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_SERVED = "served"
STATUS_CANCELLED = "cancelled"
REQUEST_STATUSES = [STATUS_PENDING, STATUS_SERVED, STATUS_CANCELLED]

# --- Cocktail <-> Ingredient link (bar stock) --------------------------------
cocktail_ingredients = db.Table(
    "cocktail_ingredients",
    db.Column("cocktail_id", db.ForeignKey("cocktails.id"), primary_key=True),
    db.Column("ingredient_id", db.ForeignKey("ingredients.id"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    # Only admins have a password; regular users identify by name only.
    password_hash = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    requests = db.relationship(
        "Request", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.name}{' (admin)' if self.is_admin else ''}>"


class Cocktail(db.Model):
    __tablename__ = "cocktails"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), unique=True, nullable=False)
    category = db.Column(db.String(80), nullable=False, default=CATEGORY_CUSTOM)
    glass = db.Column(db.String(120), nullable=True)
    # Free text, one ingredient per line.
    ingredients = db.Column(db.Text, nullable=True)
    garnish = db.Column(db.String(255), nullable=True)
    method = db.Column(db.Text, nullable=True)

    is_iba = db.Column(db.Boolean, default=False, nullable=False)
    # Whether the cocktail can currently be requested by users.
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    requests = db.relationship(
        "Request", back_populates="cocktail", cascade="all, delete-orphan"
    )
    # Canonical ingredients this cocktail needs, used for bar-stock filtering.
    required_ingredients = db.relationship(
        "Ingredient", secondary=cocktail_ingredients, back_populates="cocktails"
    )

    @property
    def ingredient_list(self):
        """Ingredients split into a clean list of lines."""
        if not self.ingredients:
            return []
        return [line.strip() for line in self.ingredients.splitlines() if line.strip()]

    @property
    def missing_ingredients(self):
        """Required ingredients that are currently out of stock."""
        return [ing for ing in self.required_ingredients if not ing.in_stock]

    @property
    def is_orderable(self):
        """Can a customer request this now? Available AND all ingredients in stock."""
        return self.is_available and not self.missing_ingredients

    def __repr__(self):
        return f"<Cocktail {self.name}>"


class Request(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cocktail_id = db.Column(db.Integer, db.ForeignKey("cocktails.id"), nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="requests")
    cocktail = db.relationship("Cocktail", back_populates="requests")

    def __repr__(self):
        return f"<Request #{self.id} {self.status}>"


class Ingredient(db.Model):
    """A bar ingredient. When out of stock, every cocktail that needs it is
    automatically hidden from customers and blocked for requests."""

    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    in_stock = db.Column(db.Boolean, default=True, nullable=False)

    cocktails = db.relationship(
        "Cocktail", secondary=cocktail_ingredients, back_populates="required_ingredients"
    )

    def __repr__(self):
        return f"<Ingredient {self.name}{'' if self.in_stock else ' (out)'}>"
