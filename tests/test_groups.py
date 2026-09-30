import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember


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


@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User(name="Owner", email="owner@example.com")
        user.set_password("Password123")
        db.session.add(user)
        db.session.commit()

    client.post("/auth/login", data={"email": "owner@example.com", "password": "Password123"})
    return client


def test_groups_require_auth(client):
    response = client.get("/groups", follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign In" in response.data


def test_create_group(auth_client, app):
    response = auth_client.post(
        "/groups/new",
        data={"name": "College Trip", "description": "Goa vacation"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"College Trip" in response.data

    with app.app_context():
        group = Group.query.filter_by(name="College Trip").first()
        assert group is not None
        assert group.description == "Goa vacation"
        assert len(group.members) == 1
        assert group.members[0].user.email == "owner@example.com"


def test_add_and_remove_member(auth_client, app):
    # Create another user in DB
    with app.app_context():
        member_user = User(name="Friend", email="friend@example.com")
        member_user.set_password("Password123")
        db.session.add(member_user)
        db.session.commit()

    # Create group
    auth_client.post("/groups/new", data={"name": "Roommates", "description": "Flat 302"})
    with app.app_context():
        group = Group.query.filter_by(name="Roommates").first()
        group_id = group.id

    # Add member by email
    response = auth_client.post(
        f"/groups/{group_id}/members/add",
        data={"email": "friend@example.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Added Friend to the group" in response.data

    with app.app_context():
        group = db.session.get(Group, group_id)
        assert len(group.members) == 2

    # Remove member
    with app.app_context():
        friend = User.query.filter_by(email="friend@example.com").first()
        friend_id = friend.id

    response = auth_client.post(
        f"/groups/{group_id}/members/{friend_id}/remove",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Member removed successfully" in response.data


def test_unauthorized_group_access(client, app):
    with app.app_context():
        owner = User(name="Owner", email="owner2@example.com")
        owner.set_password("Pass123")
        stranger = User(name="Stranger", email="stranger@example.com")
        stranger.set_password("Pass123")
        db.session.add_all([owner, stranger])
        db.session.commit()

        group = Group(name="Private Group", created_by=owner.id)
        db.session.add(group)
        db.session.commit()
        db.session.add(GroupMember(group_id=group.id, user_id=owner.id))
        db.session.commit()
        group_id = group.id

    # Stranger logs in
    client.post("/auth/login", data={"email": "stranger@example.com", "password": "Pass123"})
    response = client.get(f"/groups/{group_id}", follow_redirects=True)
    assert response.status_code == 200
    assert b"You are not a member of this group" in response.data
