from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.recurring_service import RecurringService
from app.services.group_service import GroupService

recurring_bp = Blueprint("recurring", __name__, url_prefix="/recurring")

CATEGORIES = ["Food", "Transport", "Shopping", "Entertainment", "Utilities", "Travel", "Rent", "Other"]
FREQUENCIES = ["daily", "weekly", "monthly", "yearly"]


@recurring_bp.route("")
@recurring_bp.route("/")
@login_required
def list_recurring():
    user_recurring = RecurringService.get_user_recurring_expenses(current_user.id)
    user_groups = GroupService.get_user_groups(current_user.id)
    return render_template("recurring/list.html", recurring_expenses=user_recurring, groups=user_groups)


@recurring_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_recurring():
    user_groups = GroupService.get_user_groups(current_user.id)
    if not user_groups:
        flash("You must join or create a group first.", "warning")
        return redirect(url_for("groups.create_group"))

    if request.method == "POST":
        group_id = request.form.get("group_id", type=int)
        description = request.form.get("description", "").strip()
        amount_str = request.form.get("amount", "0")
        frequency = request.form.get("frequency", "monthly")
        category = request.form.get("category", "Other")
        due_date_str = request.form.get("next_due_date", "")

        try:
            amount = float(amount_str)
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            flash("Invalid amount or date format provided.", "danger")
            return render_template("recurring/create.html", groups=user_groups, categories=CATEGORIES, frequencies=FREQUENCIES)

        try:
            rec = RecurringService.create_recurring_expense(
                group_id=group_id,
                description=description,
                amount=amount,
                frequency=frequency,
                next_due_date=due_date,
                category=category,
                creator_id=current_user.id,
            )
            flash(f"Recurring expense '{rec.description}' created successfully!", "success")
            return redirect(url_for("recurring.list_recurring"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("recurring/create.html", groups=user_groups, categories=CATEGORIES, frequencies=FREQUENCIES)


@recurring_bp.route("/<int:recurring_id>/toggle", methods=["POST"])
@login_required
def toggle_recurring(recurring_id):
    success, message = RecurringService.toggle_active_status(recurring_id, current_user.id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("recurring.list_recurring"))


@recurring_bp.route("/process", methods=["POST"])
@login_required
def process_due():
    count = RecurringService.process_due_recurring_expenses()
    flash(f"Processed {count} due recurring expenses!", "info")
    return redirect(url_for("recurring.list_recurring"))
