"""Requests (bookings) module.

Endpoints referenced elsewhere (base template):
    requests.create, requests.my, requests.manage, requests.update_status
"""
from flask import flash, redirect, render_template, request, url_for

from app.blueprints.requests import bp
from app.extensions import db
from app.models import Cocktail, Request, REQUEST_STATUSES, STATUS_CANCELLED, STATUS_PENDING
from app.utils import admin_required, get_current_user, login_required


def _is_safe_next(target):
    """Only allow redirecting to a same-site relative path."""
    return bool(target) and target.startswith("/") and not target.startswith("//")


@bp.route("/create", methods=["POST"])
@login_required
def create():
    user = get_current_user()

    cocktail_id = request.form.get("cocktail_id", type=int)
    notes = (request.form.get("notes") or "").strip() or None

    cocktail = Cocktail.query.get_or_404(cocktail_id)

    if not cocktail.is_orderable:
        if not cocktail.is_available:
            flash("That cocktail is not available for requests.", "danger")
        else:
            flash("That cocktail is temporarily out of stock.", "danger")
        return redirect(url_for("cocktails.detail", cocktail_id=cocktail.id))

    booking = Request(
        user=user,
        cocktail=cocktail,
        status=STATUS_PENDING,
        notes=notes,
    )
    db.session.add(booking)
    db.session.commit()

    flash(f"Your request for {cocktail.name} has been placed.", "success")
    return redirect(url_for("requests.my"))


@bp.route("/mine")
@login_required
def my():
    user = get_current_user()
    my_requests = (
        Request.query.filter_by(user_id=user.id)
        .order_by(Request.created_at.desc())
        .all()
    )
    return render_template("requests/my.html", requests=my_requests)


@bp.route("/manage")
@admin_required
def manage():
    status_filter = request.args.get("status")

    query = Request.query
    if status_filter in REQUEST_STATUSES:
        query = query.filter_by(status=status_filter)

    all_requests = query.order_by(Request.created_at.desc()).all()

    counts = {status: 0 for status in REQUEST_STATUSES}
    for req in Request.query.all():
        counts[req.status] = counts.get(req.status, 0) + 1

    return render_template(
        "requests/manage.html",
        requests=all_requests,
        counts=counts,
        status_filter=status_filter,
    )


@bp.route("/<int:request_id>/status", methods=["POST"])
@login_required
def update_status(request_id):
    user = get_current_user()
    booking = Request.query.get_or_404(request_id)
    new_status = request.form.get("status")

    if new_status not in REQUEST_STATUSES:
        flash("Invalid status.", "danger")
        return _redirect_after_status(user)

    if user.is_admin:
        booking.status = new_status
        db.session.commit()
        flash(f"Request #{booking.id} updated to {new_status}.", "success")
        return _redirect_after_status(user)

    # Regular users may only cancel their own pending request.
    if (
        booking.user_id != user.id
        or new_status != STATUS_CANCELLED
        or booking.status != STATUS_PENDING
    ):
        flash("You are not allowed to make that change.", "danger")
        return _redirect_after_status(user)

    booking.status = STATUS_CANCELLED
    db.session.commit()
    flash("Your request has been cancelled.", "success")
    return _redirect_after_status(user)


def _redirect_after_status(user):
    if user.is_admin:
        return redirect(url_for("requests.manage"))

    referrer = request.referrer
    if referrer:
        from urllib.parse import urlparse

        parsed = urlparse(referrer)
        if not parsed.netloc or parsed.netloc == request.host:
            path = parsed.path or url_for("requests.my")
            if _is_safe_next(path):
                return redirect(path)

    return redirect(url_for("requests.my"))
