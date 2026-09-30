import pytest
from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_api_register_and_login(client):
    # API Register
    res = client.post(
        "/api/auth/register",
        json={"name": "API User", "email": "api@example.com", "password": "SecretPassword123"},
    )
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["user"]["email"] == "api@example.com"

    # API Login
    res = client.post(
        "/api/auth/login",
        json={"email": "api@example.com", "password": "SecretPassword123"},
    )
    assert res.status_code == 200
    assert "Logged in successfully" in res.get_json()["message"]


def test_api_predict_category(client):
    res = client.post(
        "/api/ml/predict-category",
        json={"description": "swiggy dinner pizza"},
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["category"] == "Food"


def test_api_parse_expense(client):
    res = client.post(
        "/api/ai/parse-expense",
        json={"text": "I paid ₹1500 for grocery shopping at supermarket", "members": []},
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["amount"] == 1500.0
    assert json_data["category"] in ["Food", "Shopping", "Groceries"]
