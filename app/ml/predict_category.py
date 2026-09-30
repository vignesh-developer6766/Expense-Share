import os
from pathlib import Path
import joblib
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "expense_category_model.pkl"
VECTORIZER_PATH = BASE_DIR / "models" / "tfidf_vectorizer.pkl"


class CategoryPredictor:
    _model = None
    _vectorizer = None

    @classmethod
    def _load_model(cls):
        if cls._model is None or cls._vectorizer is None:
            if MODEL_PATH.exists() and VECTORIZER_PATH.exists():
                try:
                    cls._model = joblib.load(MODEL_PATH)
                    cls._vectorizer = joblib.load(VECTORIZER_PATH)
                except Exception:
                    cls._model = None
                    cls._vectorizer = None

    @classmethod
    def predict(cls, description: str) -> dict:
        description_clean = description.strip().lower()
        if not description_clean:
            return {"category": "Other", "confidence": 1.0}

        cls._load_model()

        if cls._model and cls._vectorizer:
            try:
                X_vec = cls._vectorizer.transform([description_clean])
                probabilities = cls._model.predict_proba(X_vec)[0]
                best_idx = np.argmax(probabilities)
                predicted_category = cls._model.classes_[best_idx]
                confidence = float(probabilities[best_idx])
                if confidence >= 0.60:
                    return {"category": predicted_category, "confidence": round(confidence, 2)}
            except Exception:
                pass

        # Heuristic fallback if model is unavailable or confidence < 0.60
        return cls._fallback_predict(description_clean)

    @classmethod
    def _fallback_predict(cls, text: str) -> dict:
        text = text.lower()
        keywords = {
            "Groceries": [
                "dmart", "d-mart", "reliance smart", "bigbasket", "blinkit", "zepto", "instamart", 
                "supermarket", "grocery", "groceries", "mart", "provision", "hypermarket", "spencer", 
                "market", "foodhall", "vegetable", "fruits", "dairy", "milk"
            ],
            "Food": [
                "swiggy", "zomato", "pizza", "dinner", "lunch", "breakfast", "coffee", "restaurant", "burger", 
                "starbucks", "food", "kfc", "dominos", "subway", "dunkin", "mcdonald", "cafe", "bistro", 
                "bakery", "kitchen", "biryani", "sweets", "haldiram", "barbeque", "grill", "pub", "bar", 
                "tea", "canteen", "mess", "chai", "eatery", "tiffin"
            ],
            "Transport": [
                "uber", "ola", "rapido", "cab", "bus", "flight", "auto", "petrol", "fuel", "diesel", 
                "train", "metro", "ticket", "fare", "shell", "hpcl", "bpcl", "iocl", "toll", "parking", 
                "ride", "travels", "transport"
            ],
            "Shopping": [
                "amazon", "flipkart", "myntra", "ajio", "nykaa", "zara", "h&m", "uniqlo", "tata cliq", 
                "electronics", "croma", "reliance digital", "vijay sales", "shoes", "clothes", "apparel", 
                "mall", "store", "retail", "fashion", "footwear", "lenskart", "headphones", "gadget", "shopping"
            ],
            "Entertainment": [
                "netflix", "spotify", "bookmyshow", "pvr", "inox", "cinepolis", "movie", "cinema", 
                "theater", "play", "concert", "youtube", "prime", "disney", "apple", "gaming", "steam", 
                "playstation", "show", "games"
            ],
            "Utilities": [
                "electricity", "power", "bescom", "msedcl", "tneb", "wbsedcl", "tata power", "water", 
                "gas", "lpg", "indane", "bharatgas", "hp gas", "wifi", "internet", "broadband", "airtel", 
                "jio", "vi", "vodafone", "bsnl", "recharge", "mobile", "postpaid", "bill"
            ],
            "Travel": [
                "makemytrip", "goibibo", "easemytrip", "yatra", "agoda", "booking.com", "airbnb", 
                "hotel", "resort", "stay", "vacation", "trip", "tour", "sightseeing"
            ],
            "Rent": ["rent", "maintenance", "flat", "room", "pg", "society", "hostel", "house"],
        }
        for cat, kw_list in keywords.items():
            if any(kw in text for kw in kw_list):
                return {"category": cat, "confidence": 0.88}
        return {"category": "Other", "confidence": 0.50}


def predict_category(description: str) -> dict:
    return CategoryPredictor.predict(description)
