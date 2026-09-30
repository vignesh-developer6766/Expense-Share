from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.notification_service import NotificationService

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("")
@notifications_bp.route("/")
@login_required
def list_notifications():
    notifications = NotificationService.get_user_notifications(current_user.id)
    return render_template("notifications/list.html", notifications=notifications)


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    NotificationService.mark_notification_as_read(notification_id, current_user.id)
    return redirect(url_for("notifications.list_notifications"))


@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    count = NotificationService.mark_all_read(current_user.id)
    flash(f"Marked {count} notifications as read.", "success")
    return redirect(url_for("notifications.list_notifications"))
