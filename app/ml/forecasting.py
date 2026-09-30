from app.services.analytics_service import AnalyticsService


class ExpenseForecaster:
    @staticmethod
    def forecast_next_month_spending(user_id: int) -> dict:
        monthly_data = AnalyticsService.get_monthly_spending(user_id, months=6)
        amounts = [m["amount"] for m in monthly_data]

        if not amounts or sum(amounts) == 0:
            return {
                "current_monthly_spending": 0.0,
                "estimated_next_month": 0.0,
                "growth_percentage": 0.0,
                "label": "Estimated projection based on historical trends",
            }

        curr_month_spending = amounts[-1] if amounts else 0.0

        # Weighted moving average (giving more weight to recent months)
        weights = [i + 1 for i in range(len(amounts))]
        weighted_sum = sum(w * a for w, a in zip(weights, amounts))
        total_weight = sum(weights)

        estimated_next_month = round(weighted_sum / total_weight, 2)

        growth_pct = 0.0
        if curr_month_spending > 0:
            growth_pct = round(((estimated_next_month - curr_month_spending) / curr_month_spending) * 100, 1)

        return {
            "current_monthly_spending": round(curr_month_spending, 2),
            "estimated_next_month": estimated_next_month,
            "growth_percentage": growth_pct,
            "label": "Estimated projection based on weighted historical trends (Not guaranteed)",
        }
