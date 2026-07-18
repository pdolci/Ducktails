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

### Run with Docker

The app ships with a production image (gunicorn) and a persistent SQLite volume.
The database is seeded automatically on first start.

```bash
docker compose up --build      # → http://localhost:8000
```

Configure via environment in `docker-compose.yml` (or `-e` flags): `SECRET_KEY`
(set a real one in production), `ADMIN_USERNAME`, `ADMIN_PASSWORD`. Data persists
in the named volume `ducktails-data` (mounted at `/data`), so restarts keep users
and requests. To reset everything: `docker compose down -v`.

Without compose:

```bash
docker build -t ducktails .
docker run -p 8000:8000 -v ducktails-data:/data \
  -e SECRET_KEY=change-me -e ADMIN_PASSWORD=s3cret ducktails
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
run.py                   entry point + `seed` / `reset` CLI commands
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

## Maintenance

Two CLI commands manage the database. Locally use `flask --app run <cmd>`; with
Docker run them inside the container with `docker compose exec web <cmd>`.

### `seed` — populate the database (idempotent)

```bash
flask --app run seed
# Docker: docker compose exec web flask --app run seed
```

Creates the tables, the default admin, the 89 official IBA cocktails, and indexes
their ingredients. Safe to run repeatedly: existing cocktails, the admin, and any
manual ingredient stock flags are left untouched. Runs automatically on container
start (see `docker/entrypoint.sh`).

### `reset` — fresh-start the bar (repeatable)

```bash
flask --app run reset
# Docker: docker compose exec web flask --app run reset
```

For starting a new event with a clean slate. It:

- deletes **all requests**,
- deletes **all customer (non-admin) users**,
- marks **every ingredient out of stock**,
- **keeps** admin accounts and all cocktails.

After a reset the customer cocktail list is **empty** — a cocktail is *orderable*
only when it is available **and** all its ingredients are in stock. Go to
**Admin → Bar stock** and flag the ingredients you actually have; the preparable
cocktails reappear automatically. These stock flags survive container restarts
(the automatic `seed` never overwrites them).

> `reset` is a targeted, data-preserving alternative to wiping the whole SQLite
> volume with `docker compose down -v` (which also destroys cocktails and admins).

## Notes

This app is designed for single-machine / trusted-LAN use (e.g. a party or a
bar). Regular-user identification is name-only by design.

Behind a reverse proxy (e.g. nginx) terminating HTTPS, the app trusts one proxy
hop via Werkzeug `ProxyFix`. Set `SESSION_COOKIE_SECURE=true` in production so
the session cookie is only sent over TLS.
