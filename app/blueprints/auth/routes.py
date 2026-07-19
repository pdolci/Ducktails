"""Auth module.

Auth model (see project spec):
  - Regular users identify by NAME ONLY (no password). Logging in with a name
    that doesn't exist yet creates a new regular User.
  - Admins log in with name + password on a separate page.
"""
from flask import flash, redirect, render_template, request, url_for

from app.blueprints.auth import bp
from app.blueprints.auth.forms import AdminLoginForm, NameForm
from app.extensions import db
from app.models import User
from app.utils import login_user, logout_user


def _is_safe_next(target):
    """Only allow redirecting to a same-site relative path."""
    return bool(target) and target.startswith("/") and not target.startswith("//")


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        # Case-insensitive: 'Paolo', 'paolo' and 'pAoLo' are the same person.
        existing = User.find_by_name(name)
        if existing and existing.is_admin:
            flash("That name belongs to an administrator account. Please use the admin login.", "warning")
            return redirect(url_for("auth.admin_login"))

        user = existing
        if user is None:
            user = User(name=name, is_admin=False)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash(f"Welcome, {user.name}!", "success")

        next_url = request.args.get("next")
        if _is_safe_next(next_url):
            return redirect(next_url)
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", form=form)


@bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        user = User.find_by_name(username)
        if user and user.is_admin and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("main.index"))
        flash("Invalid administrator credentials.", "danger")

    return render_template("auth/admin_login.html", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
