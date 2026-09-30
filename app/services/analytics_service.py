from datetime import datetime, timedelta, timezone
from collections import defaultdict
from sqlalchemy import func
from app.extensions import db
from app.models.expense import Expense
from app.models.group import Group, GroupMember


class AnalyticsService:
    @staticmethod
    def _get_user_group_ids(user_id: int) -> list[int]:
        return [
            m.group_id for m in GroupMember.query.filter_by(user_id=user_id).all()
        ]

    @staticmethod
    def get_category_spending(user_id: int) -> dict[str, float]:
        group_ids = AnalyticsService._get_user_group_ids(user_id)
        if not group_ids:
            return {}

        results = (
            db.session.query(Expense.category, func.sum(Expense.amount))
            .filter(Expense.group_id.in_(group_ids))
            .group_by(Expense.category)
            .all()
        )
        return {category: round(float(total), 2) for category, total in results if total}

    @staticmethod
    def get_monthly_spending(user_id: int, months: int = 6) -> list[dict]:
        group_ids = AnalyticsService._get_user_group_ids(user_id)
        if not group_ids:
            return []

        expenses = (
            Expense.query.filter(Expense.group_id.in_(group_ids))
            .order_by(Expense.expense_date.asc())
            .all()
        )

        monthly_map = defaultdict(float)
        now = datetime.now(timezone.utc)

        # Generate last N months keys
        for i in range(months - 1, -1, -1):
            target_date = now - timedelta(days=i * 30)
            month_key = target_date.strftime("%b %Y")
            monthly_map[month_key] = 0.0

        for exp in expenses:
            month_key = exp.expense_date.strftime("%b %Y")
            if month_key in monthly_map:
                monthly_map[month_key] += exp.amount

        return [{"month": k, "amount": round(v, 2)} for k, v in monthly_map.items()]

    @staticmethod
    def get_group_spending_comparison(user_id: int) -> list[dict]:
        group_ids = AnalyticsService._get_user_group_ids(user_id)
        if not group_ids:
            return []

        results = (
            db.session.query(Group.name, func.sum(Expense.amount))
            .join(Expense, Group.id == Expense.group_id)
            .filter(Group.id.in_(group_ids))
            .group_by(Group.id, Group.name)
            .all()
        )
        return [{"group_name": name, "amount": round(float(total), 2)} for name, total in results]

    @staticmethod
    def generate_spending_insights(user_id: int) -> list[str]:
        group_ids = AnalyticsService._get_user_group_ids(user_id)
        if not group_ids:
            return ["No expense data available yet to generate spending insights."]

        insights = []

        # 1. Highest category insight
        cat_spending = AnalyticsService.get_category_spending(user_id)
        if cat_spending:
            top_category = max(cat_spending, key=cat_spending.get)
            top_amount = cat_spending[top_category]
            total_spent = sum(cat_spending.values())
            pct = (top_amount / total_spent * 100) if total_spent > 0 else 0
            insights.append(
                f"{top_category} is your highest spending category at ₹{top_amount:,.2f} ({pct:.1f}% of total spending)."
            )

        # 2. Month over month trend
        monthly = AnalyticsService.get_monthly_spending(user_id, months=2)
        if len(monthly) >= 2:
            prev_month_amt = monthly[-2]["amount"]
            curr_month_amt = monthly[-1]["amount"]

            if prev_month_amt > 0:
                diff_pct = ((curr_month_amt - prev_month_amt) / prev_month_amt) * 100
                if diff_pct > 0:
                    insights.append(f"Your spending increased by {diff_pct:.1f}% compared with the previous month.")
                elif diff_pct < 0:
                    insights.append(f"Your spending decreased by {abs(diff_pct):.1f}% compared with the previous month.")
                else:
                    insights.append("Your spending remained unchanged compared with the previous month.")

        # 3. Average monthly spending
        all_monthly = AnalyticsService.get_monthly_spending(user_id, months=6)
        active_months = [m["amount"] for m in all_monthly if m["amount"] > 0]
        if active_months:
            avg_monthly = sum(active_months) / len(active_months)
            insights.append(f"Your average monthly group expenditure is ₹{avg_monthly:,.2f}.")

        if not insights:
            insights.append("Start adding expenses to receive real-time financial insights.")

        return insights
