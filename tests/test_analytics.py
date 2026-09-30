import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.services.expense_service import ExpenseService
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def analytics_setup(app):
    with app.app_context():
        u1 = User(name="User A", email="a@example.com")
        u1.set_password("pass")
        u2 = User(name="User B", email="b@example.com")
        u2.set_password("pass")
        db.session.add_all([u1, u2])
        db.session.commit()

        group = Group(name="Trip", created_by=u1.id)
        db.session.add(group)
        db.session.commit()

        db.session.add_all([
            GroupMember(group_id=group.id, user_id=u1.id),
            GroupMember(group_id=group.id, user_id=u2.id),
        ])
        db.session.commit()
        return u1.id, u2.id, group.id


def test_category_spending(app, analytics_setup):
    u1_id, u2_id, group_id = analytics_setup
    with app.app_context():
        ExpenseService.create_expense(
            group_id=group_id,
            description="Dinner",
            amount=500.0,
            category="Food",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id]},
        )
        ExpenseService.create_expense(
            group_id=group_id,
            description="Lunch",
            amount=300.0,
            category="Food",
            paid_by=u2_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id]},
        )
        ExpenseService.create_expense(
            group_id=group_id,
            description="Uber",
            amount=400.0,
            category="Transport",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id]},
        )

        cat_spending = AnalyticsService.get_category_spending(u1_id)
        assert cat_spending["Food"] == 800.0
        assert cat_spending["Transport"] == 400.0


def test_spending_insights(app, analytics_setup):
    u1_id, u2_id, group_id = analytics_setup
    with app.app_context():
        ExpenseService.create_expense(
            group_id=group_id,
            description="Resort",
            amount=5000.0,
            category="Travel",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id]},
        )

        insights = AnalyticsService.generate_spending_insights(u1_id)
        assert len(insights) >= 1
        assert "Travel" in insights[0]
        assert "highest spending category" in insights[0]
