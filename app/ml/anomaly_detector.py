import numpy as np
from app.models.expense import Expense


class AnomalyDetector:
    @staticmethod
    def detect_anomaly(group_id: int, amount: float, category: str = None) -> dict:
        query = Expense.query.filter_by(group_id=group_id)
        if category:
            query = query.filter_by(category=category)

        existing_amounts = [exp.amount for exp in query.all() if exp.amount > 0]

        if len(existing_amounts) < 3:
            # Simple thresholding fallback when historical data is sparse
            is_anomaly = amount >= 5000.0
            return {
                "is_anomaly": is_anomaly,
                "upper_threshold": 5000.0,
                "message": "⚠️ Unusual expense detected. This expense is significantly higher than typical spending." if is_anomaly else "",
            }

        q25, q75 = np.percentile(existing_amounts, [25, 75])
        iqr = q75 - q25
        upper_threshold = q75 + (1.5 * iqr)

        is_anomaly = amount > upper_threshold

        return {
            "is_anomaly": bool(is_anomaly),
            "upper_threshold": round(float(upper_threshold), 2),
            "median_spending": round(float(np.median(existing_amounts)), 2),
            "message": f"⚠️ Unusual expense detected. ₹{amount:,.2f} is significantly higher than your typical group spending (Threshold: ₹{upper_threshold:,.2f})." if is_anomaly else "",
        }
