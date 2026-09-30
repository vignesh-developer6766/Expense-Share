import pytest
from app.ml.predict_category import predict_category
from app.ai.expense_parser import AIExpenseParser


def test_predict_category_food():
    res = predict_category("swiggy pizza dinner with friends")
    assert res["category"] == "Food"
    assert res["confidence"] > 0.3


def test_predict_category_transport():
    res = predict_category("uber cab ride to office")
    assert res["category"] == "Transport"
    assert res["confidence"] > 0.3


def test_predict_category_shopping():
    res = predict_category("amazon headphones purchase")
    assert res["category"] == "Shopping"
    assert res["confidence"] > 0.2


def test_ai_expense_parser():
    text = "I paid ₹1200 for dinner with Arun and Rahul"
    parsed = AIExpenseParser.parse_natural_language_expense(
        text, group_member_names=["Arun", "Rahul", "Karthik"]
    )

    assert parsed["amount"] == 1200.0
    assert parsed["category"] == "Food"
    assert "Arun" in parsed["members"]
    assert "Rahul" in parsed["members"]
    assert "Karthik" not in parsed["members"]
