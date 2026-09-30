import re
from app.ml.predict_category import predict_category


class AIExpenseParser:
    @staticmethod
    def parse_natural_language_expense(text: str, group_member_names: list[str] = None) -> dict:
        text_clean = text.strip()
        if not text_clean:
            return {
                "amount": 0.0,
                "description": "",
                "category": "Other",
                "members": [],
                "confidence": 0.0,
            }

        # Regex for Amount extraction (e.g. ₹1200, 1200 rs, Rs 1200, $50, 1200)
        amount_match = re.search(r'(?:₹|rs\.?|inr|\$)?\s*(\d+(?:\.\d{1,2})?)\s*(?:rs|inr|rupees)?', text_clean, re.IGNORECASE)
        amount = float(amount_match.group(1)) if amount_match else 0.0

        # Description extraction (strip amount and participant keywords)
        desc = text_clean
        if amount_match:
            desc = text_clean.replace(amount_match.group(0), "").strip()

        # Clean common prefix words like "I paid", "paid for", "spent", "for"
        desc_clean = re.sub(r'^(i\s+paid|paid\s+for|spent|bought|for)\s+', '', desc, flags=re.IGNORECASE).strip()
        if not desc_clean:
            desc_clean = "Expense"

        # Participant names extraction
        detected_members = []
        if group_member_names:
            for name in group_member_names:
                if re.search(rf'\b{re.escape(name)}\b', text_clean, re.IGNORECASE):
                    detected_members.append(name)

        # Category prediction via ML module
        cat_result = predict_category(desc_clean)

        return {
            "amount": amount,
            "description": desc_clean.capitalize(),
            "category": cat_result["category"],
            "category_confidence": cat_result["confidence"],
            "members": detected_members,
            "raw_text": text_clean,
        }
