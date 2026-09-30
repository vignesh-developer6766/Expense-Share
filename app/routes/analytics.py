from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.analytics_service import AnalyticsService
from app.ml.forecasting import ExpenseForecaster

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("")
@analytics_bp.route("/")
@login_required
def index():
    category_data = AnalyticsService.get_category_spending(current_user.id)
    monthly_trend = AnalyticsService.get_monthly_spending(current_user.id, months=6)
    group_comparison = AnalyticsService.get_group_spending_comparison(current_user.id)
    insights = AnalyticsService.generate_spending_insights(current_user.id)
    forecast = ExpenseForecaster.forecast_next_month_spending(current_user.id)

    return render_template(
        "analytics/index.html",
        category_data=category_data,
        monthly_trend=monthly_trend,
        group_comparison=group_comparison,
        insights=insights,
        forecast=forecast,
    )
