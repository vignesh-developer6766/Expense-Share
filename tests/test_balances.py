import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.services.expense_service import ExpenseService
from app.services.balance_service import BalanceService
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
def balance_setup(app):
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


def test_group_balances_calculation(app, balance_setup):
    u1_id, u2_id, u3_id, group_id = balance_setup
    with app.app_context():
        # User A pays 1200 for A, B, C (400 each)
        ExpenseService.create_expense(
            group_id=group_id,
            description="Hotel",
            amount=1200.0,
            category="Travel",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id, u3_id]},
        )

        balances = BalanceService.get_group_member_balances(group_id)
        # User A: paid 1200, owes 400 -> net +800
        # User B: paid 0, owes 400 -> net -400
        # User C: paid 0, owes 400 -> net -400
        assert balances[u1_id] == 800.0
        assert balances[u2_id] == -400.0
        assert balances[u3_id] == -400.0

        user_a_summary = BalanceService.get_user_group_balance(u1_id, group_id)
        assert user_a_summary["total_paid"] == 1200.0
        assert user_a_summary["total_owed"] == 400.0
        assert user_a_summary["net_balance"] == 800.0


def test_settlement_impact_on_balances(app, balance_setup):
    u1_id, u2_id, u3_id, group_id = balance_setup
    with app.app_context():
        ExpenseService.create_expense(
            group_id=group_id,
            description="Dinner",
            amount=600.0,
            category="Food",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id, u3_id]},
        )
        # Net before settlement: A: +400, B: -200, C: -200

        # User B settles ₹200 with User A
        SettlementService.record_settlement(group_id, payer_id=u2_id, receiver_id=u1_id, amount=200.0)

        balances = BalanceService.get_group_member_balances(group_id)
        # Net after settlement: A: +200, B: 0.0, C: -200
        assert balances[u1_id] == 200.0
        assert balances[u2_id] == 0.0
        assert balances[u3_id] == -200.0
