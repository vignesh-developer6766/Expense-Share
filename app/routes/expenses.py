from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app.services.expense_service import ExpenseService
from app.services.group_service import GroupService
from app.services.export_service import ExportService
from app.ml.anomaly_detector import AnomalyDetector

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")

CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Entertainment",
    "Utilities",
    "Travel",
    "Rent",
    "Other",
]


@expenses_bp.route("")
@expenses_bp.route("/")
@login_required
def list_expenses():
    group_id = request.args.get("group_id", type=int)
    category = request.args.get("category", type=str)
    search = request.args.get("search", type=str)
    sort_by = request.args.get("sort_by", type=str, default="newest")

    expenses = ExpenseService.get_user_expenses(
        user_id=current_user.id,
        group_id=group_id,
        category=category,
        search=search,
        sort_by=sort_by,
    )
    user_groups = GroupService.get_user_groups(current_user.id)

    return render_template(
        "expenses/list.html",
        expenses=expenses,
        groups=user_groups,
        categories=CATEGORIES,
        selected_group_id=group_id,
        selected_category=category,
        search=search,
        sort_by=sort_by,
    )


@expenses_bp.route("/export/csv")
@login_required
def export_csv():
    group_id = request.args.get("group_id", type=int)
    category = request.args.get("category", type=str)

    csv_data = ExportService.export_expenses_to_csv(
        user_id=current_user.id,
        group_id=group_id,
        category=category,
    )

    filename = f"expenseshare_export_{current_user.id}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"},
    )


@expenses_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_expense():
    user_groups = GroupService.get_user_groups(current_user.id)
    if not user_groups:
        flash("You must create or join a group before adding an expense.", "warning")
        return redirect(url_for("groups.create_group"))

    selected_group_id = request.args.get("group_id", type=int)
    if not selected_group_id and user_groups:
        selected_group_id = user_groups[0].id

    selected_group = GroupService.get_group_by_id(selected_group_id) if selected_group_id else None

    if request.method == "POST":
        group_id = request.form.get("group_id", type=int)
        description = request.form.get("description", "").strip()
        amount_str = request.form.get("amount", "0")
        category = request.form.get("category", "Other")
        paid_by = request.form.get("paid_by", type=int)
        split_type = request.form.get("split_type", "equal")
        notes = request.form.get("notes", "").strip()
        receipt_file = request.files.get("receipt_image")

        try:
            amount = float(amount_str)
        except ValueError:
            flash("Invalid amount entered.", "danger")
            return render_template("expenses/create.html", groups=user_groups, categories=CATEGORIES, selected_group=selected_group)

        # Build split_data
        split_data = {}
        target_group = GroupService.get_group_by_id(group_id)
        if not target_group:
            flash("Invalid group selected.", "danger")
            return render_template("expenses/create.html", groups=user_groups, categories=CATEGORIES, selected_group=selected_group)

        member_ids = [m.user_id for m in target_group.members]

        if split_type == "equal":
            selected_users = request.form.getlist("equal_users", type=int)
            split_data["users"] = selected_users if selected_users else member_ids
        elif split_type == "exact":
            exact_map = {}
            for uid in member_ids:
                val = request.form.get(f"exact_{uid}", "0")
                try:
                    exact_map[uid] = float(val)
                except ValueError:
                    exact_map[uid] = 0.0
            split_data["exact"] = exact_map
        elif split_type == "percentage":
            pct_map = {}
            for uid in member_ids:
                val = request.form.get(f"percentage_{uid}", "0")
                try:
                    pct_map[uid] = float(val)
                except ValueError:
                    pct_map[uid] = 0.0
            split_data["percentage"] = pct_map
        elif split_type == "shares":
            shares_map = {}
            for uid in member_ids:
                val = request.form.get(f"shares_{uid}", "0")
                try:
                    shares_map[uid] = float(val)
                except ValueError:
                    shares_map[uid] = 0.0
            split_data["shares"] = shares_map

        try:
            expense = ExpenseService.create_expense(
                group_id=group_id,
                description=description,
                amount=amount,
                category=category,
                paid_by=paid_by,
                split_type=split_type,
                split_data=split_data,
                notes=notes,
                receipt_file=receipt_file,
            )
            flash(f"Expense '{expense.description}' added successfully!", "success")
            return redirect(url_for("groups.group_detail", group_id=group_id))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template(
                "expenses/create.html",
                groups=user_groups,
                categories=CATEGORIES,
                selected_group=target_group,
                form_data=request.form,
            )

    return render_template(
        "expenses/create.html",
        groups=user_groups,
        categories=CATEGORIES,
        selected_group=selected_group,
    )


@expenses_bp.route("/<int:expense_id>")
@login_required
def expense_detail(expense_id):
    expense = ExpenseService.get_expense_by_id(expense_id)
    if not expense or not GroupService.is_member(expense.group_id, current_user.id):
        flash("Expense not found or access unauthorized.", "danger")
        return redirect(url_for("expenses.list_expenses"))

    anomaly_info = AnomalyDetector.detect_anomaly(
        group_id=expense.group_id,
        amount=expense.amount,
        category=expense.category,
    )

    return render_template("expenses/detail.html", expense=expense, anomaly_info=anomaly_info)


@expenses_bp.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = ExpenseService.get_expense_by_id(expense_id)
    group_id = expense.group_id if expense else None

    success, message = ExpenseService.delete_expense(expense_id, current_user.id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    if group_id:
        return redirect(url_for("groups.group_detail", group_id=group_id))
    return redirect(url_for("expenses.list_expenses"))
