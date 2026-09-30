from datetime import datetime, timezone
from difflib import SequenceMatcher
from app.models.expense import Expense


class DuplicateDetector:
    @staticmethod
    def check_duplicate(
        group_id: int,
        description: str,
        amount: float,
        paid_by: int,
        expense_date: datetime = None,
    ) -> dict:
        desc_clean = description.strip().lower()
        if not expense_date:
            expense_date = datetime.now(timezone.utc)

        existing_expenses = Expense.query.filter_by(group_id=group_id).all()

        possible_duplicates = []

        for exp in existing_expenses:
            # 1. Description similarity
            exp_desc_clean = exp.description.strip().lower()
            ratio = SequenceMatcher(None, desc_clean, exp_desc_clean).ratio()

            # 2. Amount similarity (within 5% or 1.0 rupee)
            amt_diff = abs(amount - exp.amount)
            amt_match = (amt_diff <= 1.0) or (amount > 0 and (amt_diff / amount) <= 0.05)

            # 3. Date proximity (within 3 days)
            days_diff = 0
            if exp.expense_date:
                days_diff = abs((expense_date.date() - exp.expense_date.date()).days)

            date_match = days_diff <= 3

            # 4. Same payer check
            payer_match = (exp.paid_by == paid_by)

            # Calculate match score
            if (ratio >= 0.65 or desc_clean in exp_desc_clean or exp_desc_clean in desc_clean) and amt_match and date_match:
                score = (ratio * 0.5) + (0.3 if amt_match else 0) + (0.2 if payer_match else 0)
                possible_duplicates.append({
                    "expense": exp,
                    "similarity_score": round(score, 2),
                    "matched_description": exp.description,
                    "matched_amount": exp.amount,
                    "matched_date": exp.expense_date.strftime("%d %b %Y") if exp.expense_date else "",
                })

        possible_duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)

        if possible_duplicates:
            top_match = possible_duplicates[0]
            return {
                "is_duplicate": True,
                "confidence": top_match["similarity_score"],
                "matched_expense": top_match["expense"].to_dict(),
                "matched_description": top_match["matched_description"],
                "matched_amount": top_match["matched_amount"],
                "matched_date": top_match["matched_date"],
                "all_matches": possible_duplicates,
            }

        return {
            "is_duplicate": False,
            "confidence": 0.0,
            "matched_expense": None,
        }
