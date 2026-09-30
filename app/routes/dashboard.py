from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.balance_service import BalanceService
from app.services.expense_service import ExpenseService
from app.services.group_service import GroupService
from app.services.settlement_service import SettlementService
from app.services.analytics_service import AnalyticsService
from app.ml.forecasting import ExpenseForecaster
from app.ml.anomaly_detector import AnomalyDetector

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    user_id = current_user.id

    # 1. Stat cards summary
    overall_summary = BalanceService.get_user_overall_summary(user_id)

    # 2. Recent Expenses
    recent_expenses = ExpenseService.get_user_expenses(user_id=user_id, sort_by="newest")[:6]

    # 3. Active Groups Overview
    user_groups = GroupService.get_user_groups(user_id)
    group_cards = []
    total_group_spending = 0.0

    all_suggested_settlements = []

    for group in user_groups:
        group_bal = BalanceService.get_group_member_balances(group.id)
        group_spending = sum(exp.amount for exp in group.expenses)
        total_group_spending += group_spending

        group_cards.append({
            "group": group,
            "total_spending": round(group_spending, 2),
            "member_count": len(group.members),
            "members": [m.user for m in group.members],
            "user_net_balance": group_bal.get(user_id, 0.0),
        })

        # Get simplified debt transactions
        debts = SettlementService.simplify_group_debts(group.id)
        for d in debts:
            d["group_name"] = group.name
            all_suggested_settlements.append(d)

    overall_summary["total_group_expenses"] = round(total_group_spending, 2)

    # 4. Analytics & Charts
    category_data = AnalyticsService.get_category_spending(user_id)
    monthly_trend = AnalyticsService.get_monthly_spending(user_id, months=6)
    insights = AnalyticsService.generate_spending_insights(user_id)
    forecast = ExpenseForecaster.forecast_next_month_spending(user_id)

    return render_template(
        "dashboard/index.html",
        overall_summary=overall_summary,
        recent_expenses=recent_expenses,
        groups=group_cards,
        category_data=category_data,
        monthly_trend=monthly_trend,
        suggested_settlements=all_suggested_settlements,
        insights=insights,
        forecast=forecast,
    )
