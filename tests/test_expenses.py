import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.expense import Expense
from app.services.expense_service import ExpenseService


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
def group_setup(app):
    with app.app_context():
        u1 = User(name="Vignesh", email="vignesh@example.com")
        u1.set_password("Pass123")
        u2 = User(name="Arun", email="arun@example.com")
        u2.set_password("Pass123")
        u3 = User(name="Rahul", email="rahul@example.com")
        u3.set_password("Pass123")
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        group = Group(name="College Trip", created_by=u1.id)
        db.session.add(group)
        db.session.commit()

        db.session.add_all([
            GroupMember(group_id=group.id, user_id=u1.id),
            GroupMember(group_id=group.id, user_id=u2.id),
            GroupMember(group_id=group.id, user_id=u3.id),
        ])
        db.session.commit()
        return u1.id, u2.id, u3.id, group.id


def test_create_expense_equal_split(app, group_setup):
    u1_id, u2_id, u3_id, group_id = group_setup
    with app.app_context():
        expense = ExpenseService.create_expense(
            group_id=group_id,
            description="Swiggy Dinner",
            amount=1200.0,
            category="Food",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id, u3_id]},
        )
        assert expense.id is not None
        assert expense.amount == 1200.0
        assert len(expense.splits) == 3
        for split in expense.splits:
            assert split.amount == 400.0


def test_create_expense_invalid_amount(app, group_setup):
    u1_id, u2_id, u3_id, group_id = group_setup
    with app.app_context():
        with pytest.raises(ValueError, match="greater than zero"):
            ExpenseService.create_expense(
                group_id=group_id,
                description="Invalid Expense",
                amount=-50.0,
                category="Food",
                paid_by=u1_id,
                split_type="equal",
                split_data={"users": [u1_id, u2_id]},
            )


def test_expense_filtering_and_deletion(app, group_setup):
    u1_id, u2_id, u3_id, group_id = group_setup
    with app.app_context():
        e1 = ExpenseService.create_expense(
            group_id=group_id,
            description="Uber Ride",
            amount=300.0,
            category="Transport",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id]},
        )
        e2 = ExpenseService.create_expense(
            group_id=group_id,
            description="Pizza Party",
            amount=900.0,
            category="Food",
            paid_by=u2_id,
            split_type="equal",
            split_data={"users": [u1_id, u2_id, u3_id]},
        )

        # Filter by category
        food_expenses = ExpenseService.get_user_expenses(user_id=u1_id, category="Food")
        assert len(food_expenses) == 1
        assert food_expenses[0].description == "Pizza Party"

        # Search description
        search_expenses = ExpenseService.get_user_expenses(user_id=u1_id, search="Uber")
        assert len(search_expenses) == 1
        assert search_expenses[0].description == "Uber Ride"

        # Delete expense
        success, msg = ExpenseService.delete_expense(e1.id, current_user_id=u1_id)
        assert success is True
        assert db.session.get(Expense, e1.id) is None
