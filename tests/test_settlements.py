import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.notification import Notification
from app.services.expense_service import ExpenseService
from app.services.settlement_service import SettlementService


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def settlement_setup(app):
    with app.app_context():
        u1 = User(name="User A", email="a@example.com")
        u1.set_password("pass")
        u2 = User(name="User B", email="b@example.com")
        u2.set_password("pass")
        u3 = User(name="User C", email="c@example.com")
        u3.set_password("pass")
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        group = Group(name="Trip", created_by=u1.id)
        db.session.add(group)
        db.session.commit()

        db.session.add_all([
            GroupMember(group_id=group.id, user_id=u1.id),
            GroupMember(group_id=group.id, user_id=u2.id),
            GroupMember(group_id=group.id, user_id=u3.id),
        ])
        db.session.commit()
        return u1.id, u2.id, u3.id, group.id


def test_circular_debt_simplification(app, settlement_setup):
    u1_id, u2_id, u3_id, group_id = settlement_setup
    with app.app_context():
        # User B paid 1000 for User A & B (A owes B 500)
        ExpenseService.create_expense(
            group_id=group_id,
            description="B paid A",
            amount=1000.0,
            category="Food",
            paid_by=u2_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id]},
        )
        # User C paid 1000 for User B & C (B owes C 500)
        ExpenseService.create_expense(
            group_id=group_id,
            description="C paid B",
            amount=1000.0,
            category="Food",
            paid_by=u3_id,
            split_type="equal",
            split_data={"users": [u2_id, u3_id]},
        )
        # User A paid 600 for User C & A (C owes A 300)
        ExpenseService.create_expense(
            group_id=group_id,
            description="A paid C",
            amount=600.0,
            category="Food",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id, u3_id]},
        )

        # Net balances before simplification:
        # A: -500 + 300 = -200 (owes 200)
        # B: +500 - 500 = 0 (settled)
        # C: +500 - 300 = +200 (owed 200)
        simplified = SettlementService.simplify_group_debts(group_id)

        # Should result in exactly 1 transaction: A pays C 200
        assert len(simplified) == 1
        tx = simplified[0]
        assert tx["payer_id"] == u1_id
        assert tx["receiver_id"] == u3_id
        assert tx["amount"] == 200.0


def test_record_settlement_creates_notification(app, settlement_setup):
    u1_id, u2_id, u3_id, group_id = settlement_setup
    with app.app_context():
        settlement = SettlementService.record_settlement(
            group_id=group_id,
            payer_id=u1_id,
            receiver_id=u2_id,
            amount=150.0,
        )
        assert settlement.id is not None
        assert settlement.amount == 150.0

        # Receiver should have a notification
        notif = Notification.query.filter_by(user_id=u2_id).first()
        assert notif is not None
        assert "Payment Received" in notif.title
        assert "User A settled ₹150.00" in notif.message
