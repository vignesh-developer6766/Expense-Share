import pytest
from datetime import datetime, timezone
from app import create_app
from app.extensions import db
from app.models import (
    User,
    Group,
    GroupMember,
    Expense,
    ExpenseSplit,
    Settlement,
    RecurringExpense,
    Notification,
)


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


def test_user_creation_and_password_hashing(app):
    with app.app_context():
        user = User(name="Vignesh", email="vignesh@example.com")
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.commit()

        fetched = User.query.filter_by(email="vignesh@example.com").first()
        assert fetched is not None
        assert fetched.name == "Vignesh"
        assert fetched.check_password("SecurePass123!") is True
        assert fetched.check_password("WrongPassword") is False
        assert fetched.to_dict()["email"] == "vignesh@example.com"


def test_group_and_membership(app):
    with app.app_context():
        creator = User(name="Alice", email="alice@example.com", password_hash="hash")
        member_user = User(name="Bob", email="bob@example.com", password_hash="hash")
        db.session.add_all([creator, member_user])
        db.session.commit()

        group = Group(name="Trip Group", description="Goa Trip", created_by=creator.id)
        db.session.add(group)
        db.session.commit()

        membership1 = GroupMember(group_id=group.id, user_id=creator.id)
        membership2 = GroupMember(group_id=group.id, user_id=member_user.id)
        db.session.add_all([membership1, membership2])
        db.session.commit()

        assert len(group.members) == 2
        assert group.creator.name == "Alice"
        group_dict = group.to_dict(include_members=True)
        assert group_dict["member_count"] == 2
        assert len(group_dict["members"]) == 2


def test_expense_and_splits(app):
    with app.app_context():
        u1 = User(name="User 1", email="u1@example.com", password_hash="hash")
        u2 = User(name="User 2", email="u2@example.com", password_hash="hash")
        db.session.add_all([u1, u2])
        db.session.commit()

        group = Group(name="Dinner Group", created_by=u1.id)
        db.session.add(group)
        db.session.commit()

        expense = Expense(
            group_id=group.id,
            description="Team Dinner",
            amount=1000.0,
            category="Food",
            paid_by=u1.id,
        )
        db.session.add(expense)
        db.session.commit()

        split1 = ExpenseSplit(expense_id=expense.id, user_id=u1.id, split_type="equal", amount=500.0)
        split2 = ExpenseSplit(expense_id=expense.id, user_id=u2.id, split_type="equal", amount=500.0)
        db.session.add_all([split1, split2])
        db.session.commit()

        assert len(expense.splits) == 2
        assert expense.paid_by == u1.id
        assert expense.to_dict()["amount"] == 1000.0


def test_settlement_model(app):
    with app.app_context():
        u1 = User(name="Payer", email="payer@example.com", password_hash="hash")
        u2 = User(name="Receiver", email="receiver@example.com", password_hash="hash")
        db.session.add_all([u1, u2])
        db.session.commit()

        group = Group(name="Settlement Group", created_by=u1.id)
        db.session.add(group)
        db.session.commit()

        settlement = Settlement(
            group_id=group.id,
            payer_id=u1.id,
            receiver_id=u2.id,
            amount=250.0,
            status="completed",
        )
        db.session.add(settlement)
        db.session.commit()

        assert settlement.payer.name == "Payer"
        assert settlement.receiver.name == "Receiver"
        assert settlement.amount == 250.0


def test_recurring_expense_and_notifications(app):
    with app.app_context():
        user = User(name="Charlie", email="charlie@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        group = Group(name="Roommates", created_by=user.id)
        db.session.add(group)
        db.session.commit()

        rec = RecurringExpense(
            group_id=group.id,
            description="Wifi Bill",
            amount=799.0,
            frequency="monthly",
            next_due_date=datetime.now(timezone.utc),
            category="Utilities",
            created_by=user.id,
        )
        notif = Notification(
            user_id=user.id,
            title="Wifi Bill Due",
            message="Your Wifi Bill is due soon",
            type="reminder",
        )
        db.session.add_all([rec, notif])
        db.session.commit()

        assert rec.active is True
        assert notif.is_read is False
        assert notif.to_dict()["title"] == "Wifi Bill Due"
