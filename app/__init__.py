"""Application factory."""
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.extensions import csrf, db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Behind one reverse proxy (nginx): trust its X-Forwarded-* headers so
    # request.scheme/host reflect the original HTTPS request. Harmless in local
    # dev (no such headers are present there).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    csrf.init_app(app)

    # Import models so SQLAlchemy is aware of them before create_all().
    from app import models  # noqa: F401

    # --- Blueprints ---------------------------------------------------------
    from app.blueprints.main import bp as main_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.cocktails import bp as cocktails_bp
    from app.blueprints.requests import bp as requests_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cocktails_bp)
    app.register_blueprint(requests_bp)

    # --- Template globals ---------------------------------------------------
    from app.utils import get_current_user

    @app.context_processor
    def inject_current_user():
        return {"current_user": get_current_user()}

    # --- Create tables on first run ----------------------------------------
    with app.app_context():
        db.create_all()

    return app
