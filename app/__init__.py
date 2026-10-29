import os
from flask import Flask, jsonify, redirect, url_for, render_template
from flask_login import current_user
from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf
import app.models  # noqa: F401
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.groups import groups_bp
from app.routes.expenses import expenses_bp
from app.routes.settlements import settlements_bp
from app.routes.analytics import analytics_bp
from app.routes.ai_routes import ai_bp
from app.routes.ocr_routes import ocr_bp
from app.routes.recurring import recurring_bp
from app.routes.notifications import notifications_bp
from app.routes.users import users_bp
from app.routes.api import api_bp
from app.utils.helpers import CATEGORY_MAP, format_inr, get_category_info


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    flask_app = Flask(__name__)
    flask_app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure upload directory exists
    os.makedirs(flask_app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(flask_app.root_path, "..", "instance"), exist_ok=True)

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    csrf.init_app(flask_app)

    # Register Blueprints
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(dashboard_bp)
    flask_app.register_blueprint(groups_bp)
    flask_app.register_blueprint(expenses_bp)
    flask_app.register_blueprint(settlements_bp)
    flask_app.register_blueprint(analytics_bp)
    flask_app.register_blueprint(ai_bp)
    flask_app.register_blueprint(ocr_bp)
    flask_app.register_blueprint(recurring_bp)
    flask_app.register_blueprint(notifications_bp)
    flask_app.register_blueprint(users_bp)
    flask_app.register_blueprint(api_bp)

    # Global Jinja Context Processors & Filters
    flask_app.jinja_env.globals.update(
        category_map=CATEGORY_MAP,
        get_category_info=get_category_info,
    )
    flask_app.jinja_env.filters["inr"] = format_inr

    @flask_app.context_processor
    def inject_global_data():
        if current_user.is_authenticated:
            from app.services.notification_service import NotificationService
            return {
                "unread_notification_count": NotificationService.get_unread_count(current_user.id),
                "category_map": CATEGORY_MAP,
            }
        return {
            "unread_notification_count": 0,
            "category_map": CATEGORY_MAP,
        }

    # Error handlers
    @flask_app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @flask_app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    @flask_app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # Root route
    @flask_app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    # Health check
    @flask_app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "service": "ExpenseShare AI"}), 200

    # Configure Trusted Proxy & ProxyFix middleware
    trusted_hosts = flask_app.config.get("TRUSTED_HOSTS", [])

    class TrustedProxyFix:
        def __init__(self, wsgi_app, hosts):
            self.wsgi_app = wsgi_app
            self.trusted_hosts = set(hosts)

        def __call__(self, environ, start_response):
            orig_host = environ.get("HTTP_X_ORIGINAL_HOST") or environ.get("HTTP_X_FORWARDED_HOST")
            if orig_host:
                for candidate in [h.strip() for h in orig_host.split(",")]:
                    host_only = candidate.split(":")[0]
                    if host_only in self.trusted_hosts:
                        environ["HTTP_HOST"] = candidate
                        break

            proto = environ.get("HTTP_X_FORWARDED_PROTO")
            if proto:
                first_proto = [p.strip() for p in proto.split(",")][0]
                if first_proto in ("http", "https"):
                    environ["wsgi.url_scheme"] = first_proto

            return self.wsgi_app(environ, start_response)

    from werkzeug.middleware.proxy_fix import ProxyFix
    flask_app.wsgi_app = TrustedProxyFix(
        ProxyFix(flask_app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=1, x_prefix=1),
        trusted_hosts,
    )

    return flask_app
