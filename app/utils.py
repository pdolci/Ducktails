"""Shared helpers: session-based current user and access-control decorators.

Auth model (see project spec):
  - Regular users are identified by NAME only. On "login" their name is stored
    in the session (user id under session['user_id']).
  - Admins additionally authenticate with a password. Admin status is derived
    from the User row (is_admin), not from a separate session flag.
"""
from functools import wraps

from flask import flash, g, redirect, session, url_for


def get_current_user():
    """Return the User for the current session, or None. Cached on flask.g."""
    if "user" in g:
        return g.user
    from app.models import User

    user = None
    user_id = session.get("user_id")
    if user_id is not None:
        user = User.query.get(user_id)
    g.user = user
    return user


def login_user(user):
    session["user_id"] = user.id
    g.user = user


def logout_user():
    session.pop("user_id", None)
    g.pop("user", None)


def login_required(view):
    """Require any identified user (regular or admin)."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if get_current_user() is None:
            flash("Please identify yourself first.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Require an authenticated admin."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            flash("Please identify yourself first.", "warning")
            return redirect(url_for("auth.login"))
        if not user.is_admin:
            flash("Administrator access required.", "danger")
            return redirect(url_for("main.index"))
        return view(*args, **kwargs)

    return wrapped
