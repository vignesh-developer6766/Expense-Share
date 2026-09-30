from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.balance_service import BalanceService
from app.services.settlement_service import SettlementService
from app.services.group_service import GroupService

settlements_bp = Blueprint("settlements", __name__, url_prefix="/settlements")


@settlements_bp.route("")
@settlements_bp.route("/")
@login_required
def list_settlements():
    group_id = request.args.get("group_id", type=int)
    user_groups = GroupService.get_user_groups(current_user.id)

    if not group_id and user_groups:
        group_id = user_groups[0].id

    selected_group = GroupService.get_group_by_id(group_id) if group_id else None

    # Overall Summary
    overall_summary = BalanceService.get_user_overall_summary(current_user.id)

    # Selected Group Data
    group_member_balances = []
    simplified_debts = []
    settlement_history = []

    if selected_group and GroupService.is_member(selected_group.id, current_user.id):
        raw_balances = BalanceService.get_group_member_balances(selected_group.id)
        for member in selected_group.members:
            group_member_balances.append({
                "user": member.user,
                "net_balance": raw_balances.get(member.user_id, 0.0),
            })

        simplified_debts = SettlementService.simplify_group_debts(selected_group.id)
        settlement_history = SettlementService.get_group_settlements(selected_group.id)

    return render_template(
        "settlements/list.html",
        groups=user_groups,
        selected_group=selected_group,
        overall_summary=overall_summary,
        group_member_balances=group_member_balances,
        simplified_debts=simplified_debts,
        settlement_history=settlement_history,
    )


@settlements_bp.route("/record", methods=["POST"])
@login_required
def record_settlement():
    group_id = request.form.get("group_id", type=int)
    payer_id = request.form.get("payer_id", type=int)
    receiver_id = request.form.get("receiver_id", type=int)
    amount_str = request.form.get("amount", "0")

    try:
        amount = float(amount_str)
    except ValueError:
        flash("Invalid settlement amount.", "danger")
        return redirect(url_for("settlements.list_settlements", group_id=group_id))

    if not GroupService.is_member(group_id, current_user.id):
        flash("Unauthorized action.", "danger")
        return redirect(url_for("settlements.list_settlements"))

    try:
        settlement = SettlementService.record_settlement(group_id, payer_id, receiver_id, amount)
        flash(f"Settlement payment of ₹{settlement.amount:.2f} recorded successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("settlements.list_settlements", group_id=group_id))
