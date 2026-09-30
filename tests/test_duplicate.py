import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.services.expense_service import ExpenseService
from app.ml.duplicate_detector import DuplicateDetector


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def group_setup(app):
    with app.app_context():
        u1 = User(name="Vignesh", email="v@example.com")
        u1.set_password("pass")
        db.session.add(u1)
        db.session.commit()

        group = Group(name="Dinner Club", created_by=u1.id)
        db.session.add(group)
        db.session.commit()

        db.session.add(GroupMember(group_id=group.id, user_id=u1.id))
        db.session.commit()
        return u1.id, group.id


def test_duplicate_expense_detected(app, group_setup):
    u1_id, group_id = group_setup
    with app.app_context():
        # Create initial expense
        ExpenseService.create_expense(
            group_id=group_id,
            description="Swiggy Dinner",
            amount=1200.0,
            category="Food",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id]},
        )

        # Check candidate duplicate
        result = DuplicateDetector.check_duplicate(
            group_id=group_id,
            description="Swiggy Dinner",
            amount=1200.0,
            paid_by=u1_id,
        )

        assert result["is_duplicate"] is True
        assert result["confidence"] >= 0.7
        assert result["matched_description"] == "Swiggy Dinner"


def test_unique_expense_not_flagged(app, group_setup):
    u1_id, group_id = group_setup
    with app.app_context():
        ExpenseService.create_expense(
            group_id=group_id,
            description="Swiggy Dinner",
            amount=1200.0,
            category="Food",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id]},
        )

        result = DuplicateDetector.check_duplicate(
            group_id=group_id,
            description="Uber Ride to Airport",
            amount=450.0,
            paid_by=u1_id,
        )

        assert result["is_duplicate"] is False
