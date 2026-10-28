from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User

users_bp = Blueprint("users", __name__, url_prefix="/users")


def _require_admin():
    """Redirect with a flash message if the current user is not an admin."""
    if not current_user.is_admin:
        flash("Access denied. Only administrators can manage user accounts.", "danger")
        return redirect(url_for("users.list_users"))
    return None


@users_bp.route("")
@users_bp.route("/list")
@login_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    user_data = []

    for u in users:
        group_count = len(u.group_memberships)
        expense_count = len(u.paid_expenses)
        user_data.append({
            "user": u,
            "group_count": group_count,
            "expense_count": expense_count,
        })

    return render_template("users/list.html", users=user_data)


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    denied = _require_admin()
    if denied:
        return denied

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.list_users"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not name or not email:
            flash("Name and email are required fields.", "danger")
            return render_template("users/edit.html", target_user=user)

        # Check duplicate email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash("An account with this email address already exists.", "danger")
            return render_template("users/edit.html", target_user=user)

        user.name = name
        user.email = email

        # Only admin can reset passwords — field is admin-only in template, but
        # we guard server-side too for safety.
        if password:
            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return render_template("users/edit.html", target_user=user)
            user.set_password(password)

        db.session.commit()
        flash(f"User '{user.name}' updated successfully!", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/edit.html", target_user=user)


@users_bp.route("/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    denied = _require_admin()
    if denied:
        return denied

    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.list_users"))

    if user.id == current_user.id:
        flash("You cannot delete your own active logged-in account.", "danger")
        return redirect(url_for("users.list_users"))

    user_name = user.name
    db.session.delete(user)
    db.session.commit()

    flash(f"User '{user_name}' deleted successfully!", "success")
    return redirect(url_for("users.list_users"))
