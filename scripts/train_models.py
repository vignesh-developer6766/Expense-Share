import os
from pathlib import Path
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "sample_expenses.csv"
MODEL_DIR = BASE_DIR / "models"


def train_category_model():
    print("Loading training dataset...")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df["clean_description"] = df["description"].astype(str).str.lower().str.strip()

    X = df["clean_description"]
    y = df["category"]

    print(f"Training on {len(df)} sample expenses across {y.nunique()} categories...")

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    X_tfidf = vectorizer.fit_transform(X)

    model = LogisticRegression(C=1.0, max_iter=1000)
    model.fit(X_tfidf, y)

    # Save artifacts
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "expense_category_model.pkl"
    vectorizer_path = MODEL_DIR / "tfidf_vectorizer.pkl"

    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)

    print(f"Model saved to {model_path}")
    print(f"Vectorizer saved to {vectorizer_path}")
    print("Training complete successfully!")


if __name__ == "__main__":
    train_category_model()
