"""Entry point for the Ducktails app.

Usage:
    python run.py            # start dev server on http://127.0.0.1:5000
    flask --app run seed     # (re)seed the database with IBA cocktails + admin
    flask --app run reset    # clear requests + customer users, all ingredients OFF
"""
from app import create_app
from app.extensions import db
from app.seed import seed_database

app = create_app()


@app.cli.command("seed")
def seed_command():
    """Seed the database with the official IBA cocktails and a default admin."""
    seed_database()
    print("Database seeded.")


@app.cli.command("reset")
def reset_command():
    """Fresh-start the bar: clear all requests and customer (non-admin) users,
    and mark EVERY ingredient out of stock so admins flag what's available.

    Keeps admin accounts and all cocktails untouched. Safe to run repeatedly
    (e.g. between events)."""
    from app.models import Ingredient, Request, User

    n_requests = Request.query.delete()
    n_users = User.query.filter_by(is_admin=False).delete()
    n_ingredients = Ingredient.query.update({Ingredient.in_stock: False})
    db.session.commit()

    admins = User.query.filter_by(is_admin=True).count()
    print(
        f"Reset done - removed {n_requests} request(s) and {n_users} customer "
        f"user(s); marked {n_ingredients} ingredient(s) out of stock; "
        f"kept {admins} admin(s) and all cocktails."
    )


if __name__ == "__main__":
    app.run(debug=True)
