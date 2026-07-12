"""Shared Flask extensions, instantiated once and initialised in the app factory."""
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
# Enables the global `csrf_token()` template helper and enforces CSRF on POSTs.
csrf = CSRFProtect()
