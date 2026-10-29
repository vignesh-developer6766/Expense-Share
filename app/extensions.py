import logging
from urllib.parse import urlparse
from flask import current_app, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, ValidationError, same_origin, validate_csrf

logger = logging.getLogger(__name__)


class AppCSRFProtect(CSRFProtect):
    """Enhanced CSRF protection supporting trusted proxy origins.

    Maintains full cryptographic CSRF token validation on all POST/PUT/PATCH/DELETE
    requests, while verifying HTTPS referrers against request.host and configured
    TRUSTED_HOSTS.
    """

    def protect(self, apply_exemptions=False):
        if apply_exemptions:
            if not request.endpoint:
                return
            if self._is_exempt():
                return

        if request.method not in current_app.config["WTF_CSRF_METHODS"]:
            return

        try:
            token = self._get_csrf_token()
            validate_csrf(token)
        except ValidationError as e:
            logger.info("CSRF validation failed: %s", e.args[0])
            self._error_response(e.args[0])

        if request.is_secure and current_app.config.get("WTF_CSRF_SSL_STRICT", True):
            if not request.referrer:
                self._error_response("The referrer header is missing.")

            good_referrer = f"https://{request.host}/"
            if not same_origin(request.referrer, good_referrer):
                parsed = urlparse(request.referrer)
                trusted_hosts = set(current_app.config.get("TRUSTED_HOSTS", []))
                if not (parsed.scheme == "https" and parsed.hostname in trusted_hosts):
                    self._error_response("The referrer does not match the host.")

        g.csrf_valid = True


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = AppCSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
