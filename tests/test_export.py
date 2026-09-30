import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.services.expense_service import ExpenseService
from app.services.export_service import ExportService


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_csv_export(app):
    with app.app_context():
        u = User(name="User A", email="a@example.com")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()

        group = Group(name="Trip", created_by=u.id)
        db.session.add(group)
        db.session.commit()

        db.session.add(GroupMember(group_id=group.id, user_id=u.id))
        db.session.commit()

        ExpenseService.create_expense(
            group_id=group.id,
            description="Taxi Ride",
            amount=250.0,
            category="Transport",
            paid_by=u.id,
            split_type="equal",
            split_data={"users": [u.id]},
        )

        csv_content = ExportService.export_expenses_to_csv(user_id=u.id)
        assert "Date,Description,Category" in csv_content or "Date" in csv_content
        assert "Taxi Ride" in csv_content
        assert "250.00" in csv_content
