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


def test_users_list_route(client, app):
    # Register admin and another user
    client.post(
        "/auth/register",
        data={
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    client.post(
        "/auth/register",
        data={
            "name": "Member User",
            "email": "member@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )

    # Login as Admin User
    client.post(
        "/auth/login",
        data={"email": "admin@example.com", "password": "Password123"},
    )

    # Access Users List
    response = client.get("/users/list")
    assert response.status_code == 200
    assert b"User Management" in response.data
    assert b"Member User" in response.data


def test_edit_user_route(client, app):
    # Register Admin and Target User
    client.post(
        "/auth/register",
        data={
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    client.post(
        "/auth/register",
        data={
            "name": "Original Name",
            "email": "original@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )

    client.post(
        "/auth/login",
        data={"email": "admin@example.com", "password": "Password123"},
    )

    with app.app_context():
        target = User.query.filter_by(email="original@example.com").first()
        target_id = target.id

    # Post edit user
    response = client.post(
        f"/users/{target_id}/edit",
        data={
            "name": "Updated Name",
            "email": "updated@example.com",
            "password": "NewPassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"updated successfully" in response.data

    with app.app_context():
        updated_user = db.session.get(User, target_id)
        assert updated_user.name == "Updated Name"
        assert updated_user.email == "updated@example.com"
        assert updated_user.check_password("NewPassword123") is True


def test_delete_user_route(client, app):
    client.post(
        "/auth/register",
        data={
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    client.post(
        "/auth/register",
        data={
            "name": "Delete Me",
            "email": "deleteme@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )

    client.post(
        "/auth/login",
        data={"email": "admin@example.com", "password": "Password123"},
    )

    with app.app_context():
        target = User.query.filter_by(email="deleteme@example.com").first()
        target_id = target.id

    # Post delete user
    response = client.post(
        f"/users/{target_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"deleted successfully" in response.data

    with app.app_context():
        deleted_user = db.session.get(User, target_id)
        assert deleted_user is None
