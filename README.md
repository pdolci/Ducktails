# Ducktails 🦆🍸

Web app to manage **cocktail requests** from named users. Cocktails are the
official **IBA** (International Bartenders Association) drinks; administrators
can also add their own **house creations** and toggle whether each cocktail is
available for requests.

Built with **Flask + SQLAlchemy + SQLite + Bootstrap 5**. The entire database is
a single local file (`ducktails.db`).

## Features

- **Users** identify themselves by **name only** — no password, no sign-up flow.
- **Admins** log in with username + password and can:
  - create / edit / delete cocktails (IBA or house creations),
  - toggle each cocktail's **availability** for requests,
  - manage **bar stock**: mark ingredients out of stock, and every cocktail that
    needs them is automatically hidden from customers and blocked for requests,
  - view and manage all incoming requests (pending → served / cancelled).
- **Requests**: an identified user picks an *available* cocktail and places a
  request; they can track their own requests and cancel pending ones.
- Seeded with the official **IBA** cocktail list (The Unforgettables,
  Contemporary Classics, New Era Drinks) including recipes.

## Quick start

```powershell
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Seed the database (creates ducktails.db, IBA cocktails, default admin)
flask --app run seed

# 3. Run
python run.py
# → http://127.0.0.1:5000
```

### Default admin

| username | password |
|----------|----------|
| `admin`  | `admin`  |

Override before seeding via environment variables:

```powershell
$env:ADMIN_USERNAME = "paolo"; $env:ADMIN_PASSWORD = "s3cret"; flask --app run seed
```

Set a real `SECRET_KEY` in production (env var).

## Architecture

```
app/
  __init__.py            app factory: config, db, blueprints, create_all()
  config.py              configuration (SQLite path, admin defaults, secret)
  extensions.py          SQLAlchemy instance + CSRF protection
  models.py              User, Cocktail, Request, Ingredient  ← shared contract
  utils.py               session current-user + login_required/admin_required
  ingredients.py         parse recipes into a canonical ingredient inventory
  seed.py                loads IBA data + creates admin, indexes ingredients
  data/
    iba_cocktails.json   official IBA cocktails + recipes (seed source)
  blueprints/
    main/                home / dashboard
    auth/                name identify + admin login/logout
    cocktails/           list, detail, admin CRUD, availability toggle
    requests/            place request, my requests, admin manage
  templates/             Jinja2 + Bootstrap 5 (base.html + per-module folders)
run.py                   entry point + `flask --app run seed` command
```

### Data model

- **User** — `name` (unique), `is_admin`, optional `password_hash`.
- **Cocktail** — `name`, `category`, `glass`, `ingredients`, `garnish`,
  `method`, `is_iba`, `is_available`.
- **Request** — links a user to a cocktail with a `status`
  (`pending` / `served` / `cancelled`) and optional `notes`.
- **Ingredient** — a bar ingredient with an `in_stock` flag, linked many-to-many
  to the cocktails that need it. A cocktail is *orderable* only when it is
  available **and** all its ingredients are in stock.

## Notes

This app is designed for single-machine / trusted-LAN use (e.g. a party or a
bar). Regular-user identification is name-only by design.
