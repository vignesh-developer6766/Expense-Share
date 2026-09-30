import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.services.expense_service import ExpenseService
from app.ml.forecasting import ExpenseForecaster
from app.ml.anomaly_detector import AnomalyDetector


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def setup_data(app):
    with app.app_context():
        u1 = User(name="User A", email="a@example.com")
        u1.set_password("pass")
        db.session.add(u1)
        db.session.commit()

        group = Group(name="Trip", created_by=u1.id)
        db.session.add(group)
        db.session.commit()
        db.session.add(GroupMember(group_id=group.id, user_id=u1.id))
        db.session.commit()
        return u1.id, group.id


def test_expense_forecaster(app, setup_data):
    u1_id, group_id = setup_data
    with app.app_context():
        ExpenseService.create_expense(
            group_id=group_id,
            description="Dinner 1",
            amount=1000.0,
            category="Food",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id]},
        )
        ExpenseService.create_expense(
            group_id=group_id,
            description="Dinner 2",
            amount=1200.0,
            category="Food",
            paid_by=u1_id,
            split_type="equal",
            split_data={"users": [u1_id]},
        )

        forecast = ExpenseForecaster.forecast_next_month_spending(u1_id)
        assert forecast["estimated_next_month"] > 0
        assert "Historical" in forecast["label"] or "historical" in forecast["label"]


def test_anomaly_detector_normal_and_outlier(app, setup_data):
    u1_id, group_id = setup_data
    with app.app_context():
        # Add typical small expenses: 200, 450, 700, 850
        for amt in [200.0, 450.0, 700.0, 850.0]:
            ExpenseService.create_expense(
                group_id=group_id,
                description="Regular expense",
                amount=amt,
                category="Food",
                paid_by=u1_id,
                split_type="equal",
                split_data={"users": [u1_id]},
            )

        # Check normal amount
        normal_res = AnomalyDetector.detect_anomaly(group_id, amount=500.0, category="Food")
        assert normal_res["is_anomaly"] is False

        # Check outlier amount (18,500)
        outlier_res = AnomalyDetector.detect_anomaly(group_id, amount=18500.0, category="Food")
        assert outlier_res["is_anomaly"] is True
        assert "Unusual expense detected" in outlier_res["message"]
