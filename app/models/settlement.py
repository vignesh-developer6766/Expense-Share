from datetime import datetime, timezone
from app.extensions import db


class Settlement(db.Model):
    __tablename__ = "settlements"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="completed")  # pending, completed
    settled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Foreign key relationships
    payer = db.relationship("User", foreign_keys=[payer_id], backref="settlements_paid")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="settlements_received")

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "payer_id": self.payer_id,
            "payer_name": self.payer.name if self.payer else None,
            "receiver_id": self.receiver_id,
            "receiver_name": self.receiver.name if self.receiver else None,
            "amount": self.amount,
            "status": self.status,
            "settled_at": self.settled_at.isoformat() if self.settled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Settlement {self.payer_id} -> {self.receiver_id} : ₹{self.amount}>"
