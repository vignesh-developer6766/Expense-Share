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


def test_register_page_loads(client):
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"Create Account" in response.data


def test_successful_registration(client, app):
    response = client.post(
        "/auth/register",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Registration successful" in response.data

    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        assert user.name == "Test User"
        assert user.check_password("Password123") is True


def test_duplicate_email_registration(client):
    # First registration
    client.post(
        "/auth/register",
        data={
            "name": "First User",
            "email": "duplicate@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )

    # Second registration with same email
    response = client.post(
        "/auth/register",
        data={
            "name": "Second User",
            "email": "duplicate@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"already registered" in response.data


def test_password_mismatch_registration(client):
    response = client.post(
        "/auth/register",
        data={
            "name": "Test User",
            "email": "mismatch@example.com",
            "password": "Password123",
            "confirm_password": "DifferentPassword",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Passwords do not match" in response.data


def test_login_and_logout(client):
    # Register user
    client.post(
        "/auth/register",
        data={
            "name": "Auth User",
            "email": "auth@example.com",
            "password": "SecretPassword123",
            "confirm_password": "SecretPassword123",
        },
    )

    # Invalid login
    response = client.post(
        "/auth/login",
        data={"email": "auth@example.com", "password": "WrongPassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data

    # Valid login
    response = client.post(
        "/auth/login",
        data={"email": "auth@example.com", "password": "SecretPassword123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome back, Auth User" in response.data

    # Logout
    response = client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out safely" in response.data
