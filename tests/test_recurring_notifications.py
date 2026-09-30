from datetime import datetime, timezone, timedelta
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.group import Group, GroupMember
from app.services.recurring_service import RecurringService
from app.services.notification_service import NotificationService


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
        u = User(name="User A", email="a@example.com")
        u.set_password("pass")
        db.session.add(u)
        db.session.commit()

        group = Group(name="Flat 302", created_by=u.id)
        db.session.add(group)
        db.session.commit()

        db.session.add(GroupMember(group_id=group.id, user_id=u.id))
        db.session.commit()
        return u.id, group.id


def test_recurring_expense_creation_and_due_processing(app, setup_data):
    u_id, group_id = setup_data
    with app.app_context():
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        rec = RecurringService.create_recurring_expense(
            group_id=group_id,
            description="Internet Bill",
            amount=799.0,
            frequency="monthly",
            next_due_date=past_date,
            category="Utilities",
            creator_id=u_id,
        )
        assert rec.active is True

        processed_count = RecurringService.process_due_recurring_expenses()
        assert processed_count == 1

        # Unread notifications check
        notifs = NotificationService.get_user_notifications(u_id, unread_only=True)
        assert len(notifs) >= 1
        assert "Internet Bill" in notifs[0].title


def test_notification_mark_read(app, setup_data):
    u_id, group_id = setup_data
    with app.app_context():
        notif = NotificationService.create_notification(
            user_id=u_id,
            title="Test Notification",
            message="Test Message",
            type="info",
        )
        assert NotificationService.get_unread_count(u_id) == 1

        NotificationService.mark_notification_as_read(notif.id, u_id)
        assert NotificationService.get_unread_count(u_id) == 0
