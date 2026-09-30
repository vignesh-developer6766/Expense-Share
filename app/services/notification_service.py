from datetime import datetime, timezone
from app.extensions import db
from app.models.notification import Notification


class NotificationService:
    @staticmethod
    def create_notification(user_id: int, title: str, message: str, type: str = "info") -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title.strip(),
            message=message.strip(),
            type=type.lower(),
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(notif)
        db.session.commit()
        return notif

    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False) -> list[Notification]:
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_notification_as_read(notification_id: int, user_id: int) -> bool:
        notif = db.session.get(Notification, notification_id)
        if notif and notif.user_id == user_id:
            notif.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_read(user_id: int) -> int:
        unread = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        for notif in unread:
            notif.is_read = True
        db.session.commit()
        return len(unread)

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
