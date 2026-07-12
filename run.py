"""Entry point for the Ducktails app.

Usage:
    python run.py            # start dev server on http://127.0.0.1:5000
    flask --app run seed     # (re)seed the database with IBA cocktails + admin
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


if __name__ == "__main__":
    app.run(debug=True)
