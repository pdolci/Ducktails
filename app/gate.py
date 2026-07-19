"""Shared-secret access gate.

The app is meant to be handed out at an event (QR code / short link), not to be
reachable by anyone who stumbles on the domain. When ACCESS_CODE is configured,
every request must come from a visitor who has already presented the code:

    https://drinks.loonybin.it/?k=<ACCESS_CODE>

On a correct code we set a flag in the (signed) session cookie and redirect to
the same path without the query parameter, so the secret does not linger in the
browser history or leak through the Referer header. Visitors without it get a
plain 404 — the app does not advertise that it exists.

This is a shared secret, not per-user authentication: it keeps out bots,
scanners and passers-by (and the unbounded user/request creation they could
trigger), while costing guests nothing after the first scan.

If ACCESS_CODE is empty the gate is disabled entirely, so local development and
LAN-only deployments are unaffected.
"""
import hmac
from urllib.parse import urlencode

from flask import abort, redirect, request, session

SESSION_KEY = "access_ok"
CODE_PARAM = "k"


def init_gate(app):
    """Register the access gate on the given Flask app."""

    @app.before_request
    def _check_access():
        code = app.config.get("ACCESS_CODE") or ""
        if not code:
            return None  # gate disabled

        if session.get(SESSION_KEY):
            return None  # already let in

        supplied = request.args.get(CODE_PARAM)
        if supplied and hmac.compare_digest(supplied, code):
            session[SESSION_KEY] = True
            session.permanent = True  # survive browser restarts during the event
            # Redirect to the same path with the secret stripped from the query.
            remaining = {
                key: value
                for key, value in request.args.to_dict(flat=True).items()
                if key != CODE_PARAM
            }
            target = request.path
            if remaining:
                target = f"{target}?{urlencode(remaining)}"
            return redirect(target)

        # No valid code: behave as if nothing is hosted here.
        abort(404)
